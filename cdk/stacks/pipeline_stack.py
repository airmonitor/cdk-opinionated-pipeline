"""Deploy AWS CI/CD stack with all stages."""

import aws_cdk as cdk
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codecommit as codecommit
import aws_cdk.aws_events as events
import aws_cdk.aws_iam as iam

from aws_cdk import pipelines
from cdk_opinionated_constructs.stacks import create_pipeline_notifications, notifications_topic, pipeline_trigger
from cdk_opinionated_constructs.stages.logic import (
    default_install_commands,
)
from cdk_opinionated_constructs.utils import load_properties
from constructs import Construct

from cdk.schemas.configuration_vars import PipelineVars
from cdk.stages.logic.stages import code_quality_stage, plugins_stage, shared_resources_stage


class PipelineStack(cdk.Stack):
    """CI/CD Pipeline stack."""

    def __init__(self, scope: Construct, construct_id: str, env: cdk.Environment, props: dict, **kwargs) -> None:
        """Initializes a new instance of the PipelineStack class, which creates
        an AWS CDK pipeline with stages for code quality checks, infrastructure
        tests, and deployment. It also sets up notifications and a trigger for
        the pipeline. This stack is meant to be used within an AWS
        account/environment specified by the `env` parameter, and it uses
        configuration from `props`.

        Args:
            scope (Construct): The scope in which to define this construct (usually `self`).
            construct_id (str): The unique identifier for the construct.
            env (cdk.Environment): The AWS environment (account/region) where the stack will be deployed.
            props (dict): A dictionary of properties for configuring the pipeline.
            **kwargs: Additional keyword arguments to be passed to the parent class.

        Attributes:
            codepipeline (pipelines.CodePipeline): The created CodePipeline instance with the defined stages and steps.
        """
        super().__init__(scope, construct_id, env=env, **kwargs)
        pipeline_vars = PipelineVars(**props)

        notifications_sns_topic = notifications_topic(self, pipeline_vars=pipeline_vars)

        imported_repository = codecommit.Repository.from_repository_name(
            self,
            id="imported_repository",
            repository_name=pipeline_vars.repository,
        )

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
                install_commands=[
                    "n 22",
                    "pip install uv",
                    "make venv",
                    "source .venv/bin/activate",
                    *default_install_commands,
                ],
                commands=[
                    "source .venv/bin/activate",
                    "cdk synth -q",
                ],
            ),
            pipeline_name=pipeline_vars.project,
            self_mutation=True,
        )

        # DEV resources
        stage_name = "dev"
        _env = cdk.Environment(
            account=pipeline_vars.aws_account,
            region=pipeline_vars.aws_region,
        )

        code_quality_stage(
            self, env=_env, pipeline=self.codepipeline, props=props, pipeline_vars=pipeline_vars, stage_name=stage_name
        )

        self.environment_type(
            env=_env,
            stage_name=stage_name,
        )

        self.codepipeline.build_pipeline()

        create_pipeline_notifications(
            self, notifications_sns_topic=notifications_sns_topic, pipeline_vars=pipeline_vars, source=self.codepipeline
        )

        pipeline_trigger(
            self,
            pipeline_vars=pipeline_vars,
            props=props,
            schedule=events.Schedule.cron(minute="0", hour="05", month="*", day="7,14,21,28", year="*"),
        )

    def environment_type(self, env: cdk.Environment, stage_name: str):
        """Loads environment configuration and creates pipeline stages.

        Parameters:

        env (cdk.Environment): The CDK environment object.

        stage_name (str): The environment name (e.g. 'dev', 'prod').

        Functionality:

        1. load all YAML config files for the environment into props_env.

        2. merge props_env and props into a single props dict.

        3. create a PipelineVars model from the merged props.

        4. call plugins_stage() to create the Plugins stage, passing props and PipelineVars.

        5. call shared_resources_stage() to create the shared resources stage, passing props, and PipelineVars.

        this allows environment-specific configuration to be loaded from YAML files and passed to the pipeline stages.
        """

        props_env = load_properties(stage=stage_name)
        updated_props = {**props_env, "stage": stage_name}
        pipeline_vars = PipelineVars(**updated_props)

        plugins_stage(
            self,
            env=env,
            pipeline=self.codepipeline,
            props=updated_props,
            pipeline_vars=pipeline_vars,
            stage_name=stage_name,
        )
        shared_resources_stage(
            self,
            env=env,
            pipeline=self.codepipeline,
            props=updated_props,
            pipeline_vars=pipeline_vars,
            stage_name=stage_name,
        )
