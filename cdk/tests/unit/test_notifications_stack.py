# -*- coding: utf-8 -*-
"""Test CDK template."""
from os import path, walk
import yaml
import aws_cdk as cdk
from aws_cdk.assertions import Template
from typing import Dict, List

from cdk.schemas.configuration_vars import PipelineVars
from cdk.stacks.notifications_stack import NotificationsStack

import pytest
from os import environ

STAGE = environ["STAGE"]


def load_properties() -> dict:
    """
    Load all configuration values from yaml files and generate dictionary from them
    :return:
    """
    with open("cdk/config/config-ci-cd.yaml", encoding="utf-8") as file:
        props = yaml.safe_load(file)
        props["stage"] = STAGE

    props_env: Dict[List, Dict] = {}

    # pylint: disable=W0612
    for dir_path, dir_names, files in walk(f"cdk/config/{STAGE}", topdown=False):
        for file_name in files:
            with open(path.join(dir_path, file_name), encoding="utf-8") as f:
                props_env |= yaml.safe_load(f)
                props = {**props_env, **props}

    return props


PROPS = load_properties()

PIPELINE_VARS = PipelineVars(**PROPS)
ENV = cdk.Environment(
    account=PIPELINE_VARS.aws_account,
    region=PIPELINE_VARS.aws_region,
)


@pytest.fixture
def stack_template() -> Template:
    """Returns CDK template."""
    app = cdk.App()
    stack = NotificationsStack(app, "stack", env=ENV, props=PROPS)
    return Template.from_stack(stack)


# pylint: disable=redefined-outer-name
def test_sns_topic_existence(stack_template):
    """Test if ssm parameters exists."""
    stack_template.resource_count_is("AWS::SNS::Topic", 1)


def test_sns_subscription_existence(stack_template):
    """Test if ssm parameters exists."""
    stack_template.resource_count_is("AWS::SNS::Subscription", 1)


def test_sns_topic_policy_existence(stack_template):
    """Test if ssm parameters exists."""
    stack_template.resource_count_is("AWS::SNS::TopicPolicy", 1)


def test_ssm_parameter_existence(stack_template):
    """Test if ssm parameters exists."""
    stack_template.resource_count_is("AWS::SSM::Parameter", 1)
