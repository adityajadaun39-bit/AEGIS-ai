
from unittest.mock import patch

import pytest

from backend.agent.graph import run_agent
from backend.schemas.actions import ActionRequest


@patch("backend.agent.graph.execute_action")
def test_agent_sends_proposal_to_gateway(mock_execute):
    mock_execute.return_value = {
        "success": True,
        "decision": "ALLOW",
        "result": {"message": "Document read"},
    }

    result = run_agent(
        action="read_document",
        agent_id="research_agent",
        resource="public_report.pdf",
    )

    mock_execute.assert_called_once()

    submitted_request = mock_execute.call_args.args[0]

    assert isinstance(submitted_request, ActionRequest)
    assert submitted_request.agent_id == "research_agent"
    assert submitted_request.resource == "public_report.pdf"

    assert result["gateway_result"]["decision"] == "ALLOW"


@patch("backend.agent.graph.execute_action")
def test_agent_returns_gateway_denial(mock_execute):
    mock_execute.return_value = {
        "success": False,
        "decision": "DENY",
        "reason": "Resource not permitted",
    }

    result = run_agent(
        action="read_document",
        agent_id="research_agent",
        resource="confidential_notes.txt",
    )

    assert result["gateway_result"]["decision"] == "DENY"


@patch("backend.agent.graph.execute_action")
def test_agent_returns_approval_required(mock_execute):
    mock_execute.return_value = {
        "success": False,
        "decision": "REQUIRES_APPROVAL",
        "reason": "Human approval required",
    }

    result = run_agent(
        action="send_email",
        agent_id="supervised_research_agent",
        resource="email",
        destination="review@example.com",
        content="Research summary",
    )

    assert result["gateway_result"]["decision"] == "REQUIRES_APPROVAL"


@patch("backend.agent.graph.execute_action")
def test_agent_forwards_approval_id(mock_execute):
    mock_execute.return_value = {
        "success": True,
        "decision": "ALLOW",
        "result": {"message": "Simulated email sent"},
    }

    run_agent(
        action="send_email",
        agent_id="supervised_research_agent",
        resource="email",
        destination="review@example.com",
        content="Research summary",
        approval_id="approval-demo-001",
    )

    assert mock_execute.call_args.kwargs["approval_id"] == "approval-demo-001"


def test_agent_preserves_document_provenance():
    with patch(
        "backend.agent.graph.execute_action",
        return_value={"success": True, "decision": "ALLOW"},
    ):
        result = run_agent(
            action="read_document",
            agent_id="research_agent",
            resource="public_report.pdf",
        )

    assert len(result["source_provenance"]) == 1
    assert len(result["output_provenance"]) == 1

    output = result["output_provenance"][0]

    assert output["source_type"] == "AGENT_GENERATED"
    assert output["parent_source_ids"] == [
        result["source_provenance"][0]["source_id"]
    ]


def test_agent_rejects_invalid_action():
    with pytest.raises(ValueError):
        run_agent(
            action="delete_database",
            agent_id="research_agent",
            resource="database",
        )
