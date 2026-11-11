
"""Provenance and trust metadata for information handled by AEGIS."""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class SourceType(StrEnum):
    USER_INPUT = "USER_INPUT"
    DOCUMENT = "DOCUMENT"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    AGENT_GENERATED = "AGENT_GENERATED"
    EXTERNAL = "EXTERNAL"


class TrustLevel(StrEnum):
    UNTRUSTED = "UNTRUSTED"
    REVIEWED = "REVIEWED"
    TRUSTED = "TRUSTED"


class SensitivityLevel(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"


class Provenance(BaseModel):
    """Records the origin and security context of information."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    source_id: str = Field(min_length=1, max_length=150)
    source_type: SourceType
    origin: str = Field(min_length=1, max_length=500)

    trust_level: TrustLevel = TrustLevel.UNTRUSTED
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL

    parent_source_ids: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=50,
    )

    contains_untrusted_instructions: bool = True

    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("parent_source_ids")
    @classmethod
    def validate_parent_sources(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)

        if any(not value for value in cleaned):
            raise ValueError("Parent source IDs cannot be empty")

        if len(cleaned) != len(set(cleaned)):
            raise ValueError("Duplicate parent source IDs are not allowed")

        return cleaned

    @model_validator(mode="after")
    def validate_lineage(self):
        if self.source_id in self.parent_source_ids:
            raise ValueError("A source cannot be its own parent")

        return self
