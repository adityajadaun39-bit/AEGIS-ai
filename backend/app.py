
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict

from fastapi import FastAPI, Header, HTTPException, Query
from backend.security.audit import (
    get_audit_logs,
    get_audit_trace,
    get_attack_trace,
)
from backend import config
from backend.schemas.actions import ActionRequest
from backend.security.authorization import authorize_action
from backend.security.policy_engine import evaluate_policy
from backend.security.approval_engine import (
    create_approval,
    review_approval,
)
from backend.security.gateway import execute_action


app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION)


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


@app.post("/approvals")
def request_human_approval(request: ActionRequest):
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
):
    return execute_action(request, approval_id=approval_id)



@app.get("/audit")
def read_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    decision: str | None = None,
    agent_id: str | None = None,
    attack_id: str | None = None,
):
    """Retrieve recent security audit events."""

    return {
        "events": get_audit_logs(
            limit=limit,
            decision=decision,
            agent_id=agent_id,
            attack_id=attack_id,
        )
    }


@app.get("/audit/traces/{trace_id}")
def read_audit_trace(trace_id: str):
    """Retrieve events belonging to one execution trace."""

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
def read_attack_trace(attack_id: str):
    """Retrieve all correlated events belonging to one attack."""

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



@app.get("/audit/traces/{trace_id}")
def read_audit_trace(trace_id: str):
    """Retrieve the chronological events for one execution trace."""

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



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app:app",
        host=config.HOST,
        port=config.PORT,
    )
