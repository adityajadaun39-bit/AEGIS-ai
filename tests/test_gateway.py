
from backend.schemas.actions import ActionRequest
from backend.security.gateway import execute_action


def test_public_document_is_allowed():
    request = ActionRequest(
        action="read_document",
        agent_id="research_agent",
        resource="public_report.pdf",
    )

    result = execute_action(request)

    assert result["decision"] == "ALLOW"
    assert result["result"]["success"] is True


def test_confidential_document_is_denied():
    request = ActionRequest(
        action="read_document",
        agent_id="research_agent",
        resource="confidential_notes.txt",
    )

    result = execute_action(request)

    assert result["decision"] == "DENY"
    assert result["reason"] == "Resource not permitted"


def test_email_sending_is_denied():
    request = ActionRequest(
        action="send_email",
        agent_id="research_agent",
        resource="email",
        destination="demo@example.com",
        content="Test",
    )

    result = execute_action(request)

    assert result["decision"] == "DENY"


def test_search_does_not_reveal_confidential_documents():
    request = ActionRequest(
        action="search_documents",
        agent_id="research_agent",
        resource=".txt",
    )

    result = execute_action(request)

    assert result["decision"] == "ALLOW"
    assert "confidential_notes.txt" not in result["result"]["matches"]

from unittest.mock import patch


def test_opa_denial_prevents_tool_execution():
    request = ActionRequest(
        action="read_document",
        agent_id="research_agent",
        resource="public_report.pdf",
    )

    with patch(
        "backend.security.gateway.evaluate_policy",
        return_value=(False, "Simulated OPA denial"),
    ):
        with patch(
            "backend.security.gateway.tool_broker.execute"
        ) as mock_execute:
            result = execute_action(request)

    assert result["decision"] == "DENY"
    assert result["success"] is False
    mock_execute.assert_not_called()


def test_tool_failure_is_handled_safely():
    request = ActionRequest(
        action="read_document",
        agent_id="research_agent",
        resource="public_report.pdf",
    )

    with patch(
        "backend.security.gateway.tool_broker.execute",
        side_effect=RuntimeError("Simulated tool crash"),
    ):
        result = execute_action(request)

    assert result["decision"] == "ERROR"
    assert result["success"] is False
    assert result["reason"] == "Tool execution failed"


def test_broker_error_result_is_not_reported_as_success():
    request = ActionRequest(
        action="read_document",
        agent_id="research_agent",
        resource="public_report.pdf",
    )

    with patch(
        "backend.security.gateway.tool_broker.execute",
        return_value={
            "success": False,
            "error": "Simulated document failure",
        },
    ):
        result = execute_action(request)

    assert result["decision"] == "ERROR"
    assert result["success"] is False
