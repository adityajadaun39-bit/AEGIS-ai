from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_audit_rejects_missing_token():
    response = client.get("/audit")
    assert response.status_code == 403


def test_audit_rejects_agent_token(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_AGENT_TOKEN_RESEARCH_AGENT",
        "research-test-token",
    )

    response = client.get(
        "/audit",
        headers={
            "X-AEGIS-Agent-Token": "research-test-token"
        },
    )

    assert response.status_code == 403


def test_audit_rejects_reviewer_token(monkeypatch):
    monkeypatch.setenv(
        "AEGIS_APPROVER_TOKEN",
        "reviewer-test-token",
    )

    response = client.get(
        "/audit",
        headers={
            "X-AEGIS-Approver-Token": "reviewer-test-token"
        },
    )

    assert response.status_code == 403


@patch("backend.app.get_audit_logs", return_value=[])
def test_audit_accepts_admin_token(mock_logs, monkeypatch):
    monkeypatch.setenv(
        "AEGIS_ADMIN_TOKEN",
        "admin-test-token",
    )

    response = client.get(
        "/audit",
        headers={"X-AEGIS-Admin-Token": "admin-test-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"events": []}


def test_approvals_rejects_missing_token():
    response = client.get("/approvals")
    assert response.status_code == 403


@patch("backend.app.approval_store.list_approvals", return_value=[])
def test_approvals_accepts_reviewer_token(
    mock_list,
    monkeypatch,
):
    monkeypatch.setenv(
        "AEGIS_APPROVER_TOKEN",
        "reviewer-test-token",
    )

    response = client.get(
        "/approvals",
        headers={
            "X-AEGIS-Approver-Token": "reviewer-test-token"
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "approvals": [],
    }


@patch("backend.app.approval_store.list_approvals", return_value=[])
def test_approvals_accepts_admin_token(mock_list, monkeypatch):
    monkeypatch.setenv(
        "AEGIS_ADMIN_TOKEN",
        "admin-test-token",
    )

    response = client.get(
        "/approvals",
        headers={"X-AEGIS-Admin-Token": "admin-test-token"},
    )

    assert response.status_code == 200


@patch("backend.app.get_audit_trace", return_value=[{"id": 1}])
def test_execution_trace_accepts_admin(mock_trace, monkeypatch):
    monkeypatch.setenv("AEGIS_ADMIN_TOKEN", "admin-test-token")

    response = client.get(
        "/audit/traces/test-trace",
        headers={"X-AEGIS-Admin-Token": "admin-test-token"},
    )

    assert response.status_code == 200
    assert response.json()["trace_id"] == "test-trace"


def test_execution_trace_rejects_missing_token():
    response = client.get("/audit/traces/test-trace")
    assert response.status_code == 403


@patch("backend.app.get_attack_trace", return_value=[{"id": 1}])
def test_attack_trace_accepts_admin(mock_trace, monkeypatch):
    monkeypatch.setenv("AEGIS_ADMIN_TOKEN", "admin-test-token")

    response = client.get(
        "/audit/attacks/test-attack",
        headers={"X-AEGIS-Admin-Token": "admin-test-token"},
    )

    assert response.status_code == 200
    assert response.json()["attack_id"] == "test-attack"


def test_attack_trace_rejects_missing_token():
    response = client.get("/audit/attacks/test-attack")
    assert response.status_code == 403
