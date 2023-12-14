"""The pre-prerequisites stack which create resource which needs to exist
before core stack will be created.

Example is SSM parameter store entry ci/cd configuration values
"""
from os import path, walk

import aws_cdk as cdk
import aws_cdk.aws_ssm as ssm
import yaml
from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks
from constructs import Construct

from cdk.schemas.configuration_vars import ConfigurationVars


class CodeQualityStack(cdk.Stack):
    """Create SSM Parameter required by CDK Pipelines.

    As CDK pipeline can't contain empty stage to which additional jobs
    will be added, this stack will create AWS SSM parameter store with
    the content of used configuration file. It is done like this as a
    workaround to the CDK pipelines limitations.
    """

    def __init__(self, scope: Construct, construct_id: str, env, props, **kwargs) -> None:
        super().__init__(scope, construct_id, env=env, **kwargs)
        props_env: dict[list, dict] = {}
        config_vars = ConfigurationVars(**props)
        # pylint: disable=W0612
        for dir_path, dir_names, files in walk(f"cdk/config/{config_vars.stage}", topdown=False):
            for file_name in files:
                with open(path.join(dir_path, file_name), encoding="utf-8") as f:
                    props_env |= yaml.safe_load(f)
                    props = {**props_env, **props}

        ssm.StringParameter(
            self,
            id="config_file",
            string_value=str(props_env),
            parameter_name=f"/{config_vars.project}/{config_vars.stage}/config",
        )

        Aspects.of(self).add(AwsSolutionsChecks(log_ignores=True))
