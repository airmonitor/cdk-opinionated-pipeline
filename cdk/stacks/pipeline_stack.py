"""Deploy AWS CI/CD stack with all stages."""
from os import path, walk

import aws_cdk as cdk
import aws_cdk.aws_chatbot as chatbot
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codecommit as codecommit
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as events_targets
import aws_cdk.aws_iam as iam
import aws_cdk.aws_sns as sns
import aws_cdk.aws_sns_subscriptions as sns_subscriptions
import yaml
from aws_cdk import pipelines
from aws_cdk.aws_codestarnotifications import DetailType, NotificationRule
from constructs import Construct

from cdk.schemas.configuration_vars import PipelineVars, NotificationVars
from cdk.stages.code_quality_stage import CodeQualityStage
from cdk.stages.infrastructure_tests_stage import InfrastructureTestsStage
from cdk.stages.plugins_stage import PluginsStage
from cdk.stages.shared_resources_stage import SharedResourcesStage
from cdk.utils.utils import check_ansible_dir, apply_tags


class PipelineStack(cdk.Stack):
    """CI/CD Pipeline stack."""

    def __init__(self, scope: Construct, construct_id: str, env: cdk.Environment, props: dict, **kwargs) -> None:
        """Initialize default parameters from AWS CDK and configuration file.

        :param scope: The AWS CDK parent class from which this class
            inherits
        :param construct_id: The name of CDK construct
        :param env: Tha AWS CDK Environment class which provides AWS
            Account ID and AWS Region
        :param props: The dictionary which contain configuration values
            loaded initially from /config/config-env.yaml
        :param kwargs:
        """
        super().__init__(scope, construct_id, env=env, **kwargs)
        pipeline_vars = PipelineVars(**props)
        notification_vars = NotificationVars(**props)
        imported_repository = codecommit.Repository.from_repository_name(
            self, id="imported_repository", repository_name=pipeline_vars.repository
        )

        notifications_sns_topic = self.notifications_topic(pipeline_vars=pipeline_vars)

        self.codepipeline = pipelines.CodePipeline(
            self,
            "pipeline",
            code_build_defaults=pipelines.CodeBuildOptions(
                role_policy=[
                    iam.PolicyStatement(actions=["*"], resources=["*"]),
                    iam.PolicyStatement(actions=["sts:AssumeRole"], resources=["*"]),
                ],
                build_environment=codebuild.BuildEnvironment(
                    compute_type=codebuild.ComputeType.SMALL,
                    build_image=codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
                ),
            ),
            synth=pipelines.ShellStep(
                "synth",
                input=pipelines.CodePipelineSource.code_commit(repository=imported_repository, branch="main"),
                commands=[
                    "pip install -r requirements.txt",
                    "npm install -g aws-cdk",
                    "cdk synth",
                ],
            ),
            pipeline_name=pipeline_vars.project,
            self_mutation=True,
        )

        self.code_quality_stage(
            env=env, pipeline=self.codepipeline, props=props, pipeline_vars=pipeline_vars, stage="dev"
        )

        # DEV resources
        stage = "dev"
        env = cdk.Environment(
            account=pipeline_vars.aws_account,
            region=pipeline_vars.aws_region,
        )
        self.infrastructure_test_stage(
            env=env, pipeline=self.codepipeline, props=props, pipeline_vars=pipeline_vars, stage=stage
        )
        self.environment_type(
            props=props,
            env=env,
            stage=stage,
        )

        self.codepipeline.build_pipeline()

        self.create_pipeline_notifications(
            notifications_sns_topic=notifications_sns_topic,
            pipeline_vars=pipeline_vars,
            notification_vars=notification_vars,
        )

        self.pipeline_trigger(
            pipeline_vars=pipeline_vars,
            props=props,
            schedule=events.Schedule.cron(minute="0", hour="05", month="*", day="7,14,21,28", year="*"),
        )

    def create_pipeline_notifications(
        self, notifications_sns_topic: sns.Topic, notification_vars: NotificationVars, pipeline_vars: PipelineVars
    ):
        """Create pipeline notifications through email and Slack channel.

        :param notification_vars:
        :param notifications_sns_topic: CDK object for an SNS topic to
            which notifications will be sent
        :param pipeline_vars: Pydantic model that contains configuration
            values loaded initially from config files
        :return:
        """
        # Enable SNS notifications if the recipient email address was provided
        if pipeline_vars.ci_cd_notification_email:
            self.pipeline_email_notifications(sns_topic=notifications_sns_topic)
        self.pipeline_notifications(sns_topic=notifications_sns_topic)
        # Enable Slack notifications if recipient workspace and channel slack were provided.
        if notification_vars.slack_workspace_id and notification_vars.slack_channel_id:
            chatbot.SlackChannelConfiguration(
                self,
                "chatbot",
                slack_channel_configuration_name=pipeline_vars.project,
                notification_topics=[notifications_sns_topic],
                slack_workspace_id=notification_vars.slack_workspace_id,
                slack_channel_id=notification_vars.slack_channel_id,
            )

    def pipeline_trigger(self, pipeline_vars: PipelineVars, props: dict, schedule: events.Schedule):
        """

        :param schedule: The events schedule object
        :param pipeline_vars: Pydantic model that contains configuration values loaded initially from config files
        :param props: The dictionary which contains configuration values loaded initially from /config/config-env.yaml
        """
        # Auto triggers the pipeline every day to ensure pipeline validation
        trigger = events.Rule(
            self,
            id="daily_release",
            description="Auto trigger the pipeline every day to ensure pipeline validation",
            enabled=True,
            rule_name=f"{pipeline_vars.project}-scheduled-release",
            schedule=schedule,
        )
        trigger.add_target(events_targets.CodePipeline(self.codepipeline.pipeline))
        apply_tags(props=props, resource=trigger)

    def code_quality_stage(
        self,
        env: cdk.Environment,
        pipeline: pipelines.CodePipeline,
        props: dict,
        stage: str,
        pipeline_vars: PipelineVars,
    ) -> None:
        """Create CI/CD stage which contains several jobs for checking code
        quality using various linters. Stage will be added to an existing
        pipeline.

        :param pipeline_vars: Pydantic model that contains configuration values loaded initially from config files
        :param env: The AWS CDK Environment class which provide AWS Account ID and AWS Region
        :param pipeline: The AWS CDK pipelines CdkPipeline object
        :param props: The dictionary loaded from config directory.
        :param stage: The stage at which deploy - example: dr, prod, ppe

        :return: None
        """
        props["stage"] = stage
        stage = CodeQualityStage(
            self,
            construct_id=f"{stage}-{pipeline_vars.project}-code-quality-stage",
            env=env,
            props=props,
        )
        apply_tags(props=props, resource=stage)

        pre_commit = pipelines.ShellStep(
            "pre-commit",
            commands=[
                "git init .",
                "git add .",
                "python3 -m pip install --upgrade pip",
                "pip install -r cdk/stacks/requirements.txt",
                "pre-commit run --files app.py",
                "pre-commit run --files cdk/constructs/*.py",
                "pre-commit run --files cdk/schemas/*.py",
                "pre-commit run --files cdk/stacks/*.py",
                "pre-commit run --files cdk/stacks/services/*.py",
                "pre-commit run --files cdk/stacks/plugins/*.py",
                "pre-commit run --files cdk/stacks/plugins/pipeline_trigger/*.py",
                "pre-commit run --files cdk/stages/*.py",
                "pre-commit run --files cdk/utils/*.py",
                "pre-commit run --files cdk/tests/infrastructure/*.py",
            ],
        )

        ansible_lint = pipelines.ShellStep(
            "ansible-lint",
            commands=[
                "pip install -r cdk/stacks/requirements.txt",
                "ansible-lint -p --nocolor ansible/",
            ],
        )

        pre_jobs = [pre_commit]
        if check_ansible_dir(directory="../ansible"):
            pre_jobs.append(ansible_lint)

        pipeline.add_stage(stage=stage, pre=pre_jobs)

    def infrastructure_test_stage(
        self,
        env: cdk.Environment,
        pipeline: pipelines.CodePipeline,
        props: dict,
        stage: str,
        pipeline_vars: PipelineVars,
    ) -> None:
        """Create CI/CD stage which contains several jobs for various tests.

        :param pipeline_vars: Pydantic model that contains configuration values loaded initially from config files
        :param env: The AWS CDK Environment class which provides AWS Account ID and AWS Region
        :param pipeline: The AWS CDK pipelines CdkPipeline object
        :param props: The dictionary loaded from config directory.
        :param stage: The stage at which deploy - example: dr, prod, ppe

        :return: None
        """
        props["stage"] = stage
        stage = InfrastructureTestsStage(
            self,
            construct_id=f"{stage}-{pipeline_vars.project}-infrastructure-tests-stage",
            env=env,
            props=props,
        )
        apply_tags(props=props, resource=stage)

        unit_test_stacks = pipelines.ShellStep(
            "unit_test_stacks",
            commands=[
                "python3 -m pip install --upgrade pip",
                "pip install -r requirements.txt",
                "npm install -g aws-cdk",
                "pip install -r cdk/stacks/requirements.txt",
                "pip install pytest",
                f"STAGE={props['stage']} pytest -v cdk/tests/unit/",
            ],
        )

        pre_jobs = [
            unit_test_stacks,
        ]

        pipeline.add_stage(stage=stage, pre=pre_jobs)

    def shared_resources_stage(
        self,
        env: cdk.Environment,
        stage: str,
        pipeline: pipelines.CodePipeline,
        props: dict,
        pipeline_vars: PipelineVars,
    ) -> None:
        """Create core shared resources stage.

        :param stage: The type of environment, example prod, ppe, dr
        :param env: The AWS CDK Environment class which provides AWS
            Account ID and AWS Region
        :param pipeline: The AWS CDK pipelines CdkPipeline object
        :param props: The dictionary loaded from config directory
        :param pipeline_vars: Pydantic model that contains configuration
            values loaded initially from config files
        :return: None
        """
        stage = SharedResourcesStage(
            self,
            construct_id=f"{stage}-{pipeline_vars.project}-shared-resources-stage",
            env=env,
            props=props,
        )
        apply_tags(props=props, resource=stage)
        pipeline.add_stage(stage=stage)

    def notifications_topic(self, pipeline_vars: PipelineVars) -> sns.Topic:
        """Create an SNS topic used in CI/CD notifications.

        :param pipeline_vars: Pydantic model that contains configuration
            values loaded initially from config files
        :return sns.Topic: The AWS SNS Topic instance
        """
        notifications_sns_topic = sns.Topic(self, "notifications_topic", display_name="CodePipeline notifications")
        notifications_sns_topic.add_subscription(
            topic_subscription=sns_subscriptions.EmailSubscription(email_address=pipeline_vars.ci_cd_notification_email)
        )

        # Warning suppression for cdk_nag
        notifications_sns_topic_cfn = notifications_sns_topic.node.default_child
        notifications_sns_topic_cfn.add_metadata(
            "cdk_nag",
            {
                "rules_to_suppress": [
                    {"id": "AwsSolutions-SNS2", "reason": "Notification topic don't require encryption"}
                ]
            },
        )
        return notifications_sns_topic

    @staticmethod
    def pipeline_email_notifications(sns_topic: sns.Topic) -> None:
        """Create SNS subscription which will be used to send email
        notifications during CodePipeline execution.

        :param sns_topic: The AWS CDK SNS topic instance
        :return: None
        """
        sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal(service="codestar-notifications.amazonaws.com")],
                actions=["SNS:Publish"],
                resources=[sns_topic.topic_arn],
            )
        )

    def pipeline_notifications(self, sns_topic: sns.ITopic) -> None:
        """Create SNS subscription which will be used to send email
        notifications during CodePipeline execution.

        :return: None
        """
        sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal(service="codestar-notifications.amazonaws.com")],
                actions=["SNS:Publish"],
                resources=[sns_topic.topic_arn],
            )
        )

        # The CodePipeline notifications available rules:
        # https://docs.aws.amazon.com/dtconsole/latest/userguide/concepts.html#events-ref-repositories
        NotificationRule(
            self,
            "codepipeline_notifications",
            detail_type=DetailType.FULL,
            events=[
                "codepipeline-pipeline-pipeline-execution-failed",
                "codepipeline-pipeline-action-execution-failed",
                "codepipeline-pipeline-stage-execution-failed",
                "codepipeline-pipeline-manual-approval-failed",
                "codepipeline-pipeline-manual-approval-needed",
            ],
            source=self.codepipeline.pipeline,
            targets=[sns_topic],
        )

    def environment_type(self, env: cdk.Environment, stage: str, props: dict):
        """Create environment using a dedicated AWS account, including a
        different AWS region.

        :param stage: The type of environment, example prod, ppe, dr
        :param env: The AWS CDK environment object.
        :param props: The dictionary loaded from config directory.
        """
        props_env: dict[list, dict] = {}

        # pylint: disable=W0612
        for dir_path, dir_names, files in walk(f"cdk/config/{stage}", topdown=False):
            for file_name in files:
                with open(path.join(dir_path, file_name), encoding="utf-8") as f:
                    props_env |= yaml.safe_load(f)

        props = {**props_env, **props, "stage": stage}
        pipeline_vars = PipelineVars(**props)

        self.plugins_stage(env=env, pipeline=self.codepipeline, props=props, pipeline_vars=pipeline_vars, stage=stage)
        self.shared_resources_stage(
            env=env, pipeline=self.codepipeline, props=props, pipeline_vars=pipeline_vars, stage=stage
        )

    def plugins_stage(
        self,
        env: cdk.Environment,
        stage: str,
        pipeline: pipelines.CodePipeline,
        props: dict,
        pipeline_vars: PipelineVars,
    ) -> None:
        """Create Bots stage.

        :param stage: The type of environment, example prod, ppe, dr
        :param env: The AWS CDK Environment class which provides AWS
            Account ID and AWS Region
        :param pipeline: The AWS CDK pipelines CdkPipeline object
        :param props: The dictionary loaded from config directory
        :param pipeline_vars: Pydantic model that contains configuration
            values loaded initially from config files
        :return: None
        """

        pipeline_stage = PluginsStage(
            self,
            construct_id=f"{stage}-{pipeline_vars.project}-plugins-stage",
            env=env,
            props=props,
        )
        apply_tags(props=props, resource=pipeline_stage)

        pipeline.add_stage(stage=pipeline_stage)
