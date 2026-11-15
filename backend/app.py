import hmac
import os
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from backend import config
from backend.schemas.actions import ActionRequest
from backend.security.audit import (
    get_audit_logs,
    get_audit_trace,
    get_attack_trace,
)
from backend.security.authorization import authorize_action
from backend.security.policy_engine import (
    evaluate_policy,
    evaluate_information_flow,
)
from backend.security.provenance_context import resolve_context_details
from backend.security.approval_engine import (
    create_approval,
    review_approval,
)
from backend.security.gateway import execute_action

from backend.schemas.approval import ApprovalStatus
from backend.security import approval_store
from backend.security.agent_auth import authenticate_agent


app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION)


def _token_matches(supplied: str | None, env_name: str) -> bool:
    expected = os.getenv(env_name)

    return bool(
        supplied
        and expected
        and hmac.compare_digest(supplied, expected)
    )


def require_admin(admin_token: str | None) -> None:
    if not _token_matches(admin_token, "AEGIS_ADMIN_TOKEN"):
        raise HTTPException(
            status_code=403,
            detail="Administrator authentication required",
        )


def require_reviewer_or_admin(
    reviewer_token: str | None,
    admin_token: str | None,
) -> None:
    if not (
        _token_matches(reviewer_token, "AEGIS_APPROVER_TOKEN")
        or _token_matches(admin_token, "AEGIS_ADMIN_TOKEN")
    ):
        raise HTTPException(
            status_code=403,
            detail="Reviewer or administrator authentication required",
        )


def require_agent_identity(
    request: ActionRequest,
    token: str | None,
) -> None:
    """Authenticate the API caller and prevent agent impersonation."""

    authenticated_agent = authenticate_agent(token)

    if authenticated_agent is None:
        raise HTTPException(
            status_code=403,
            detail="Invalid or unconfigured agent credentials",
        )

    if authenticated_agent != request.agent_id:
        raise HTTPException(
            status_code=403,
            detail="Authenticated agent does not match request agent_id",
        )


class ApprovalReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["APPROVE", "REJECT"]
    reviewer_id: str


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "ok",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}

@app.get("/approvals")
def list_human_approvals(
    status: ApprovalStatus = Query(
        default=ApprovalStatus.PENDING
    ),
    reviewer_token: str | None = Header(
        default=None,
        alias="X-AEGIS-Approver-Token",
    ),
    admin_token: str | None = Header(
        default=None,
        alias="X-AEGIS-Admin-Token",
    ),
):
    require_reviewer_or_admin(reviewer_token, admin_token)

    approvals = approval_store.list_approvals(status)

    return {
        "count": len(approvals),
        "approvals": [
            {
                "approval_id": item.approval_id,
                "agent_id": item.agent_id,
                "action": item.action,
                "resource": item.resource,
                "status": item.status.value,
                "created_at": item.created_at.isoformat(),
                "expires_at": item.expires_at.isoformat(),
                "is_expired": item.is_expired,
            }
            for item in approvals
        ],
    }

@app.post("/approvals")
def request_human_approval(
    request: ActionRequest,
    agent_token: str | None = Header(
        default=None,
        alias="X-AEGIS-Agent-Token",
    ),
):
    require_agent_identity(request, agent_token)

    if request.action != "send_email":
        raise HTTPException(
            status_code=400,
            detail="This action does not require human approval",
        )

    allowed, reason = authorize_action(
        request.agent_id,
        request.action,
        request.resource,
    )

    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    allowed, reason = evaluate_policy(request)

    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    context = resolve_context_details(
        request.provenance_context_id
    )

    if context is None:
        raise HTTPException(
            status_code=403,
            detail="Verified provenance context required",
        )

    allowed, reason = evaluate_information_flow(
        request,
        context["records"],
    )

    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    try:
        approval = create_approval(request)
    except (ValueError, RuntimeError):
        raise HTTPException(
            status_code=500,
            detail="Could not create approval request",
        )

    return approval.model_dump(mode="json")

@app.post("/approvals/{approval_id}/review")
def review_human_approval(
    approval_id: str,
    body: ApprovalReviewBody,
    reviewer_token: str = Header(alias="X-AEGIS-Approver-Token"),
):
    try:
        updated = review_approval(
            approval_id=approval_id,
            decision=body.decision,
            reviewer_id=body.reviewer_id,
            reviewer_token=reviewer_token,
        )
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Reviewer authentication failed or is not configured",
        )

    if not updated:
        raise HTTPException(
            status_code=409,
            detail="Approval not found, expired, or already reviewed",
        )

    return {
        "approval_id": approval_id,
        "decision": body.decision,
        "success": True,
    }


@app.post("/actions")
def submit_action(
    request: ActionRequest,
    approval_id: str | None = None,
    agent_token: str | None = Header(
        default=None,
        alias="X-AEGIS-Agent-Token",
    ),
):
    require_agent_identity(request, agent_token)

    return execute_action(request, approval_id=approval_id)


@app.get("/audit")
def read_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    decision: str | None = None,
    agent_id: str | None = None,
    attack_id: str | None = None,
    admin_token: str | None = Header(
        default=None,
        alias="X-AEGIS-Admin-Token",
    ),
):
    require_admin(admin_token)

    return {
        "events": get_audit_logs(
            limit=limit,
            decision=decision,
            agent_id=agent_id,
            attack_id=attack_id,
        )
    }

@app.get("/audit/traces/{trace_id}")
def read_audit_trace(
    trace_id: str,
    admin_token: str | None = Header(
        default=None,
        alias="X-AEGIS-Admin-Token",
    ),
):
    require_admin(admin_token)

    events = get_audit_trace(trace_id)

    if not events:
        raise HTTPException(
            status_code=404,
            detail="Audit trace not found",
        )

    return {
        "trace_id": trace_id,
        "event_count": len(events),
        "events": events,
    }

@app.get("/audit/attacks/{attack_id}")
def read_attack_trace(
    attack_id: str,
    admin_token: str | None = Header(
        default=None,
        alias="X-AEGIS-Admin-Token",
    ),
):
    require_admin(admin_token)

    events = get_attack_trace(attack_id)

    if not events:
        raise HTTPException(
            status_code=404,
            detail="Attack correlation not found",
        )

    return {
        "attack_id": attack_id,
        "event_count": len(events),
        "events": events,
    }