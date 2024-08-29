"""Test CDK template."""

from os import environ

import aws_cdk as cdk
import pytest
import yaml

from aws_cdk.assertions import Template
from cdk_opinionated_constructs.utils import load_properties

from cdk.schemas.configuration_vars import PipelineVars
from cdk.stacks.pipeline_stack import PipelineStack

STAGE = environ["STAGE"]

PROPS = load_properties(stage=STAGE)

PIPELINE_VARS = PipelineVars(**PROPS)
ENV = cdk.Environment(
    account=PIPELINE_VARS.aws_account,
    region=PIPELINE_VARS.aws_region,
)


@pytest.fixture
def stack_template() -> Template:
    """Returns a CDK template for the GovernanceStack.

    Creates an instance of the GovernanceStack, providing the required
    props and environment. The template is then generated from the stack
    and returned.
    """

    app = cdk.App()
    stack = PipelineStack(app, "stack", env=ENV, props=PROPS)
    return Template.from_stack(stack)


def test_snapshot(stack_template, snapshot):
    """Tests that the stack template matches a snapshot.

    Parameters:
    - stack_template: The CDK stack template to check.
    - snapshot: The snapshot tester to match against.

    Functionality:
    - Dumps the stack template to YAML and asserts it matches a snapshot file
      with name formatted as {stack_name}_{stage}.yaml.
      This allows snapshot testing the infrastructure stack template.
    """
    snapshot.assert_match(yaml.dump(stack_template.to_json()), f"pipeline_stack_{STAGE}.yaml")
