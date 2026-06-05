from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - public package installs may omit dev deps.
    Draft202012Validator = None  # type: ignore[assignment]

from tradearena.tools.broker_capability import validate_broker_adapter_capability_file
from tradearena.tools.broker_export import (
    validate_broker_approval_artifact_file,
    validate_broker_approval_request_binding,
    validate_broker_handoff_artifact_file,
    validate_broker_response_artifact_file,
)
from tradearena.tools.operator_runbook import validate_operator_runbook_artifact_file

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schemas" / "live_readiness_preflight.schema.json"


def validate_live_readiness_preflight_bundle_file(
    path: str | Path, *, now: str | None = None
) -> tuple[dict[str, Any], list[str]]:
    bundle_path = Path(path)
    bundle, errors = _read_preflight_json_file(bundle_path)
    if errors:
        return {}, errors
    if not isinstance(bundle, dict):
        return {}, ["live-readiness preflight bundle must be a JSON object"]

    schema_errors = _validate_bundle_schema(bundle)
    component_summary: dict[str, Any] = {"schema_valid": not schema_errors, "components": {}}
    component_errors = _validate_components(bundle, bundle_path=bundle_path, now=now, summary=component_summary)
    errors = sorted([*schema_errors, *component_errors], key=str)
    component_summary["ready"] = not errors
    component_summary["error_count"] = len(errors)
    return component_summary, errors


def _read_preflight_json_file(path: Path) -> tuple[Any, list[str]]:
    if path.exists() and not path.is_file():
        return {}, [f"live-readiness preflight bundle path is not a file: {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return {}, [f"live-readiness preflight bundle not found: {path}"]
    except json.JSONDecodeError as exc:
        return {}, [f"live-readiness preflight bundle must contain valid JSON: {exc}"]


def _validate_bundle_schema(bundle: dict[str, Any]) -> list[str]:
    if Draft202012Validator is not None and SCHEMA_PATH.exists():
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        return sorted((error.message for error in validator.iter_errors(bundle)), key=str)
    return _fallback_schema_errors(bundle)


def _fallback_schema_errors(bundle: dict[str, Any]) -> list[str]:
    required = {
        "schema",
        "capability_manifest",
        "handoff_artifact",
        "approval_artifact",
        "response_artifact",
        "operator_runbook_artifact",
        "approval_checked_at",
        "safety_note",
    }
    errors: list[str] = []
    missing = sorted(required - set(bundle))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    if bundle.get("schema") != "trellm_live_readiness_preflight_v0.1":
        errors.append("schema must be trellm_live_readiness_preflight_v0.1")
    return errors


def _validate_components(
    bundle: dict[str, Any], *, bundle_path: Path, now: str | None, summary: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    checked_at = now or _text(bundle.get("approval_checked_at"))
    components = summary["components"]

    capability_path = _resolve_bundle_path(bundle_path, bundle.get("capability_manifest"))
    handoff_path = _resolve_bundle_path(bundle_path, bundle.get("handoff_artifact"))
    approval_path = _resolve_bundle_path(bundle_path, bundle.get("approval_artifact"))
    response_path = _resolve_bundle_path(bundle_path, bundle.get("response_artifact"))
    runbook_path = _resolve_bundle_path(bundle_path, bundle.get("operator_runbook_artifact"))

    capability, capability_errors = validate_broker_adapter_capability_file(capability_path)
    components["capability_manifest"] = _component_result(capability_path, capability_errors)
    errors.extend(_prefix_errors("capability_manifest", capability_errors))

    handoff, handoff_errors = validate_broker_handoff_artifact_file(handoff_path)
    components["handoff_artifact"] = _component_result(handoff_path, handoff_errors)
    errors.extend(_prefix_errors("handoff_artifact", handoff_errors))

    approval, approval_errors = validate_broker_approval_artifact_file(approval_path, now=checked_at)
    components["approval_artifact"] = _component_result(approval_path, approval_errors)
    errors.extend(_prefix_errors("approval_artifact", approval_errors))

    if not approval_errors and not handoff_errors:
        binding_errors = validate_broker_approval_request_binding(approval, handoff_path, now=checked_at)
    else:
        binding_errors = ["approval binding skipped until approval and handoff artifacts validate"]
    components["approval_binding"] = {"valid": not binding_errors, "error_count": len(binding_errors)}
    errors.extend(_prefix_errors("approval_binding", binding_errors))

    response, response_errors = validate_broker_response_artifact_file(response_path)
    components["response_artifact"] = _component_result(response_path, response_errors)
    errors.extend(_prefix_errors("response_artifact", response_errors))

    _, runbook_errors = validate_operator_runbook_artifact_file(runbook_path)
    components["operator_runbook_artifact"] = _component_result(runbook_path, runbook_errors)
    errors.extend(_prefix_errors("operator_runbook_artifact", runbook_errors))

    if not capability_errors:
        errors.extend(_capability_boundary_errors(capability, handoff, response))
    return errors


def _capability_boundary_errors(
    capability: dict[str, Any], handoff: dict[str, Any], response: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    supported_modes = _string_set(capability.get("supported_modes"))
    account_modes = _string_set(capability.get("account_modes"))
    for label, payload in (("handoff_artifact", handoff), ("response_artifact", response)):
        adapter_mode = payload.get("adapter_mode")
        account_mode = payload.get("account_mode")
        if isinstance(adapter_mode, str) and adapter_mode not in supported_modes:
            errors.append(f"{label}.adapter_mode {adapter_mode} is not declared in capability_manifest.supported_modes")
        if isinstance(account_mode, str) and account_mode not in account_modes:
            errors.append(f"{label}.account_mode {account_mode} is not declared in capability_manifest.account_modes")
        if capability.get("supports_live_submission") is not True and payload.get("live_submission") is True:
            errors.append(f"{label} uses live_submission but capability_manifest does not support live submission")
    return errors


def _component_result(path: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "path": _display_path(path),
        "exists": path.exists(),
        "valid": not errors,
        "error_count": len(errors),
    }


def _prefix_errors(label: str, errors: list[str]) -> list[str]:
    return [f"{label}: {error}" for error in errors]


def _resolve_bundle_path(bundle_path: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        return bundle_path.parent / "<missing>"
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    root_candidate = ROOT / candidate
    if root_candidate.exists() or value.startswith(("outputs/", "docs/", "examples/", "schemas/")):
        return root_candidate
    return bundle_path.parent / candidate


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None
