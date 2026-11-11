"""Validated models and shared constants for DevControl."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

TaskStatus = Literal["todo", "in_progress", "blocked", "review", "done", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "urgent"]
TestStatus = Literal["passed", "failed", "error", "skipped"]

TASK_STATUSES: tuple[str, ...] = (
    "todo",
    "in_progress",
    "blocked",
    "review",
    "done",
    "cancelled",
)
TASK_PRIORITIES: tuple[str, ...] = ("low", "medium", "high", "urgent")
TEST_STATUSES: tuple[str, ...] = ("passed", "failed", "error", "skipped")


class ToolError(BaseModel):
    """Machine-readable error details."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ToolResponse(BaseModel):
    """Consistent success/failure envelope returned by every tool."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    data: dict[str, Any] | None = None
    error: ToolError | None = None

    @model_validator(mode="after")
    def validate_envelope(self) -> "ToolResponse":
        if self.ok and self.data is None:
            raise ValueError("data is required when ok is true")
        if self.ok and self.error is not None:
            raise ValueError("error must be null when ok is true")
        if not self.ok and self.error is None:
            raise ValueError("error is required when ok is false")
        if not self.ok and self.data is not None:
            raise ValueError("data must be null when ok is false")
        return self

    @classmethod
    def success(cls, data: dict[str, Any]) -> "ToolResponse":
        return cls(ok=True, data=data)

    @classmethod
    def failure(cls, code: str, message: str) -> "ToolResponse":
        return cls(ok=False, error=ToolError(code=code, message=message))
