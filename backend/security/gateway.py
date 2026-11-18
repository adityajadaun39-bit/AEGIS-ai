
"""Central security gateway for AEGIS."""

import uuid

from backend.schemas.actions import ActionRequest
from backend.security.authorization import AGENT_REGISTRY, authorize_action
from backend.security.policy_engine import (
    evaluate_policy,
    evaluate_information_flow,
)
from backend.security.audit import log_decision
from backend.security.approval_engine import (
    create_approval,
    consume_approval,
)
from backend.security.provenance_context import (
    register_document_context,
    resolve_context_details,
    resolve_provenance_context,
)
from backend.tools.broker import tool_broker
from backend.security.ml_detector import detect_injection
from backend.security.dlp_engine import scan_for_secrets


def _deny(
    request: ActionRequest,
    reason: str,
    trace_id: str,
    approval_id: str | None = None,
    tool_invoked: bool = False,
    attack_id: str | None = None,
    ml_score: float | None = None,
) -> dict:
    """Record and return a denied security decision."""

    log_decision(
        request.agent_id,
        request.action,
        request.resource,
        "DENY",
        reason,
        trace_id=trace_id,
        attack_id=attack_id,
        approval_id=approval_id,
        tool_invoked=tool_invoked,
    )

    out = {
        "success": False,
        "decision": "DENY",
        "reason": reason,
        "trace_id": trace_id,
        "attack_id": attack_id,
    }
    if ml_score is not None:
        out["ml_score"] = ml_score
    return out


def execute_action(
    request: ActionRequest,
    approval_id: str | None = None,
) -> dict:
    """Authorize, verify provenance, approve, audit, and execute."""

    trace_id = str(uuid.uuid4())
    attack_id = None
    provenance_records = None

    # 0. Scan for prompt injection and sensitive credentials (DLP)
    ml_result = detect_injection(request.content or request.resource)
    dlp_result = scan_for_secrets(request.content)

    if request.action == "send_email" and dlp_result["has_sensitive_data"]:
        finding_types = ", ".join(f["category"] for f in dlp_result["findings"])
        return _deny(
            request,
            f"DLP policy violation: sensitive credentials detected ({finding_types})",
            trace_id,
            approval_id,
            attack_id=attack_id,
            ml_score=ml_result["score"],
        )

    # 1. Resolve server-controlled provenance for outbound email.
    if request.action == "send_email":
        context = resolve_context_details(
            request.provenance_context_id
        )

        if context is not None:
            attack_id = context["attack_id"]
            provenance_records = context["records"]
        else:
            # Compatibility with tests and legacy resolver callers.
            provenance_records = resolve_provenance_context(
                request.provenance_context_id
            )

    # 2. Check agent authorization.
    allowed, reason = authorize_action(
        request.agent_id,
        request.action,
        request.resource,
    )

    if not allowed:
        return _deny(
            request,
            reason,
            trace_id,
            approval_id,
            attack_id=attack_id,
        )

    # 3. Evaluate OPA policy.
    allowed, reason = evaluate_policy(request)

    if not allowed:
        return _deny(
            request,
            reason,
            trace_id,
            approval_id,
            attack_id=attack_id,
        )

    # 4. Enforce information-flow security BEFORE approval.
    # Human approval must never override untrusted or confidential provenance.
    allowed, reason = evaluate_information_flow(
        request,
        provenance_records,
    )

    if not allowed:
        return _deny(
            request,
            reason,
            trace_id,
            approval_id,
            attack_id=attack_id,
        )

    # 5. Require human approval for outbound email.
    if request.action == "send_email":

        if not approval_id:
            try:
                approval = create_approval(request)
            except Exception:
                return _deny(
                    request,
                    "Could not create approval request",
                    trace_id,
                    attack_id=attack_id,
                )

            reason = "Human approval required before email execution"

            log_decision(
                request.agent_id,
                request.action,
                request.resource,
                "REQUIRES_APPROVAL",
                reason,
                trace_id=trace_id,
                attack_id=attack_id,
                approval_id=approval.approval_id,
                tool_invoked=False,
            )

            return {
                "success": False,
                "decision": "REQUIRES_APPROVAL",
                "reason": reason,
                "approval_id": approval.approval_id,
                "trace_id": trace_id,
                "attack_id": attack_id,
            }

        # Verify and consume approval bound to the exact original payload.
        if not consume_approval(approval_id, request):
            return _deny(
                request,
                "Invalid, expired, consumed, or mismatched approval",
                trace_id,
                approval_id,
                attack_id=attack_id,
            )

    # 6. Resolve agent permissions.
    permissions = AGENT_REGISTRY.get(request.agent_id)

    if permissions is None:
        return _deny(
            request,
            "Agent permissions not found",
            trace_id,
            approval_id,
            attack_id=attack_id,
        )

    # 7. Execute only through the controlled tool broker.
    try:
        result = tool_broker.execute(
            action=request.action,
            resource=request.resource,
            allowed_resources=permissions.allowed_resources,
            destination=request.destination,
            content=request.content,
        )

    except Exception:
        reason = "Tool execution failed"

        log_decision(
            request.agent_id,
            request.action,
            request.resource,
            "ERROR",
            reason,
            trace_id=trace_id,
            attack_id=attack_id,
            approval_id=approval_id,
            tool_invoked=True,
        )

        return {
            "success": False,
            "decision": "ERROR",
            "reason": reason,
            "trace_id": trace_id,
            "attack_id": attack_id,
        }

    if not result.get("success", False):
        reason = result.get(
            "error",
            "Tool execution unsuccessful",
        )

        log_decision(
            request.agent_id,
            request.action,
            request.resource,
            "ERROR",
            reason,
            trace_id=trace_id,
            attack_id=attack_id,
            approval_id=approval_id,
            tool_invoked=True,
        )

        return {
            "success": False,
            "decision": "ERROR",
            "reason": reason,
            "result": result,
            "trace_id": trace_id,
            "attack_id": attack_id,
        }

    response = {
        "success": True,
        "decision": "ALLOW",
        "result": result,
        "trace_id": trace_id,
        "attack_id": attack_id,
        "ml_score": ml_result["score"],
        "ml_verdict": ml_result["verdict"],
        "has_sensitive_data": dlp_result["has_sensitive_data"],
    }

    # 8. Register server-verified provenance after document reads.
    if request.action == "read_document":
        try:
            context_id = register_document_context(
                request.resource,
                result["provenance"],
            )
        except Exception:
            return _deny(
                request,
                "Could not verify document provenance",
                trace_id,
                approval_id,
                tool_invoked=True,
                attack_id=attack_id,
            )

        response["provenance_context_id"] = context_id

        context = resolve_context_details(context_id)

        if context is not None:
            response["attack_id"] = context["attack_id"]
            attack_id = context["attack_id"]

    # 9. Audit successful execution.
    log_decision(
        request.agent_id,
        request.action,
        request.resource,
        "ALLOW",
        "Authorization, OPA, provenance, and approval checks passed",
        trace_id=trace_id,
        attack_id=attack_id,
        approval_id=approval_id,
        tool_invoked=True,
        tool_succeeded=True,
    )

    return response
