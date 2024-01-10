"""Deploy AWS CI/CD stack with all stages."""

from os import walk
from pathlib import Path

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

from cdk.schemas.configuration_vars import NotificationVars, PipelineVars
from cdk.stages.code_quality_stage import CodeQualityStage
from cdk.stages.infrastructure_tests_stage import InfrastructureTestsStage
from cdk.stages.plugins_stage import PluginsStage
from cdk.stages.shared_resources_stage import SharedResourcesStage
from cdk.utils.utils import apply_tags, check_ansible_dir


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
            self,
            id="imported_repository",
            repository_name=pipeline_vars.repository,
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
                    build_image=codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,  # type: ignore
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
            env=env,
            pipeline=self.codepipeline,
            props=props,
            pipeline_vars=pipeline_vars,
            stage="dev",
        )

        # DEV resources
        stage = "dev"
        env = cdk.Environment(
            account=pipeline_vars.aws_account,
            region=pipeline_vars.aws_region,
        )
        self.infrastructure_test_stage(
            env=env,
            pipeline=self.codepipeline,
            props=props,
            pipeline_vars=pipeline_vars,
            stage=stage,
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
        self,
        notifications_sns_topic: sns.Topic | sns.ITopic,
        notification_vars: NotificationVars,
        pipeline_vars: PipelineVars,
    ):
        """Creates notifications for the pipeline.

        parameters:

        notifications_sns_topic (sns.Topic | sns.ITopic): The SNS topic to publish notifications to.

        pipeline_vars (PipelineVars): A Pydantic model containing pipeline configuration values like
        notification email, Slack workspace ID, etc.

        functionality:

        1. if a notification email address is provided in pipeline_vars, enable email notifications by calling
        pipeline_email_notifications()

        2. enable default pipeline notifications by calling pipeline_notifications()

        3. if Slack workspace ID and channel ID are provided in pipeline_vars, enable Slack notifications by
        creating a SlackChannelConfiguration construct
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
        """Creates a scheduled rule to trigger the pipeline.

        parameters:

        pipeline_vars (PipelineVars): A model containing pipeline configuration values.

        props (dict): A dictionary of configuration properties.

        schedule (events.Schedule): The scheduled interval to trigger the pipeline.

        functionality:

        1. create a Rule with the provided schedule, enabled status, name, and description.

        2. add the pipeline as a target for the rule.
        this will trigger the pipeline on the schedule.

        3. apply tags to the rule based on props.
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
        trigger.add_target(events_targets.CodePipeline(self.codepipeline.pipeline))  # type: ignore
        apply_tags(props=props, resource=trigger)  # type: ignore

    def code_quality_stage(
        self,
        env: cdk.Environment,
        pipeline: pipelines.CodePipeline,
        props: dict,
        stage: str,
        pipeline_vars: PipelineVars,
    ) -> None:
        """Creates a code quality stage in the pipeline.

        parameters:

        env (cdk.Environment): The CDK environment object.

        pipeline (pipelines.CodePipeline): The CDK pipeline object.

        props (dict): A dictionary of configuration properties.

        stage (str): The name of the stage (e.g. 'dev', 'prod').

        pipeline_vars (PipelineVars): A model containing pipeline configuration values.


        functionality:

        1. create a new CodeQualityStage with the provided parameters.

        2. apply tags to the stage based on props.

        3. create a ShellStep to run pre-commit on source files.

        4. create a ShellStep to run ansible-lint if there is an ansible directory.

        5. add the ShellSteps as pre-jobs to the stage.

        6. add the stage to the pipeline.
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
                "pre-commit run --files cdk/tests/integration/*.py",
                "pre-commit run --files cdk/tests/*.py",
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
        """Creates an infrastructure test stage in the pipeline.

        parameters:

        env (cdk.Environment): The CDK environment object.

        pipeline (pipelines.CodePipeline): The CDK pipeline object.

        props (dict): A dictionary of configuration properties.

        stage (str): The name of the stage (e.g. 'dev', 'prod').

        pipeline_vars (PipelineVars): A model containing pipeline configuration values.

        functionality:

        1. create a new InfrastructureTestsStage with the provided parameters.

        2. apply tags to the stage based on props.

        3. create a ShellStep to run infrastructure tests:
           - Install dependencies
           - Install AWS CDK
           - Install pytest
           - Run pytest on the infrastructure tests and pass the stage name

        4. add the ShellStep as a pre-job to the stage.

        5. add the stage to the pipeline.
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
        """Create shared resources stage.

        parameters:

        - env (cdk.Environment): The AWS CDK Environment class which provides AWS Account ID and AWS Region.

        - stage (str): The type of environment, example prod, ppe, dr.

        - pipeline (pipelines.CodePipeline): The AWS CDK pipelines CdkPipeline object.

        - props (dict): The dictionary loaded from config directory.

        - pipeline_vars (PipelineVars):
        Pydantic model that contains configuration values loaded initially from config files.

        functionality:

        - create a SharedResourcesStage construct with the provided parameters.

        - apply tags to the stage based on props.

        - add the stage to the pipeline.
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
        """Creates an SNS topic for pipeline notifications.

        parameters:

        pipeline_vars (PipelineVars): A model containing pipeline configuration values like notification email.

        functionality:

        1. create an SNS topic called 'notifications_topic' to be used for notifications.

        2. add a subscription to the topic using the email address from pipeline_vars.

        3. add metadata to suppress cdk_nag warnings about encryption.

        4. return the created SNS topic.
        """
        notifications_sns_topic = sns.Topic(self, "notifications_topic", display_name="CodePipeline notifications")
        notifications_sns_topic.add_subscription(
            topic_subscription=sns_subscriptions.EmailSubscription(
                email_address=pipeline_vars.ci_cd_notification_email,
            ),
        )

        # Warning suppression for cdk_nag
        notifications_sns_topic_cfn = notifications_sns_topic.node.default_child
        notifications_sns_topic_cfn.add_metadata(
            "cdk_nag",
            {
                "rules_to_suppress": [
                    {"id": "AwsSolutions-SNS2", "reason": "Notification topic don't require encryption"},
                ],
            },
        )
        return notifications_sns_topic

    @staticmethod
    def pipeline_email_notifications(sns_topic: sns.Topic) -> None:
        """Configures email notifications for the pipeline SNS topic.

        parameters:

        sns_topic (sns.Topic): The SNS topic to configure notifications for.

        functionality:

        - adds a resource policy to the SNS topic to allow CodeStar Notifications
        to publish messages to it.

        - this enables email notifications to be sent on pipeline events.
        """
        sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal(service="codestar-notifications.amazonaws.com")],
                actions=["SNS:Publish"],
                resources=[sns_topic.topic_arn],
            ),
        )

    def pipeline_notifications(self, sns_topic: sns.ITopic) -> None:
        """Configures notifications for pipeline events.

        parameters:

        sns_topic (sns.ITopic): The SNS topic to send notifications to.

        functionality:

        1. add resource policy to an SNS topic to allow CodeStar Notifications to publish.

        2. create a NotificationRule to send notifications on pipeline events:
           - Pipeline execution failed
           - Action execution failed
           - Stage execution failed
           - Manual approval failed
           - Manual approval needed

        the notification rule will send messages to the provided SNS topic.
        """

        sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal(service="codestar-notifications.amazonaws.com")],
                actions=["SNS:Publish"],
                resources=[sns_topic.topic_arn],
            ),
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
        """Loads environment configuration and creates pipeline stages.

        parameters:

        env (cdk.Environment): The CDK environment object.

        stage (str): The environment name (e.g. 'dev', 'prod').

        props (dict): Pipeline configuration properties.

        functionality:

        1. load all YAML config files for the environment into props_env.

        2. merge props_env and props into a single props dict.

        3. create a PipelineVars model from the merged props.

        4. call plugins_stage() to create the Plugins stage, passing props and PipelineVars.

        5. call shared_resources_stage() to create the shared resources stage, passing props, and PipelineVars.

        this allows environment-specific configuration to be loaded from YAML files and passed to the pipeline stages.
        """

        props_env: dict[list, dict] = {}

        # pylint: disable=W0612
        for dir_path, dir_names, files in walk(f"cdk/config/{stage}", topdown=False):  # noqa
            for file_name in files:
                file_path = Path(f"{dir_path}/{file_name}")
                with file_path.open(encoding="utf-8") as f:
                    props_env |= yaml.safe_load(f)

        props = {**props_env, **props, "stage": stage}
        pipeline_vars = PipelineVars(**props)

        self.plugins_stage(env=env, pipeline=self.codepipeline, props=props, pipeline_vars=pipeline_vars, stage=stage)
        self.shared_resources_stage(
            env=env,
            pipeline=self.codepipeline,
            props=props,
            pipeline_vars=pipeline_vars,
            stage=stage,
        )

    def plugins_stage(
        self,
        env: cdk.Environment,
        stage: str,
        pipeline: pipelines.CodePipeline,
        props: dict,
        pipeline_vars: PipelineVars,
    ) -> None:
        """Create plugin stage.

        parameters:

        - env (cdk.Environment): The AWS CDK Environment class which provides AWS Account ID and AWS Region.

        - stage (str): The type of environment, example prod, ppe, dr.

        - pipeline (pipelines.CodePipeline): The AWS CDK pipelines CdkPipeline object.

        - props (dict): The dictionary loaded from config directory.

        - pipeline_vars (PipelineVars):
        Pydantic model that contains configuration values loaded initially from config files.

        functionality:

        - create a PluginsStage construct with the provided parameters.

        - apply tags to the stage based on props.

        - add the stage to the pipeline.
        """

        pipeline_stage = PluginsStage(
            self,
            construct_id=f"{stage}-{pipeline_vars.project}-plugins-stage",
            env=env,
            props=props,
        )
        apply_tags(props=props, resource=pipeline_stage)

        pipeline.add_stage(stage=pipeline_stage)
