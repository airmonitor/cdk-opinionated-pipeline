import aws_cdk as cdk

from aws_cdk import pipelines
from cdk_opinionated_constructs.stages.code_quality_stage import CodeQualityStage
from cdk_opinionated_constructs.stages.infrastructure_tests_stage import InfrastructureTestsStage
from cdk_opinionated_constructs.stages.plugins_stage import PluginsStage
from cdk_opinionated_constructs.utils import apply_tags, load_properties

from cdk.schemas.configuration_vars import PipelineVars
from cdk.stages.shared_resources_stage import SharedResourcesStage


def infrastructure_test_stage(
    self,
    env: cdk.Environment,
    pipeline: pipelines.CodePipeline,
    props: dict,
    stage_name: str,
    pipeline_vars: PipelineVars,
) -> None:
    """Creates an infrastructure test stage in the pipeline.

    Parameters:

    env (cdk.Environment): The CDK environment object.

    pipeline (pipelines.CodePipeline): The CDK pipeline object.

    props (dict): A dictionary of configuration properties.

    stage_name (str): The name of the stage (e.g. 'dev', 'prod').

    pipeline_vars (PipelineVars): A model containing pipeline configuration values.

    Functionality:

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
    props["stage"] = stage_name
    _stage = InfrastructureTestsStage(
        self,
        construct_id=f"{stage_name}-{pipeline_vars.project}-infrastructure-tests-stage",
        env=env,
        props=props,
    )
    apply_tags(props=load_properties(stage=stage_name), resource=_stage)

    unit_test_stacks = pipelines.ShellStep(
        "unit_test_stacks",
        install_commands=["pip install uv", "make install", "pip install pytest", "npm install -g aws-cdk"],
        commands=[f"make test STAGE={props['stage']}"],
    )

    pre_jobs = [
        unit_test_stacks,
    ]

    pipeline.add_stage(stage=_stage, pre=pre_jobs)


def shared_resources_stage(
    self,
    env: cdk.Environment,
    stage_name: str,
    pipeline: pipelines.CodePipeline,
    props: dict,
    pipeline_vars: PipelineVars,
) -> None:
    """Create shared resources stage.

    Parameters:

    - env (cdk.Environment): The AWS CDK Environment class which provides AWS Account ID and AWS Region.

    - stage_name (str): The type of environment, example prod, ppe, dr.

    - pipeline (pipelines.CodePipeline): The AWS CDK pipelines CdkPipeline object.

    - props (dict): The dictionary loaded from config directory.

    - pipeline_vars (PipelineVars):
    Pydantic model that contains configuration values loaded initially from config files.

    Functionality:

    - create a SharedResourcesStage construct with the provided parameters.

    - apply tags to the stage based on props.

    - add the stage to the pipeline.
    """
    _stage = SharedResourcesStage(
        self,
        construct_id=f"{stage_name}-{pipeline_vars.project}-shared-resources-stage",
        env=env,
        props=props,
    )
    apply_tags(props=load_properties(stage=stage_name), resource=_stage)
    pipeline.add_stage(stage=_stage)


def code_quality_stage(
    self,
    env: cdk.Environment,
    pipeline: pipelines.CodePipeline,
    props: dict,
    stage_name: str,
    pipeline_vars: PipelineVars,
) -> None:
    """Creates a code quality stage in the pipeline.

    Parameters:

    env (cdk.Environment): The CDK environment object.

    pipeline (pipelines.CodePipeline): The CDK pipeline object.

    props (dict): A dictionary of configuration properties.

    stage_name (str): The name of the stage (e.g. 'dev', 'prod').

    pipeline_vars (PipelineVars): A model containing pipeline configuration values.


    Functionality:

    1. create a new CodeQualityStage with the provided parameters.

    2. apply tags to the stage based on props.

    3. create a ShellStep to run pre-commit on source files.

    4. create a ShellStep to run ansible-lint if there is an ansible directory.

    5. add the ShellSteps as pre-jobs to the stage.

    6. add the stage to the pipeline.
    """
    props["stage"] = stage_name
    _stage = CodeQualityStage(
        self,
        construct_id=f"{stage_name}-{pipeline_vars.project}-code-quality-stage",
        env=env,
        props=props,
    )
    apply_tags(props=load_properties(stage=stage_name), resource=_stage)

    pre_commit = pipelines.ShellStep(
        "pre_commit",
        install_commands=[
            "pip install uv",
            "make install",
            "pip install pre-commit prek",
        ],
        commands=[
            "git init .",
            "git add .",
            "make pre-commit",
        ],
    )

    pre_jobs = [pre_commit]

    pipeline.add_stage(stage=_stage, pre=pre_jobs)


def plugins_stage(
    self,
    env: cdk.Environment,
    stage_name: str,
    pipeline: pipelines.CodePipeline,
    props: dict,
    pipeline_vars: PipelineVars,
) -> None:
    """Create plugin stage.

    Parameters:

    - env (cdk.Environment): The AWS CDK Environment class which provides AWS Account ID and AWS Region.

    - stage_name (str): The type of environment, example prod, ppe, dr.

    - pipeline (pipelines.CodePipeline): The AWS CDK pipelines CdkPipeline object.

    - props (dict): The dictionary loaded from config directory.

    - pipeline_vars (PipelineVars):
    Pydantic model that contains configuration values loaded initially from config files.

    Functionality:

    - create a PluginsStage construct with the provided parameters.

    - apply tags to the stage based on props.

    - add the stage to the pipeline.
    """

    _stage = PluginsStage(
        self,
        construct_id=f"{stage_name}-{pipeline_vars.project}-plugins-stage",
        env=env,
        props=props,
    )
    apply_tags(props=load_properties(stage=stage_name), resource=_stage)

    pipeline.add_stage(stage=_stage)
