
from datetime import datetime, timedelta, timezone

import pytest

from backend.schemas.actions import ActionRequest
from backend.schemas.approval import ApprovalRequest, ApprovalStatus
from backend.security import approval_engine, approval_store


def make_request(content="Research summary"):
    return ActionRequest(
        action="send_email",
        agent_id="research_agent",
        resource="email",
        destination="review@example.com",
        content=content,
    )


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "approval_test.db",
    )
    monkeypatch.setenv("AEGIS_APPROVER_TOKEN", "test-secret-token")


def test_create_approval_binds_exact_payload(isolated_db):
    request = make_request()
    approval = approval_engine.create_approval(request)

    assert approval.status == ApprovalStatus.PENDING
    assert approval.agent_id == request.agent_id
    assert approval.payload_hash == approval_engine.calculate_payload_hash(request)
    assert approval.expires_at > approval.created_at


def test_invalid_ttl_is_rejected(isolated_db):
    with pytest.raises(ValueError):
        approval_engine.create_approval(make_request(), ttl_minutes=0)


def test_review_requires_valid_token(isolated_db):
    approval = approval_engine.create_approval(make_request())

    with pytest.raises(PermissionError):
        approval_engine.review_approval(
            approval.approval_id,
            "APPROVE",
            "demo_reviewer",
            "wrong-token",
        )


def test_review_approves_pending_request(isolated_db):
    approval = approval_engine.create_approval(make_request())

    result = approval_engine.review_approval(
        approval.approval_id,
        "APPROVE",
        "demo_reviewer",
        "test-secret-token",
    )

    assert result is True
    assert approval_store.get_approval(
        approval.approval_id
    ).status == ApprovalStatus.APPROVED


def test_rejected_request_cannot_be_consumed(isolated_db):
    request = make_request()
    approval = approval_engine.create_approval(request)

    approval_engine.review_approval(
        approval.approval_id,
        "REJECT",
        "demo_reviewer",
        "test-secret-token",
    )

    assert approval_engine.consume_approval(
        approval.approval_id,
        request,
    ) is False


def test_modified_payload_cannot_use_approval(isolated_db):
    original_request = make_request()
    approval = approval_engine.create_approval(original_request)

    approval_engine.review_approval(
        approval.approval_id,
        "APPROVE",
        "demo_reviewer",
        "test-secret-token",
    )

    modified_request = make_request(content="Changed email content")

    assert approval_engine.consume_approval(
        approval.approval_id,
        modified_request,
    ) is False


def test_approved_request_can_be_consumed_only_once(isolated_db):
    request = make_request()
    approval = approval_engine.create_approval(request)

    approval_engine.review_approval(
        approval.approval_id,
        "APPROVE",
        "demo_reviewer",
        "test-secret-token",
    )

    assert approval_engine.consume_approval(
        approval.approval_id,
        request,
    ) is True

    assert approval_engine.consume_approval(
        approval.approval_id,
        request,
    ) is False

    stored = approval_store.get_approval(approval.approval_id)
    assert stored.status == ApprovalStatus.CONSUMED


def test_missing_reviewer_configuration_fails_closed(
    isolated_db,
    monkeypatch,
):
    approval = approval_engine.create_approval(make_request())
    monkeypatch.delenv("AEGIS_APPROVER_TOKEN")

    with pytest.raises(PermissionError):
        approval_engine.review_approval(
            approval.approval_id,
            "APPROVE",
            "demo_reviewer",
            "test-secret-token",
        )
        if decision not in ("APPROVE", "REJECT"):
            raise ValueError("Decision must be APPROVE or REJECT")


def test_expired_pending_approval_cannot_be_approved(
    isolated_db,
    monkeypatch,
):
    approval = approval_engine.create_approval(make_request())

    monkeypatch.setattr(
        ApprovalRequest,
        "is_expired",
        property(lambda self: True),
    )

    result = approval_engine.review_approval(
        approval.approval_id,
        "APPROVE",
        "demo_reviewer",
        "test-secret-token",
    )

    assert result is False
    assert approval_store.get_approval(
        approval.approval_id
    ).status == ApprovalStatus.EXPIRED


def test_expired_approved_approval_cannot_be_consumed(
    isolated_db,
    monkeypatch,
):
    request = make_request()
    approval = approval_engine.create_approval(request)

    approval_engine.review_approval(
        approval.approval_id,
        "APPROVE",
        "demo_reviewer",
        "test-secret-token",
    )

    monkeypatch.setattr(
        ApprovalRequest,
        "is_expired",
        property(lambda self: True),
    )

    result = approval_engine.consume_approval(
        approval.approval_id,
        request,
    )

    assert result is False
    assert approval_store.get_approval(
        approval.approval_id
    ).status == ApprovalStatus.EXPIRED
