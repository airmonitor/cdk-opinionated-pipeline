"""Main script for an AWS CDK framework which deploys the AWS CI/CD pipeline
stack."""
from pathlib import Path

import aws_cdk as cdk
import yaml

from cdk.schemas.configuration_vars import PipelineVars
from cdk.stacks.pipeline_stack import PipelineStack
from cdk.utils.utils import apply_tags

app = cdk.App()

config_ci_cd_path = Path("cdk/config/config-ci-cd.yaml")
with config_ci_cd_path.open(encoding="utf-8") as file:
    PROPS = yaml.safe_load(file)
    pipeline_vars = PipelineVars(**PROPS)

ENV = cdk.Environment(
    account=pipeline_vars.aws_account,
    region=pipeline_vars.aws_region,
)

ci_cd_pipeline_stack = PipelineStack(app, construct_id=f"{pipeline_vars.project}-pipeline", env=ENV, props=PROPS)

apply_tags(props=PROPS, resource=ci_cd_pipeline_stack)

app.synth()
