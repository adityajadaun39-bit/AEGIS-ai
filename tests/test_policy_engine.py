import json
import subprocess

import pytest

from backend.schemas.actions import ActionRequest
from backend.security import policy_engine


def make_request(action, resource):
    extra_fields = {}

    if action == "send_email":
        extra_fields = {
            "destination": "attacker@example.com",
            "content": "Simulated confidential data",
        }

    return ActionRequest(
        action=action,
        agent_id="research_agent",
        resource=resource,
        **extra_fields,
    )


@pytest.mark.parametrize(
    "action, resource, expected",
    [
        ("read_document", "public_report.pdf", True),
        ("read_document", "confidential_notes.txt", False),
        ("send_email", "email", False),
        ("search_documents", ".pdf", True),
    ],
)
def test_opa_policy_decisions(monkeypatch, action, resource, expected):
    monkeypatch.setattr(policy_engine, "find_opa", lambda: "fake-opa")

    response = {
        "result": [
            {"expressions": [{"value": expected}]}
        ]
    }

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=json.dumps(response),
            stderr="",
        )

    monkeypatch.setattr(policy_engine.subprocess, "run", fake_run)

    allowed, reason = policy_engine.evaluate_policy(
        make_request(action, resource)
    )

    assert allowed is expected
    assert reason == (
        "OPA policy allowed action"
        if expected
        else "OPA policy denied action"
    )


def test_opa_timeout_fails_closed(monkeypatch):
    monkeypatch.setattr(policy_engine, "find_opa", lambda: "fake-opa")

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="fake-opa", timeout=5)

    monkeypatch.setattr(policy_engine.subprocess, "run", fake_run)

    allowed, reason = policy_engine.evaluate_policy(
        make_request("read_document", "public_report.pdf")
    )

    assert allowed is False
    assert reason == "OPA execution failed"


def test_opa_nonzero_exit_fails_closed(monkeypatch):
    monkeypatch.setattr(policy_engine, "find_opa", lambda: "fake-opa")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr="OPA error",
        )

    monkeypatch.setattr(policy_engine.subprocess, "run", fake_run)

    allowed, reason = policy_engine.evaluate_policy(
        make_request("read_document", "public_report.pdf")
    )

    assert allowed is False
    assert reason == "OPA evaluation failed"


def test_missing_opa_fails_closed(monkeypatch):
    monkeypatch.setattr(policy_engine, "find_opa", lambda: None)

    allowed, reason = policy_engine.evaluate_policy(
        make_request("read_document", "public_report.pdf")
    )

    assert allowed is False
    assert reason == "OPA executable not found"