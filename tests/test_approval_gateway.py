
from unittest.mock import patch

import pytest

from backend.schemas.actions import ActionRequest
from backend.schemas.approval import ApprovalStatus
from backend.security import approval_engine, approval_store
from backend.security.gateway import execute_action
from unittest.mock import patch

from backend.schemas.actions import ActionRequest
from backend.security.gateway import execute_action

from backend.schemas.provenance import (
    Provenance,
    SourceType,
    TrustLevel,
    SensitivityLevel,
)

SAFE_PROVENANCE = Provenance(
    source_id="test-reviewed-001",
    source_type=SourceType.USER_INPUT,
    origin="reviewed_test_fixture",
    trust_level=TrustLevel.REVIEWED,
    sensitivity=SensitivityLevel.INTERNAL,
    contains_untrusted_instructions=False,
)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "gateway_approval_test.db",
    )
    monkeypatch.setenv("AEGIS_APPROVER_TOKEN", "test-secret-token")


def make_request(content="Approved research summary"):
    return ActionRequest(
        action="send_email",
        agent_id="supervised_research_agent",
        resource="email",
        destination="review@example.com",
        content=content,
    )


def create_approved_request(request):
    approval = approval_engine.create_approval(request)

    approval_engine.review_approval(
        approval.approval_id,
        "APPROVE",
        "demo_reviewer",
        "test-secret-token",
    )

    return approval


@patch(
    "backend.security.gateway.evaluate_policy",
    return_value=(True, "OPA allowed"),
)
@patch(
    "backend.security.gateway.resolve_provenance_context",
    return_value=[SAFE_PROVENANCE],
)
@patch(
    "backend.security.gateway.evaluate_policy",
    return_value=(True, "OPA allowed"),
)
def test_email_requires_approval(
    mock_policy,
    mock_provenance,
    isolated_db,
):
    request = make_request().model_copy(
        update={"provenance_context_id": "test-safe-context"}
    )

    response = execute_action(request)

    assert response["decision"] == "REQUIRES_APPROVAL"
@patch("backend.security.gateway.resolve_provenance_context")
@patch("backend.security.gateway.tool_broker.execute")
@patch(
    "backend.security.gateway.evaluate_policy",
    return_value=(True, "OPA allowed"),
)
def test_approved_email_executes_once(
    mock_policy,
    mock_execute,
    mock_provenance,
    isolated_db,
):
    mock_provenance.return_value = [SAFE_PROVENANCE]

    request = make_request().model_copy(
        update={"provenance_context_id": "test-safe-context"}
    )

    approval = create_approved_request(request)

    mock_execute.return_value = {
        "success": True,
        "message": "Simulated email sent",
    }

    response = execute_action(
        request,
        approval_id=approval.approval_id,
    )

    assert response["success"] is True
    assert response["decision"] == "ALLOW"
    mock_execute.assert_called_once()
    
@patch("backend.security.gateway.resolve_provenance_context")
@patch("backend.security.gateway.tool_broker.execute")
@patch(
    "backend.security.gateway.evaluate_policy",
    return_value=(True, "OPA allowed"),
)
def test_modified_email_payload_is_denied(
    mock_policy,
    mock_execute,
    mock_provenance,
    isolated_db,
):
    mock_provenance.return_value = [SAFE_PROVENANCE]

    request = make_request().model_copy(
        update={"provenance_context_id": "test-safe-context"}
    )

    approval = create_approved_request(request)

    modified_request = request.model_copy(
        update={"content": "Modified email content"}
    )

    response = execute_action(
        modified_request,
        approval_id=approval.approval_id,
    )

    assert response["success"] is False
    assert response["decision"] == "DENY"
    mock_execute.assert_not_called()
def test_original_research_agent_email_remains_denied(isolated_db):
    request = ActionRequest(
        action="send_email",
        agent_id="research_agent",
        resource="email",
        destination="attacker@example.com",
        content="Attempted unauthorized email",
    )

    response = execute_action(request)

    assert response["success"] is False
    assert response["decision"] == "DENY"