"""Helper functions to make your life simple."""

from pathlib import Path

import aws_cdk as cdk

from aws_cdk import Stack, Stage


def check_ansible_dir(directory: str) -> bool:
    """Check if ansible directory exists in a root path.

    :return: Bool - True if ansible directory exist, false if not
    """
    this_dir = Path(__file__).parent
    ansible_path = this_dir.joinpath(directory).resolve()
    return ansible_path.is_dir()


def apply_tags(props: dict, resource: cdk.Stack | cdk.Stage) -> Stack | Stage:
    """Add standardized tags to every resource created in stack.

    :param props: Contain standardized tags (key value) for TR
    :param resource: CDK Stack, Stage or app
    :return: Input object (class) with added tags
    """
    for key, value in props["tags"].items():
        cdk.Tags.of(resource).add(key, value)

    return resource
