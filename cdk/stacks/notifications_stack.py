"""Create AWS resources responsible for notifications.

Example sns alarm topic
"""
import yaml
from os import path, walk
import aws_cdk as cdk
import aws_cdk.aws_chatbot as chatbot
import aws_cdk.aws_iam as iam
import aws_cdk.aws_logs as logs
import aws_cdk.aws_sns_subscriptions as sns_subscriptions
import aws_cdk.aws_ssm as ssm
from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks, NagSuppressions, NagPackSuppression
from cdk_opinionated_constructs.sns import SNSTopic
from constructs import Construct

from cdk.schemas.configuration_vars import ConfigurationVars, NotificationVars


class NotificationsStack(cdk.Stack):
    """Service stack.

    Create notifications cloudformation stack.
    """

    def __init__(self, scope: Construct, construct_id: str, env: cdk.Environment, props: dict, **kwargs) -> None:
        """Initialize default parameters from AWS CDK and configuration file.

        :param scope: The AWS CDK parent class from which this class
            inherits
        :param construct_id: The name of CDK construct
        :param env: Tha AWS CDK Environment class which provides AWS
            Account ID and AWS Region
        :param props: The dictionary which contain configuration values
            loaded initially from /config/config-env.yaml
        :param kwargs:
        """
        super().__init__(scope, construct_id, env=env, **kwargs)
        config_vars = ConfigurationVars(**props)

        # pylint: disable=W0612
        props_env: dict[list, dict] = {}
        for dir_path, dir_names, files in walk(f"cdk/config/{config_vars.stage}", topdown=False):
            for file_name in files:
                with open(path.join(dir_path, file_name), encoding="utf-8") as f:
                    props_env |= yaml.safe_load(f)
                    props["slack_channel_id_alarms"] = props_env["slack_channel_id_alarms"]  # type: ignore

        notification_vars = NotificationVars(**props)

        sns_construct = SNSTopic(self, id="topic_construct")
        sns_topic = sns_construct.create_sns_topic(topic_name=f"{config_vars.project}-alarms", master_key=None)

        # grant cloudwatch permissions to publish to the topic
        sns_topic.add_to_resource_policy(
            statement=iam.PolicyStatement(
                sid="CloudWatchPolicy",
                actions=["sns:Publish"],
                resources=[sns_topic.topic_arn],
                principals=[iam.ServicePrincipal("cloudwatch.amazonaws.com")],
                effect=iam.Effect.ALLOW,
            )
        )

        ssm.StringParameter(
            self,
            id="sns_topic_ssm_param",
            string_value=sns_topic.topic_arn,
            parameter_name=f"/{config_vars.project}/topic/alarm/arn",
        )

        for email_address in config_vars.alarm_emails:
            sns_topic.add_subscription(
                topic_subscription=sns_subscriptions.EmailSubscription(email_address=email_address)
            )

        if notification_vars.slack_workspace_id and notification_vars.slack_channel_id_alarms:
            chatbot_iam_role = iam.Role(
                self,
                id="iam_role_chatbot",
                assumed_by=iam.ServicePrincipal(service="chatbot.amazonaws.com"),
                managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("ReadOnlyAccess")],
            )
            chatbot_iam_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "iam:*",
                        "s3:GetBucketPolicy",
                        "ssm:*",
                        "sts:*",
                        "kms:*",
                        "cognito-idp:GetSigningCertificate",
                        "ec2:GetPasswordData",
                        "ecr:GetAuthorizationToken",
                        "gamelift:RequestUploadCredentials",
                        "gamelift:GetInstanceAccess",
                        "lightsail:DownloadDefaultKeyPair",
                        "lightsail:GetInstanceAccessDetails",
                        "lightsail:GetKeyPair",
                        "lightsail:GetKeyPairs",
                        "redshift:GetClusterCredentials",
                        "storagegateway:DescribeChapCredentials",
                    ],
                    effect=iam.Effect.DENY,
                    resources=["*"],
                )
            )
            chatbot_iam_role.add_to_policy(
                iam.PolicyStatement(
                    actions=["cloudwatch:Describe*", "cloudwatch:Get*", "cloudwatch:List*"], resources=["*"]
                )
            )

            chatbot.SlackChannelConfiguration(
                self,
                "chatbot",
                slack_channel_configuration_name=f"{config_vars.stage}-{config_vars.project}",
                notification_topics=[sns_topic],
                slack_workspace_id=notification_vars.slack_workspace_id,
                slack_channel_id=notification_vars.slack_channel_id_alarms,
                log_retention=logs.RetentionDays.ONE_DAY,
                logging_level=chatbot.LoggingLevel.ERROR,
                role=chatbot_iam_role,
            )

        # Validate stack against AWS Solutions checklist
        NagSuppressions.add_stack_suppressions(self, self.nag_suppression())
        Aspects.of(self).add(AwsSolutionsChecks(log_ignores=True))

    @staticmethod
    def nag_suppression() -> list:
        """Create CFN-NAG suppression.

        :return:
        """
        return [
            NagPackSuppression(id="AwsSolutions-SNS2", reason="Notifications stack, doesn't require encryption"),
            NagPackSuppression(id="AwsSolutions-IAM4", reason="Wildcard permissions are used in Deny section"),
            NagPackSuppression(id="AwsSolutions-IAM5", reason="Wildcard permissions are used in Deny section"),
        ]
