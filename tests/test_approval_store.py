
from datetime import datetime, timedelta, timezone

from backend.schemas.approval import ApprovalRequest, ApprovalStatus
from backend.security import approval_store


def make_approval(approval_id="approval-001"):
    now = datetime.now(timezone.utc)

    return ApprovalRequest(
        approval_id=approval_id,
        agent_id="research_agent",
        action="send_email",
        resource="email",
        payload_hash="a" * 64,
        expires_at=now + timedelta(minutes=10),
    )


def test_create_and_retrieve_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "test.db",
    )

    request = make_approval()

    assert approval_store.create_approval(request) is True

    stored = approval_store.get_approval("approval-001")

    assert stored is not None
    assert stored.agent_id == "research_agent"
    assert stored.status == ApprovalStatus.PENDING
    assert stored.payload_hash == "a" * 64


def test_duplicate_approval_id_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "test.db",
    )

    request = make_approval()

    assert approval_store.create_approval(request) is True
    assert approval_store.create_approval(request) is False


def test_unknown_approval_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "test.db",
    )

    assert approval_store.get_approval("unknown") is None


def test_pending_approval_can_be_approved(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "test.db",
    )

    approval_store.create_approval(make_approval())

    updated = approval_store.update_approval_status(
        "approval-001",
        ApprovalStatus.APPROVED,
    )

    assert updated is True

    stored = approval_store.get_approval("approval-001")
    assert stored.status == ApprovalStatus.APPROVED


def test_approved_request_cannot_be_approved_again(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "test.db",
    )

    approval_store.create_approval(make_approval())

    assert approval_store.update_approval_status(
        "approval-001",
        ApprovalStatus.APPROVED,
    ) is True

    assert approval_store.update_approval_status(
        "approval-001",
        ApprovalStatus.APPROVED,
    ) is False


def test_unknown_approval_cannot_be_updated(tmp_path, monkeypatch):
    monkeypatch.setattr(
        approval_store,
        "DB_PATH",
        tmp_path / "test.db",
    )

    assert approval_store.update_approval_status(
        "unknown",
        ApprovalStatus.APPROVED,
    ) is False
