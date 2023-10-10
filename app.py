"""Main script for AWS CDK framework which deploy the AWS CI/CD pipeline
stack."""
import aws_cdk as cdk
import yaml

from cdk.schemas.configuration_vars import PipelineVars
from cdk.stacks.pipeline_stack import PipelineStack
from cdk.utils.utils import apply_tags

app = cdk.App()

# The first deployment "cdk deploy -c stage=poc1" will mark stage permanent to cdk pipeline for subsequent commits


with open("cdk/config/config-ci-cd.yaml", encoding="utf-8") as file:
    PROPS = yaml.safe_load(file)
    pipeline_vars = PipelineVars(**PROPS)

ENV = cdk.Environment(
    account=pipeline_vars.aws_account,
    region=pipeline_vars.aws_region,
)

ci_cd_pipeline_stack = PipelineStack(app, construct_id=f"{pipeline_vars.project}-pipeline", env=ENV, props=PROPS)

apply_tags(props=PROPS, resource=ci_cd_pipeline_stack)

app.synth()
