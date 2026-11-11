
"""Approval request models for AEGIS."""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CONSUMED = "CONSUMED"


class ApprovalRequest(BaseModel):
    """A human approval request bound to a specific action."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    approval_id: str = Field(min_length=1, max_length=100)
    agent_id: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=50)
    resource: str = Field(min_length=1, max_length=255)

    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    status: ApprovalStatus = ApprovalStatus.PENDING

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    expires_at: datetime

    @field_validator("created_at", "expires_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Datetime must include timezone information")

        return value

    @model_validator(mode="after")
    def validate_expiry(self):
        if self.expires_at <= self.created_at:
            raise ValueError("Expiry must be later than creation")

        return self

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at
