from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - public package installs may omit dev deps.
    Draft202012Validator = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "operator_runbook_artifact.schema.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a TreLLM operator runbook artifact.")
    parser.add_argument("artifact", help="Path to an operator runbook summary JSON file.")
    args = parser.parse_args(argv)

    path = Path(args.artifact)
    try:
        payload = _load_artifact(path)
    except ValueError as exc:
        print(f"Invalid operator runbook artifact: {path}")
        print(f"  - {exc}")
        return 1

    errors = validate_operator_runbook_artifact(payload)
    if errors:
        print(f"Invalid operator runbook artifact: {path}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Valid operator runbook artifact: {path}")
    return 0


def validate_operator_runbook_artifact(payload: dict[str, Any]) -> list[str]:
    if Draft202012Validator is None:
        return _fallback_schema_errors(payload)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return sorted((error.message for error in validator.iter_errors(payload)), key=str)


def _load_artifact(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("operator runbook artifact must contain valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("operator runbook artifact must be a JSON object")
    return payload


def _fallback_schema_errors(payload: dict[str, Any]) -> list[str]:
    required = {
        "schema",
        "live_submission",
        "default_mode",
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
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
