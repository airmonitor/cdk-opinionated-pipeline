"""Test CDK template."""

from os import environ, walk
from pathlib import Path

import aws_cdk as cdk
import pytest
import yaml

from aws_cdk.assertions import Template

from cdk.schemas.configuration_vars import PipelineVars
from cdk.stacks.notifications_stack import NotificationsStack

STAGE = environ["STAGE"]


def load_properties() -> dict:
    """Loads configuration properties from YAML files.

    Parameters:
      - None

    Returns:
      - props (dict): The loaded configuration properties.

    Functionality:
      - Loads the base config from cdk/config/config-ci-cd.yaml
      - Sets the "stage" property to the STAGE environment variable
      - Walks the cdk/config/{STAGE} directory and loads all YAML files
      - Merges the loaded configs into a single props dict
      - Returns the merged props
    """

    config_path = Path("cdk/config/config-ci-cd.yaml")
    with config_path.open(encoding="utf-8") as file:
        props = yaml.safe_load(file)
        props["stage"] = STAGE

    props_env: dict[list, dict] = {}

    # pylint: disable=W0612
    for dir_path, dir_names, files in walk(f"cdk/config/{STAGE}", topdown=False):  # noqa
        for file_name in files:
            file_path = Path(f"{dir_path}/{file_name}")
            with file_path.open(encoding="utf-8") as f:
                props_env |= yaml.safe_load(f)
                props = {**props_env, **props}

    return props


PROPS = load_properties()

PIPELINE_VARS = PipelineVars(**PROPS)
ENV = cdk.Environment(
    account=PIPELINE_VARS.aws_account,
    region=PIPELINE_VARS.aws_region,
)


@pytest.fixture()
def stack_template() -> Template:
    """Fixture to create a CDK stack template from the NotificationsStack.

    Parameters:
      - None

    Returns:
      - stack_template (Template): The CDK stack template generated from
        the NotificationsStack.

    Functionality:
      - Creates a CDK App
      - Initializes an instance of NotificationsStack with the app, name, env
        and props
      - Uses Template.from_stack() to generate a Template object from the stack
      - Returns this Template, which can be used in tests to validate the
        infrastructure being created.
    """

    app = cdk.App()
    stack = NotificationsStack(app, "stack", env=ENV, props=PROPS)
    return Template.from_stack(stack)


# pylint: disable=redefined-outer-name
def test_sns_topic_existence(stack_template):
    """
    Tests that the AWS::SNS::Topic resource exists in the CDK stack template.

    Parameters:
      - stack_template (Template): The CDK stack template to check.

    Functionality:
      - Uses stack_template.resource_count_is() to assert there is 1 AWS::SNS::Topic
        resource defined in the template.
        This checks that the expected SNS topic
        resource has been created in the CDK stack.

    """

    stack_template.resource_count_is("AWS::SNS::Topic", 1)


def test_sns_subscription_existence(stack_template):
    """
    Tests that the AWS::SNS::Subscription resource exists in the CDK stack template.

    Parameters:
    - stack_template (Template): The CDK stack template to check.

    Functionality:
    - Uses stack_template.resource_count_is() to assert there is 1 AWS::SNS::Subscription
      resource defined in the template.
      This checks that the expected SNS subscription
      resource has been created in the CDK stack.

    """

    stack_template.resource_count_is("AWS::SNS::Subscription", 1)


def test_sns_topic_policy_existence(stack_template):
    """
    Tests that the AWS::SNS::TopicPolicy resource exists in the CDK stack template.

    Parameters:
    - stack_template (Template): The CDK stack template to check.

    Functionality:
    - Uses stack_template.resource_count_is() to assert there is 1 AWS::SNS::TopicPolicy
      resource defined in the template.
      This checks that the expected SNS topic policy
      resource has been created in the CDK stack.

    """

    stack_template.resource_count_is("AWS::SNS::TopicPolicy", 1)


def test_ssm_parameter_existence(stack_template):
    """
    Tests that the AWS::SSM::Parameter resource exists in the CDK stack template.

    Parameters:
    - stack_template (Template): The CDK stack template to check.

    Functionality:
    - Uses stack_template.resource_count_is() to assert that there is 1 AWS::SSM::Parameter
      resource defined in the template.
      This checks that the expected SSM parameter resource
      has been created in the CDK stack.

    """

    stack_template.resource_count_is("AWS::SSM::Parameter", 1)
