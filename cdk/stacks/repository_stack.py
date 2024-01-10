"""Deploy AWS CodeCommit repository."""

import aws_cdk as cdk
import aws_cdk.aws_codecommit as codecommit

from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks
from constructs import Construct

from cdk.schemas.configuration_vars import PipelineVars


class RepositoryStack(cdk.Stack):
    """Repository stack."""

    def __init__(self, scope: Construct, construct_id: str, env: cdk.Environment, props: dict, **kwargs) -> None:
        """Initializes the RepositoryStack construct.

        Parameters:
        - scope (Construct): The parent construct.
        - construct_id (str): The construct ID.
        - env (cdk.Environment): The CDK environment.
        - props (dict): Stack configuration properties.
        - **kwargs: Additional keyword arguments passed to the Stack constructor.

        The constructor does the following:

        1. Call the parent Stack constructor.

        2. Create a PipelineVars object from the props.

        3. Create an AWS CodeCommit repository with the name configured in PipelineVars.

        4. Validates the stack against the AWS Solutions checklist using Aspects.
        """

        super().__init__(scope, construct_id, env=env, **kwargs)
        pipeline_vars = PipelineVars(**props)

        codecommit.Repository(self, id=pipeline_vars.repository, repository_name=pipeline_vars.repository)

        Aspects.of(self).add(AwsSolutionsChecks(log_ignores=True))
