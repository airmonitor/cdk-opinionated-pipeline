"""Test CDK template."""

from os import environ

import aws_cdk as cdk
import pytest

from aws_cdk.assertions import Template
from cdk_opinionated_constructs.stacks.notifications_stack import NotificationsStack

from cdk.schemas.configuration_vars import PipelineVars
from cdk.tests.infrastructure import load_properties

STAGE = environ["STAGE"]

PROPS = load_properties(stage=STAGE)

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
