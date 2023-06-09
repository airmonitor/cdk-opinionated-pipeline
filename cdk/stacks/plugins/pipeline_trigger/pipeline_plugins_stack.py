# -*- coding: utf-8 -*-
"""The pre-prerequisites stack which create resource which needs to exist
before core stack will be created.

Example is SSM parameter store entry ci/cd configuration values
"""
from os import path, walk
from typing import Dict, List

import aws_cdk as cdk
import aws_cdk.aws_ssm as ssm
import yaml
from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks
from constructs import Construct

from cdk.schemas.configuration_vars import ConfigurationVars, PipelineVars


class PipelinePluginsStack(cdk.Stack):
    """Create SSM Parameter required by CDK Pipelines.

    As CDK pipeline can't contain empty stage to which additional jobs
    will be added, this stack will create AWS SSM parameter store with
    the content of used configuration file. It is done like this as a
    workaround to the CDK pipelines limitations.
    """

    def __init__(self, scope: Construct, construct_id: str, env, props, **kwargs) -> None:
        super().__init__(scope, construct_id, env=env, **kwargs)
        props_env: Dict[List, Dict] = {}

        # pylint: disable=W0612
        for dir_path, dir_names, files in walk(f"cdk/config/{props['stage']}", topdown=False):
            for file_name in files:
                with open(path.join(dir_path, file_name), encoding="utf-8") as f:
                    props_env |= yaml.safe_load(f)
                    props = {**props_env, **props}

        config_vars = ConfigurationVars(**props)
        pipeline_vars = PipelineVars(**props)

        ssm.StringParameter(
            self,
            id="pipeline_plugins",
            string_value=str(pipeline_vars.plugins),
            parameter_name=f"/{config_vars.stage}/{config_vars.project}/pipeline_plugins",
        )

        Aspects.of(self).add(AwsSolutionsChecks(log_ignores=True))
