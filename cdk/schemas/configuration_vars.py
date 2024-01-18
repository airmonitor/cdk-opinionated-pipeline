"""Validate variables against pydantic models."""

from typing import Literal

from pydantic import BaseModel, EmailStr, PositiveFloat, constr


class Observability(BaseModel):
    """Defines the Observability model.

    Parameters:
      - None

    Attributes:

      - LOG_LEVEL (Literal["DEBUG", "INFO", "ERROR", "CRITICAL", "WARNING", "EXCEPTION"]):
        The log level to use.

      - LOG_SAMPLING_RATE (PositiveFloat):
        The log sampling rate.

    Functionality:

      - Defines a Pydantic model for observability configuration.
      - Constrains LOG_LEVEL to a set of literal string values.
      - Constrains LOG_SAMPLING_RATE to be a positive float.
    """

    LOG_LEVEL: Literal["DEBUG", "INFO", "ERROR", "CRITICAL", "WARNING", "EXCEPTION"]
    LOG_SAMPLING_RATE: PositiveFloat


class PipelinePluginsVars(BaseModel):
    """Defines the PipelinePluginsVars model.

    Parameters:
      - None

    Attributes:

      - pipeline_trigger (bool | None): Whether to enable the pipeline trigger plugin.
      optional.

      - pipeline_trigger_ssm_parameters (list | None): List of SSM parameters to trigger the pipeline.
      optional.

    Functionality:

      - defines a Pydantic model for pipeline plugins configuration.
      - pipeline_trigger enables/disables the pipeline trigger plugin.
      - pipeline_trigger_ssm_parameters configures SSM parameters that will trigger the pipeline when changed.
      - all attributes are optional.
    """

    pipeline_trigger: bool | None = None
    pipeline_trigger_ssm_parameters: list | None = None


class PipelineVars(BaseModel):
    """Defines the PipelineVars model.

    Parameters:
      - None

    Attributes:

      - aws_region (Literal["eu-central-1", "us-west-2"]): The AWS region to deploy to.

      - aws_account (constr): The AWS account ID. Constrained to 12 characters.

      - project (str): The name of the project.

      - repository (constr): The name of the Git repository.
      constrained between 3 and 255 characters.

      - ci_cd_notification_email (EmailStr): The email address to send CI/CD notifications to.

      - slack_ci_cd_channel_id (constr | None): Optional Slack channel ID for CI/CD notifications.
      constrained to 11 characters.

      - plugins (PipelinePluginsVars): Configuration for pipeline plugins.

    Functionality:

      - defines a Pydantic model for general pipeline configuration.
      - Constrains attributes with validations where applicable.
      - plugin attribute holds config for pipeline plugins.
    """

    aws_region: Literal["eu-central-1", "us-west-2"]
    aws_account: constr(min_length=12, max_length=12)  # type: ignore
    project: str
    repository: constr(min_length=3, max_length=255)  # type: ignore
    ci_cd_notification_email: EmailStr
    slack_ci_cd_channel_id: constr(min_length=0, max_length=11) | None = None  # type: ignore

    plugins: PipelinePluginsVars


class ConfigurationVars(PipelineVars):
    """Defines the ConfigurationVars model.

    Parameters:
      - None

    Attributes:

      - stage (Literal["dev", "ppe", "prod"]): The deployment stage.
      constrained to "dev", "ppe", or "prod".

      - alarm_emails (list[EmailStr]): A list of emails to receive alarm notifications.

    Functionality:

      - extends the PipelineVars model with additional configuration attributes.
      - Constrains stage to a predefined set of options.
      - Allows configuring multiple alarm notification emails.
    """

    stage: Literal["dev", "ppe", "prod"]
    alarm_emails: list[EmailStr]


class NotificationVars(BaseModel):
    """Defines the NotificationVars model.

    Parameters:
      - None

    Attributes:

      - slack_channel_id_alarms (constr | None): Optional Slack channel for alarm notifications.
      constrained to 11 characters.

      - slack_channel_id (constr | None): Optional Slack channel for general notifications.
      constrained to 11 characters.

      - slack_workspace_id (constr): Required Slack workspace ID. Constrained to 11 characters.

    Functionality:

      - defines a Pydantic model for notification configuration.
      - Allows configuring different Slack channels for alarms and general notifications.
      - slack_workspace_id is required.
      other attributes are optional.
    """

    slack_channel_id_alarms: constr(min_length=0, max_length=11) | None = None  # type: ignore
    slack_channel_id: constr(min_length=0, max_length=11) | None = None  # type: ignore
    slack_workspace_id: constr(min_length=0, max_length=11)  # type: ignore
