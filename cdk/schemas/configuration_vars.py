# -*- coding: utf-8 -*-
"""Validate variables against pydantic models."""
from typing import Literal, Optional

from pydantic import BaseModel, constr, PositiveFloat, EmailStr


class Observability(BaseModel):
    """Observability variables."""

    LOG_LEVEL: Literal["DEBUG", "INFO", "ERROR", "CRITICAL", "WARNING", "EXCEPTION"]
    LOG_SAMPLING_RATE: PositiveFloat


class PipelinePluginsVars(BaseModel):
    """Pipeline plugins variables."""

    pipeline_trigger: Optional[bool]
    pipeline_trigger_ssm_parameters: Optional[list]


class PipelineVars(BaseModel):
    """CI/CD variables.."""

    aws_region: Literal["eu-central-1", "us-west-2"]
    aws_account: constr(min_length=12, max_length=12)  # type: ignore
    project: str
    repository: constr(min_length=3, max_length=255)  # type: ignore
    ci_cd_notification_email: EmailStr
    slack_ci_cd_channel_id: Optional[constr(min_length=0, max_length=11)]  # type: ignore

    plugins: PipelinePluginsVars


class ConfigurationVars(PipelineVars):
    """Notification details, including email, slack, etc."""

    stage: Literal["dev", "ppe", "prod"]
    alarm_emails: list[EmailStr]


class NotificationVars(BaseModel):
    """Notification details, including email, slack, etc."""

    slack_channel_id_alarms: Optional[constr(min_length=0, max_length=11)]  # type: ignore
    slack_channel_id: Optional[constr(min_length=0, max_length=11)]  # type: ignore
    slack_workspace_id: constr(min_length=0, max_length=11)  # type: ignore
