
"""Human approval lifecycle for AEGIS."""

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from backend.schemas.actions import ActionRequest
from backend.schemas.approval import ApprovalRequest, ApprovalStatus
from backend.security import approval_store


def calculate_payload_hash(request: ActionRequest) -> str:
    """Create a stable SHA-256 hash of the complete action request."""

    canonical_payload = json.dumps(
        request.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(canonical_payload).hexdigest()


def create_approval(
    request: ActionRequest,
    ttl_minutes: int = 10,
) -> ApprovalRequest:
    """Create a pending approval bound to an exact action payload."""

    if not 1 <= ttl_minutes <= 60:
        raise ValueError("Approval TTL must be between 1 and 60 minutes")

    now = datetime.now(timezone.utc)

    approval = ApprovalRequest(
        approval_id=str(uuid.uuid4()),
        agent_id=request.agent_id,
        action=request.action,
        resource=request.resource,
        payload_hash=calculate_payload_hash(request),
        status=ApprovalStatus.PENDING,
        created_at=now,
        expires_at=now + timedelta(minutes=ttl_minutes),
    )

    if not approval_store.create_approval(approval):
        raise RuntimeError("Could not create approval request")

    return approval


def review_approval(
    approval_id: str,
    decision: Literal["APPROVE", "REJECT"],
    reviewer_id: str,
    reviewer_token: str,
) -> bool:
    """Record a human decision after verifying reviewer credentials."""

    expected_token = os.getenv("AEGIS_APPROVER_TOKEN")

    if not expected_token:
        raise PermissionError("Human approval is not configured")

    if not reviewer_id.strip() or not hmac.compare_digest(
        reviewer_token,
        expected_token,
    ):
        raise PermissionError("Reviewer authentication failed")

    approval = approval_store.get_approval(approval_id)

    if approval is None:
        return False

    if approval.status != ApprovalStatus.PENDING:
        return False

    if approval.is_expired:
        approval_store.update_approval_status(
            approval_id,
            ApprovalStatus.EXPIRED,
        )
        return False

    new_status = (
        ApprovalStatus.APPROVED
        if decision == "APPROVE"
        else ApprovalStatus.REJECTED
    )

    return approval_store.update_approval_status(
        approval_id,
        new_status,
        expected_status=ApprovalStatus.PENDING,
    )


def consume_approval(
    approval_id: str,
    request: ActionRequest,
) -> bool:
    """Atomically consume an approval for its exact original payload."""

    approval = approval_store.get_approval(approval_id)

    if approval is None:
        return False

    if (
        approval.agent_id != request.agent_id
        or approval.action != request.action
        or approval.resource != request.resource
    ):
        return False

    if not hmac.compare_digest(
        approval.payload_hash,
        calculate_payload_hash(request),
    ):
        return False

    if approval.status != ApprovalStatus.APPROVED:
        return False

    if approval.is_expired:
        approval_store.update_approval_status(
            approval_id,
            ApprovalStatus.EXPIRED,
            expected_status=ApprovalStatus.APPROVED,
        )
        return False

    return approval_store.update_approval_status(
        approval_id,
        ApprovalStatus.CONSUMED,
        expected_status=ApprovalStatus.APPROVED,
    )
