"""Validated action requests for the AEGIS security gateway."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ActionRequest(BaseModel):
    """Structured request proposed by an AI agent."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    action: Literal[
        "read_document",
        "search_documents",
        "send_email",
    ]
    provenance_context_id: str | None = Field(
    default=None,
    min_length=1,
    max_length=100,
    )

    agent_id: str = Field(min_length=1, max_length=100)

    resource: str = Field(min_length=1, max_length=255)

    destination: str | None = Field(default=None, max_length=254)

    content: str | None = Field(default=None, max_length=10000)

    @field_validator("agent_id", "resource")
    @classmethod
    def reject_empty_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty or whitespace")
        return value

    @field_validator("destination")
    @classmethod
    def validate_destination(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Destination cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_email_fields(self):
        if self.action == "send_email":
            if not self.destination:
                raise ValueError("Email destination is required")

            if "@" not in self.destination:
                raise ValueError("Invalid email destination")

            if not self.content:
                raise ValueError("Email content is required")

        return self