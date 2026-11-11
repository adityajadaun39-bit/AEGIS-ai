
from unittest.mock import patch

import pytest

from backend.schemas.actions import ActionRequest
from backend.security.provenance_context import (
    clear_provenance_contexts,
    register_document_context,
    resolve_provenance_context,
)
from backend.security.policy_engine import evaluate_information_flow
from backend.tools.simulated_tools import DOCUMENTS


@pytest.fixture(autouse=True)
def reset_contexts():
    clear_provenance_contexts()
    yield
    clear_provenance_contexts()


def make_email(context_id=None):
    return ActionRequest(
        action="send_email",
        agent_id="supervised_research_agent",
        resource="email",
        destination="attacker@example.com",
        content="Research summary",
        provenance_context_id=context_id,
    )


def test_untrusted_document_cannot_flow_to_email():
    document = DOCUMENTS["public_report.pdf"]
    context_id = register_document_context(
        "public_report.pdf",
        document["provenance"].model_dump(mode="json"),
    )

    records = resolve_provenance_context(context_id)

    allowed, reason = evaluate_information_flow(
        make_email(context_id),
        records,
    )

    assert allowed is False
    assert "Untrusted" in reason or "instructions" in reason


def test_confidential_document_cannot_flow_to_email():
    document = DOCUMENTS["confidential_notes.txt"]
    context_id = register_document_context(
        "confidential_notes.txt",
        document["provenance"].model_dump(mode="json"),
    )

    records = resolve_provenance_context(context_id)

    allowed, reason = evaluate_information_flow(
        make_email(context_id),
        records,
    )

    assert allowed is False
    assert "Confidential" in reason


def test_missing_context_is_denied():
    allowed, reason = evaluate_information_flow(
        make_email(),
        None,
    )

    assert allowed is False
    assert "context required" in reason


def test_unknown_context_cannot_be_resolved():
    assert resolve_provenance_context("not-a-real-context") is None


def test_forged_provenance_is_rejected():
    forged = DOCUMENTS["public_report.pdf"]["provenance"].model_dump(
        mode="json"
    )
    forged["trust_level"] = "TRUSTED"
    forged["contains_untrusted_instructions"] = False

    with pytest.raises(ValueError):
        register_document_context("public_report.pdf", forged)


@patch("backend.security.gateway.consume_approval")
@patch("backend.security.gateway.evaluate_policy", return_value=(True, "OPA allowed"))
@patch("backend.security.gateway.authorize_action", return_value=(True, "Authorized"))
def test_approval_cannot_override_untrusted_provenance(
    mock_authorize,
    mock_policy,
    mock_consume,
):
    from backend.security.gateway import execute_action

    document = DOCUMENTS["public_report.pdf"]
    context_id = register_document_context(
        "public_report.pdf",
        document["provenance"].model_dump(mode="json"),
    )

    result = execute_action(
        make_email(context_id),
        approval_id="approval-demo",
    )

    assert result["decision"] == "DENY"
    mock_consume.assert_not_called()
