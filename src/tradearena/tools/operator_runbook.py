from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - public package installs may omit dev deps.
    Draft202012Validator = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schemas" / "operator_runbook_artifact.schema.json"
_ISO_TIMESTAMP_WITH_TZ_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_SHELL_CHAINING_TOKENS = {";", "&", "&&", "||", "|"}


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
    if not isinstance(verification_commands, list):
        return ["verification_commands must include validate-live-readiness"]
    commands = [command for command in verification_commands if isinstance(command, str)]
    if any(_has_live_readiness_command_with_shell_chaining(command) for command in commands):
        return ["verification_commands validate-live-readiness command must not contain shell chaining"]
    if any(_is_runnable_live_readiness_command(command) for command in commands):
        return []
    if any(_has_live_readiness_command_with_invalid_now(command) for command in commands):
        return ["verification_commands validate-live-readiness --now value must be an ISO timestamp with timezone"]
    if any("validate-live-readiness" in command for command in commands):
        return [
            "verification_commands must include a runnable validate-live-readiness command "
            "with a preflight bundle path and --now timestamp"
        ]
    return ["verification_commands must include validate-live-readiness"]


def _is_runnable_live_readiness_command(command: str) -> bool:
    tokens = _command_tokens(command)
    if any(token in _SHELL_CHAINING_TOKENS for token in tokens):
        return False
    if "validate-live-readiness" not in tokens:
        return False
    command_index = tokens.index("validate-live-readiness")
    if command_index == 0:
        return False
    prefix = tokens[:command_index]
    if prefix != ["tradearena"] and prefix != ["python", "-m", "tradearena.cli"]:
        return False
    args = tokens[command_index + 1 :]
    has_preflight_bundle = any(token.endswith(".json") and "preflight" in token for token in args)
    if "--now" not in args:
        return False
    now_index = args.index("--now")
    has_now_value = now_index + 1 < len(args) and not args[now_index + 1].startswith("-")
    if not has_now_value:
        return False
    return has_preflight_bundle and _is_iso_timestamp_with_timezone(args[now_index + 1])


def _has_live_readiness_command_with_invalid_now(command: str) -> bool:
    tokens = _command_tokens(command)
    if "validate-live-readiness" not in tokens or "--now" not in tokens:
        return False
    args = tokens[tokens.index("validate-live-readiness") + 1 :]
    now_index = args.index("--now")
    return now_index + 1 < len(args) and not _is_iso_timestamp_with_timezone(args[now_index + 1])


def _has_live_readiness_command_with_shell_chaining(command: str) -> bool:
    tokens = _command_tokens(command)
    return "validate-live-readiness" in tokens and any(token in _SHELL_CHAINING_TOKENS for token in tokens)


def _command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _is_iso_timestamp_with_timezone(value: str) -> bool:
    return bool(_ISO_TIMESTAMP_WITH_TZ_RE.fullmatch(value))
