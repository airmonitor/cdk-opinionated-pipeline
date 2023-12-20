"""CDK constructs for opinionated S3 bucket, SNS topic, SQS Queue."""

import aws_cdk.aws_sns as sns

from constructs import Construct

from cdk.schemas.configuration_vars import (
    PipelineVars,
)


class ImportedCoreResources(Construct):
    """Imported resources for the Core stack."""

    # pylint: disable=W0622
    # pylint: disable=W0613
    def __init__(self, scope: Construct, construct_id: str, props, env):
        super().__init__(scope, construct_id)

        self.pipeline_vars = PipelineVars(**props)
        self.output_props = props.copy()

    @property
    def outputs(self):
        """Update props dictionary.

        :return: Updated props dict
        """
        return self.output_props

    @property
    def ci_cd_sns_notifications_topics(self) -> list[sns.ITopic]:
        """Returns docker image tag.

        :return: Updated props dict
        """
        return [
            sns.Topic.from_topic_arn(
                self,
                id=f"ci_cd_sns_notifications_topic_{index}",
                topic_arn=topic_arn,
            )
            for index, topic_arn in enumerate(
                self.pipeline_vars.plugins.pipeline_trigger_upstream_sns_topics,  # type: ignore
            )
        ]
