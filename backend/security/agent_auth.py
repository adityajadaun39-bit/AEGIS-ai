
"""Agent authentication for external AEGIS API requests."""

import hmac
import os

AGENT_TOKEN_ENV = {
    "research_agent": "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
    "supervised_research_agent": (
        "AEGIS_AGENT_TOKEN_SUPERVISED_RESEARCH_AGENT"
    ),
}


def authenticate_agent(token: str | None) -> str | None:
    """Return the authenticated agent ID, or None if invalid."""

    if not token:
        return None

    matched_agents = []

    for agent_id, env_name in AGENT_TOKEN_ENV.items():
        expected_token = os.getenv(env_name)

        if expected_token and hmac.compare_digest(
            token,
            expected_token,
        ):
            matched_agents.append(agent_id)

    # Reject ambiguous credentials rather than guessing an identity.
    if len(matched_agents) != 1:
        return None

    return matched_agents[0]
