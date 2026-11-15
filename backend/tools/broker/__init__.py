
"""Controlled tool execution broker for AEGIS."""

from collections.abc import Callable

from backend.tools.simulated_tools import (
    read_document,
    search_documents,
    send_email,
)


class ToolBroker:
    """Executes only explicitly registered tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {
            "read_document": read_document,
            "search_documents": search_documents,
            "send_email": send_email,
        }

    def execute(
        self,
        action: str,
        resource: str,
        *,
        allowed_resources: frozenset[str] = frozenset(),
        destination: str | None = None,
        content: str | None = None,
    ) -> dict:
        """Execute a registered tool with controlled arguments."""

        tool = self._tools.get(action)

        if tool is None:
            return {
                "success": False,
                "error": "Tool is not registered",
            }

        if action == "read_document":
            if resource not in allowed_resources:
                return {
                    "success": False,
                    "error": "Resource not permitted by tool broker",
                }

            return tool(resource)

        if action == "search_documents":
            return tool(resource, allowed_resources)

        if action == "send_email":
            if not destination or not content:
                return {
                    "success": False,
                    "error": "Email destination and content are required",
                }

            return tool(destination, content)

        return {
            "success": False,
            "error": "Unsupported tool execution",
        }


tool_broker = ToolBroker()
