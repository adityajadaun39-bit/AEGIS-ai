
"""OPA-backed contextual security policy checks for AEGIS."""

import json
import os
import shutil
import subprocess
from pathlib import Path

from backend.schemas.actions import ActionRequest
from backend.schemas.provenance import (
    Provenance,
    SensitivityLevel,
    TrustLevel,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = PROJECT_ROOT / "policies" / "agent_access.rego"
OPA_TIMEOUT_SECONDS = 5


def evaluate_information_flow(
    request: ActionRequest,
    provenance_records: list[Provenance] | None,
) -> tuple[bool, str]:
    """Check whether source information may flow into an outbound action."""

    if request.action != "send_email":
        return True, "No outbound information flow"

    if not provenance_records:
        return False, "Verified provenance context required for outbound email"

    for record in provenance_records:
        if record.sensitivity == SensitivityLevel.CONFIDENTIAL:
            return False, "Confidential information cannot be sent externally"

        if record.contains_untrusted_instructions:
            return False, "Untrusted instructions detected in source lineage"

        if record.trust_level == TrustLevel.UNTRUSTED:
            return False, "Untrusted source data cannot be sent externally"

    return True, "Information-flow policy allowed action"



def find_opa() -> str | None:
    """Locate the OPA executable."""

    configured_path = os.environ.get("OPA_PATH")

    if configured_path:
        return configured_path

    discovered_path = shutil.which("opa")

    if discovered_path:
        return discovered_path

    # Windows fallback for the current development setup.
    windows_path = Path(r"C:\Tools\OPA\opa.exe")

    if windows_path.is_file():
        return str(windows_path)

    return None


def evaluate_policy(request: ActionRequest) -> tuple[bool, str]:
    """Evaluate an action through OPA. Deny if evaluation fails."""

    opa_executable = find_opa()

    if not opa_executable:
        return False, "OPA executable not found"

    if not POLICY_PATH.is_file():
        return False, "OPA policy file not found"

    input_data = request.model_dump(mode="json")

    command = [
        opa_executable,
        "eval",
        "--format=json",
        "--data",
        str(POLICY_PATH),
        "--stdin-input",
        "data.aegis.agent_access.allow",
    ]

    try:
        result = subprocess.run(
            command,
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=OPA_TIMEOUT_SECONDS,
            check=False,
        )

        if result.returncode != 0:
            return False, "OPA evaluation failed"

        response = json.loads(result.stdout)

        expressions = response.get("result", [])

        if not expressions:
            return False, "OPA returned no policy decision"

        value = expressions[0].get("expressions", [{}])[0].get("value")

        if value is True:
            return True, "OPA policy allowed action"

        return False, "OPA policy denied action"

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "OPA execution failed"

    except (json.JSONDecodeError, IndexError, TypeError, KeyError):
        return False, "Invalid OPA response"
