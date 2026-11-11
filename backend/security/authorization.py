
"""Agent identity and permission checks for AEGIS."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPermissions:
    allowed_actions: frozenset[str]
    allowed_resources: frozenset[str]


AGENT_REGISTRY = {
    "research_agent": AgentPermissions(
        allowed_actions=frozenset({
            "read_document",
            "search_documents",
        }),
        allowed_resources=frozenset({"public_report.pdf"}),
    ),
    "supervised_research_agent": AgentPermissions(
        allowed_actions=frozenset({"send_email"}),
        allowed_resources=frozenset({"email"}),
    ),
}


def authorize_action(agent_id, action, resource):
    permissions = AGENT_REGISTRY.get(agent_id)

    if permissions is None:
        return False, "Unknown agent"

    if action not in permissions.allowed_actions:
        return False, "Action not permitted"

    if action == "read_document":
        if resource not in permissions.allowed_resources:
            return False, "Resource not permitted"

    elif action == "search_documents":
        if not resource.strip():
            return False, "Search query cannot be empty"

    elif action == "send_email":
        if resource != "email":
            return False, "Email resource not permitted"

    else:
        return False, "Unsupported action"

    return True, "Authorized"
