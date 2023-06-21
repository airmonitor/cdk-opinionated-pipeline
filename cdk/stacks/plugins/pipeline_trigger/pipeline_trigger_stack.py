# -*- coding: utf-8 -*-
# mypy: ignore-errors
"""Deploy AWS Core application resources."""
import aws_cdk as cdk
import aws_cdk.aws_codepipeline as pipeline
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as events_targets
import aws_cdk.aws_iam as iam
from constructs import Construct

from cdk.schemas.configuration_vars import ConfigurationVars, PipelineVars


class PipelineTriggerStack(cdk.Stack):
    """AWS Lambda that triggers this pipeline when the upstream pipeline
    succeeded.

    This pipeline deploys a container image created in the upstream
    pipeline to ECS fargate
    """

    def __init__(self, scope: Construct, construct_id: str, env: cdk.Environment, props: dict, **kwargs) -> None:
        """Initialize default parameters from AWS CDK and configuration file.

        :param scope: The AWS CDK parent class from which this class inherits
        :param construct_id: The name of CDK construct
        :param env: Tha AWS CDK Environment class which provide AWS Account ID and AWS Region
        :param props: The dictionary which contain configuration values loaded initially from /config/config-env.yaml
        :param kwargs:
        """
        super().__init__(scope, construct_id, env=env, **kwargs)
        config_vars = ConfigurationVars(**props)
        pipeline_vars = PipelineVars(**props)

        # Filter all ssm parameters which have the name of the stage
        filtered_ssm_parameters = list(
            filter(lambda x: config_vars.stage in x, pipeline_vars.plugins.pipeline_trigger_ssm_parameters)
        )

        event_pattern = events.EventPattern(
            source=["aws.ssm"],
            detail_type=["Parameter Store Change"],
            detail={"name": filtered_ssm_parameters, "operation": ["Create", "Update"]},
        )

        if filtered_ssm_parameters:
            print(filtered_ssm_parameters)
            events_iam_role_policy = iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=["codepipeline:StartPipelineExecution"],
                        resources=[
                            f"arn:aws:codepipeline:{config_vars.aws_region}:{config_vars.aws_account}:{config_vars.project}"
                        ],
                    ),
                ]
            )
            events_iam_role = iam.Role(
                self,
                id="events_iam_role",
                role_name=f"{config_vars.project}-{config_vars.stage}-pipeline-trigger",
                assumed_by=iam.ServicePrincipal(service="events.amazonaws.com"),
                inline_policies={"allow_starting_codepipeline": events_iam_role_policy},
            )
            events.Rule(
                self,
                id="rule_start_codepipeline",
                event_pattern=event_pattern,
                targets=[
                    events_targets.CodePipeline(
                        event_role=events_iam_role,
                        pipeline=pipeline.Pipeline.from_pipeline_arn(
                            self,
                            id="imported_codepipeline",
                            pipeline_arn=f"arn:aws:codepipeline:{config_vars.aws_region}:{config_vars.aws_account}:{config_vars.project}",
                        ),
                    )
                ],
            )
