from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "spec_id",
    "status",
    "claim_boundary",
    "data_windows",
    "market_rules",
    "execution",
    "allowed_information",
    "model_audit",
    "seeds",
    "baselines",
    "metrics",
    "statistics",
    "failure_policy",
    "required_artifacts",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and hash a TradeArena benchmark spec JSON file.")
    parser.add_argument("spec", nargs="?", default="benchmarks/v0.2/spec.json")
    args = parser.parse_args()

    try:
        payload = _load_spec(Path(args.spec))
    except ValueError as exc:
        result = {
            "spec": args.spec,
            "valid": False,
            "spec_id": None,
            "schema_version": None,
            "canonical_sha256": None,
            "errors": [str(exc)],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    errors = validate_spec(payload)
    result = {
        "spec": args.spec,
        "valid": not errors,
        "spec_id": payload.get("spec_id"),
        "schema_version": payload.get("schema_version"),
        "canonical_sha256": canonical_spec_hash(payload),
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


def _load_spec(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("benchmark spec file must contain valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("benchmark spec file must be a JSON object")
    return payload


def validate_spec(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_TOP_LEVEL.difference(payload)
    if missing:
        errors.append("missing top-level fields: " + ", ".join(sorted(missing)))
    if payload.get("status") != "frozen":
        errors.append("status must be 'frozen'")
    seeds = payload.get("seeds", [])
    if not isinstance(seeds, list) or len(seeds) < 5:
        errors.append("seeds must contain at least five entries")
    if "always-hold" not in payload.get("baselines", []):
        errors.append("baselines must include always-hold")
    if "random" not in payload.get("baselines", []):
        errors.append("baselines must include random")
    paired_tests = payload.get("statistics", {}).get("paired_tests", [])
    for test_name in ("paired_bootstrap", "paired_sign_flip_permutation"):
        if test_name not in paired_tests:
            errors.append(f"statistics.paired_tests must include {test_name}")
    metrics = payload.get("metrics", {})
    for metric in ("total_return", "max_drawdown", "execution_fill_rate", "trajectory_reproducibility_coverage"):
        if metric not in metrics.get("primary", []):
            errors.append(f"metrics.primary must include {metric}")
    real_windows = payload.get("data_windows", {}).get("real_market", [])
    if not real_windows:
        errors.append("data_windows.real_market must define at least one window")
    for index, window in enumerate(real_windows):
        for field in ("symbols", "start", "end", "frequency", "max_periods", "window_offset_policy"):
            if field not in window:
                errors.append(f"real_market[{index}] missing {field}")
    return errors


def canonical_spec_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
