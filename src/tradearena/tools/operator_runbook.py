from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - public package installs may omit dev deps.
    Draft202012Validator = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schemas" / "operator_runbook_artifact.schema.json"


def validate_operator_runbook_artifact(payload: dict[str, Any]) -> list[str]:
    if Draft202012Validator is not None and SCHEMA_PATH.exists():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        schema_errors = [error.message for error in validator.iter_errors(payload)]
        return sorted([*schema_errors, *_verification_command_errors(payload)], key=str)
    return _fallback_schema_errors(payload)


def validate_operator_runbook_artifact_file(path: str | Path) -> tuple[dict[str, Any], list[str]]:
    payload, errors = _read_operator_runbook_json_file(path)
    if errors:
        return {}, errors
    if not isinstance(payload, dict):
        return {}, ["operator runbook artifact must be a JSON object"]
    return payload, validate_operator_runbook_artifact(payload)


def _read_operator_runbook_json_file(path: str | Path) -> tuple[Any, list[str]]:
    artifact_path = Path(path)
    if artifact_path.exists() and not artifact_path.is_file():
        return {}, [f"operator runbook artifact path is not a file: {artifact_path}"]
    try:
        return json.loads(artifact_path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return {}, [f"operator runbook artifact not found: {artifact_path}"]
    except json.JSONDecodeError as exc:
        return {}, [f"operator runbook artifact must contain valid JSON: {exc}"]


def _fallback_schema_errors(payload: dict[str, Any]) -> list[str]:
    required = {
        "schema",
        "live_submission",
        "default_mode",
        "allowed_modes",
        "manual_approval_required",
        "kill_switch_required",
        "approval_expiry_required",
        "artifact_retention_required",
        "incident_owner_required",
        "checklist",
        "verification_commands",
        "safety_note",
    }
    errors: list[str] = []
    missing = sorted(required - set(payload))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if payload.get("schema") != "trellm_operator_runbook_v0.1":
        errors.append("schema must be trellm_operator_runbook_v0.1")
    if payload.get("live_submission") is not False:
        errors.append("live_submission must be false")
    if payload.get("default_mode") not in {"offline_export", "dry_run"}:
        errors.append("default_mode must be offline_export or dry_run")
    allowed_modes = payload.get("allowed_modes")
    if not isinstance(allowed_modes, list) or "live_human_approved" not in allowed_modes:
        errors.append("allowed_modes must include live_human_approved")
    for field in [
        "manual_approval_required",
        "kill_switch_required",
        "approval_expiry_required",
        "artifact_retention_required",
        "incident_owner_required",
    ]:
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    checklist = payload.get("checklist")
    if not isinstance(checklist, list) or len(checklist) < 5:
        errors.append("checklist must contain at least five items")
    errors.extend(_verification_command_errors(payload))
    return errors


def _verification_command_errors(payload: dict[str, Any]) -> list[str]:
    verification_commands = payload.get("verification_commands")
    if isinstance(verification_commands, list) and any(
        isinstance(command, str) and "validate-live-readiness" in command for command in verification_commands
    ):
        return []
    return ["verification_commands must include validate-live-readiness"]
