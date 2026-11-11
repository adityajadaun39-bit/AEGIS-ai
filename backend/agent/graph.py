
"""Deterministic LangGraph agent connected to the AEGIS gateway."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.schemas.actions import ActionRequest
from backend.schemas.provenance import Provenance
from backend.security.authorization import AGENT_REGISTRY
from backend.security.gateway import execute_action
from backend.tools.simulated_tools import DOCUMENTS


class AgentState(TypedDict):
    action: str
    agent_id: str
    resource: str
    destination: str | None
    content: str | None
    approval_id: str | None
    proposed_action: dict | None
    source_provenance: list[dict]
    output_provenance: list[dict]
    gateway_result: dict | None
    provenance_context_id: str | None


def collect_provenance(state: AgentState) -> dict:
    """Collect provenance only from accessible resources."""

    provenance_records = []
    permissions = AGENT_REGISTRY.get(state["agent_id"])

    if permissions is None:
        return {"source_provenance": []}

    if state["action"] not in permissions.allowed_actions:
        return {"source_provenance": []}

    if state["action"] == "read_document":
        resource = state["resource"]

        if resource in permissions.allowed_resources:
            document = DOCUMENTS.get(resource)

            if document is not None:
                provenance_records.append(
                    document["provenance"].model_dump(mode="json")
                )

    elif state["action"] == "search_documents":
        query = state["resource"].casefold()

        for name in sorted(permissions.allowed_resources):
            if query in name.casefold():
                document = DOCUMENTS.get(name)

                if document is not None:
                    provenance_records.append(
                        document["provenance"].model_dump(mode="json")
                    )

    return {"source_provenance": provenance_records}


def propose_action(state: AgentState) -> dict:
    """Validate and prepare an action proposal."""

    request = ActionRequest(
        action=state["action"],
        agent_id=state["agent_id"],
        resource=state["resource"],
        destination=state["destination"],
        content=state["content"],
        provenance_context_id=state["provenance_context_id"],
    )

    return {"proposed_action": request.model_dump(mode="json")}


def propagate_provenance(state: AgentState) -> dict:
    """Preserve source lineage in generated output metadata."""

    output_records = []

    for source in state["source_provenance"]:
        verified_source = Provenance.model_validate(source)

        output = Provenance(
            source_id=f"agent-output-{verified_source.source_id}",
            source_type="AGENT_GENERATED",
            origin="AEGIS deterministic agent",
            trust_level=verified_source.trust_level,
            sensitivity=verified_source.sensitivity,
            parent_source_ids=(verified_source.source_id,),
            contains_untrusted_instructions=(
                verified_source.contains_untrusted_instructions
            ),
        )

        output_records.append(output.model_dump(mode="json"))

    return {"output_provenance": output_records}


def gateway_check(state: AgentState) -> dict:
    """Send the proposed action through the central security gateway."""

    request = ActionRequest.model_validate(state["proposed_action"])

    result = execute_action(
        request,
        approval_id=state["approval_id"],
    )

    return {"gateway_result": result}


def finalize_result(state: AgentState) -> dict:
    """Prepare the final agent response."""

    return {
        "gateway_result": state["gateway_result"],
    }


def build_agent_graph():
    """Build and compile the complete agent workflow."""

    workflow = StateGraph(AgentState)

    workflow.add_node("collect_provenance", collect_provenance)
    workflow.add_node("propose_action", propose_action)
    workflow.add_node("propagate_provenance", propagate_provenance)
    workflow.add_node("gateway_check", gateway_check)
    workflow.add_node("finalize_result", finalize_result)

    workflow.add_edge(START, "collect_provenance")
    workflow.add_edge("collect_provenance", "propose_action")
    workflow.add_edge("propose_action", "propagate_provenance")
    workflow.add_edge("propagate_provenance", "gateway_check")
    workflow.add_edge("gateway_check", "finalize_result")
    workflow.add_edge("finalize_result", END)

    return workflow.compile()


agent = build_agent_graph()


def run_agent(
    action: str,
    agent_id: str,
    resource: str,
    destination: str | None = None,
    content: str | None = None,
    provenance_context_id: str | None = None,
    approval_id: str | None = None,
) -> dict:
    """Run the agent and return its proposal, provenance and gateway decision."""

    initial_state: AgentState = {
        "action": action,
        "agent_id": agent_id,
        "resource": resource,
        "destination": destination,
        "content": content,
        "approval_id": approval_id,
        "provenance_context_id": provenance_context_id,
        "proposed_action": None,
        "source_provenance": [],
        "output_provenance": [],
        "gateway_result": None,
    }

    result = agent.invoke(initial_state)

    return {
        "proposed_action": result["proposed_action"],
        "source_provenance": result["source_provenance"],
        "output_provenance": result["output_provenance"],
        "gateway_result": result["gateway_result"],
    }
