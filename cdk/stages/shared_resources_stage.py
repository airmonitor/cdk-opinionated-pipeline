"""The AWS shared resources for core application stage."""

import aws_cdk as cdk

from cdk_opinionated_constructs.stacks.notifications_stack import NotificationsStack
from constructs import Construct


class SharedResourcesStage(cdk.Stage):
    """Create CI/CD stage with shared resources."""

    def __init__(self, scope: Construct, construct_id: str, env: cdk.Environment, props: dict, **kwargs) -> None:
        """
        Parameters:

        - scope (Construct): The parent constructs that this stage is defined within.

        - construct_id (str): The id of this stage construct.

        - env (cdk.Environment): The CDK environment this stage is targeting.

        - props (dict): A dictionary of properties to configure this stage.

        Functionality:

        - Initializes the SharedResourcesStage, inheriting from cdk.Stage.

        - Passes the scope, construct_id, env and props to the parent cdk.Stage constructor.

        - Creates an instance of the NotificationsStack construct, passing the current scope,
          a construct id, the environment, and the props.

        """

        super().__init__(scope, construct_id, env=env, **kwargs)

        NotificationsStack(
            self,
            construct_id="notifications-stack",
            env=env,
            props=props,
        )
