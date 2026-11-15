
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.security.agent_auth import authenticate_agent

client = TestClient(app)


def test_research_agent_token_authenticates(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
        "research-test-token",
    )

    assert authenticate_agent("research-test-token") == "research_agent"


def test_supervised_agent_token_authenticates(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_SUPERVISED_RESEARCH_AGENT",
        "supervised-test-token",
    )

    assert (
        authenticate_agent("supervised-test-token")
        == "supervised_research_agent"
    )


def test_invalid_token_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
        "research-test-token",
    )

    assert authenticate_agent("wrong-token") is None


def test_duplicate_agent_tokens_fail_closed(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
        "shared-test-token",
    )
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_SUPERVISED_RESEARCH_AGENT",
        "shared-test-token",
    )

    assert authenticate_agent("shared-test-token") is None


def test_api_rejects_missing_agent_token():
    response = client.post(
        "/actions",
        json={
            "action": "read_document",
            "agent_id": "research_agent",
            "resource": "public_report.pdf",
        },
    )

    assert response.status_code == 403


def test_api_rejects_invalid_agent_token(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
        "research-test-token",
    )

    response = client.post(
        "/actions",
        headers={"X-AEGIS-Agent-Token": "wrong-token"},
        json={
            "action": "read_document",
            "agent_id": "research_agent",
            "resource": "public_report.pdf",
        },
    )

    assert response.status_code == 403


def test_api_rejects_agent_impersonation(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
        "research-test-token",
    )
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_SUPERVISED_RESEARCH_AGENT",
        "supervised-test-token",
    )

    response = client.post(
        "/actions",
        headers={
            "X-AEGIS-Agent-Token": "research-test-token",
        },
        json={
            "action": "send_email",
            "agent_id": "supervised_research_agent",
            "resource": "email",
            "destination": "test@example.com",
            "content": "Impersonation test",
        },
    )

    assert response.status_code == 403
    assert "does not match" in response.json()["detail"]


def test_valid_agent_token_reaches_gateway(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
        "research-test-token",
    )

    expected_response = {
        "success": True,
        "decision": "ALLOW",
    }

    with patch(
        "backend.app.execute_action",
        return_value=expected_response,
    ) as mock_execute:
        response = client.post(
            "/actions",
            headers={
                "X-AEGIS-Agent-Token": "research-test-token",
            },
            json={
                "action": "read_document",
                "agent_id": "research_agent",
                "resource": "public_report.pdf",
            },
        )

    assert response.status_code == 200
    assert response.json() == expected_response
    mock_execute.assert_called_once()
