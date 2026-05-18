from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from tradearena.core.reproducibility import compute_reproducibility_hash


REQUIRED_TOP_LEVEL = (
    "schema_version",
    "scenario_id",
    "agent",
    "data_source",
    "execution_config",
    "risk_config",
    "metrics",
    "trajectory_manifest",
    "reproducibility_hash",
    "redaction",
)


def load_submission(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_submission(payload: dict[str, Any], *, verify_hash: bool = True) -> list[str]:
    errors: list[str] = []
    _require_keys(payload, REQUIRED_TOP_LEVEL, "submission", errors)
    if errors:
        return errors

    if payload.get("schema_version") != "0.1":
        errors.append("submission.schema_version must be '0.1'")

    _require_keys(
        payload["agent"],
        ("agent_type", "model_family", "model_identifier_redacted"),
        "agent",
        errors,
    )
    _require_keys(
        payload["data_source"],
        ("name", "frequency", "symbols", "timestamp_policy"),
        "data_source",
        errors,
    )
    _require_keys(
        payload["execution_config"],
        ("commission_bps", "base_slippage_bps", "latency_steps", "participation_rate"),
        "execution_config",
        errors,
    )
    _require_keys(payload["risk_config"], ("risk_manager", "risk_budget"), "risk_config", errors)
    _require_keys(
        payload["metrics"],
        (
            "total_return",
            "max_drawdown",
            "execution_fill_rate",
            "rejected_order_count",
            "risk_clipped_decisions",
            "risk_violation_count",
            "trajectory_reproducibility_coverage",
        ),
        "metrics",
        errors,
    )
    _require_keys(
        payload["trajectory_manifest"],
        ("format", "path_or_uri", "raw_prompts_included", "raw_responses_included"),
        "trajectory_manifest",
        errors,
    )
    _require_keys(
        payload["redaction"],
        ("provider_secrets_removed", "timestamps_masked", "raw_provider_text_removed"),
        "redaction",
        errors,
    )

    symbols = payload["data_source"].get("symbols", [])
    if not isinstance(symbols, list) or not symbols:
        errors.append("data_source.symbols must be a non-empty list")

    fill_rate = payload["metrics"].get("execution_fill_rate")
    if not _is_number(fill_rate) or not 0.0 <= float(fill_rate) <= 1.0:
        errors.append("metrics.execution_fill_rate must be a number in [0, 1]")

    coverage = payload["metrics"].get("trajectory_reproducibility_coverage")
    if not _is_number(coverage) or not 0.0 <= float(coverage) <= 1.0:
        errors.append("metrics.trajectory_reproducibility_coverage must be a number in [0, 1]")

    for path in (
        "redaction.provider_secrets_removed",
        "redaction.raw_provider_text_removed",
        "trajectory_manifest.raw_prompts_included",
        "trajectory_manifest.raw_responses_included",
    ):
        value = _get_path(payload, path)
        if not isinstance(value, bool):
            errors.append(f"{path} must be boolean")

    if verify_hash:
        expected = compute_reproducibility_hash(payload)
        observed = payload.get("reproducibility_hash")
        if observed != expected:
            errors.append(f"reproducibility_hash mismatch: expected {expected}, observed {observed}")

    return errors


def validate_submission_file(path: str | Path, *, verify_hash: bool = True) -> tuple[dict[str, Any], list[str]]:
    payload = load_submission(path)
    return payload, validate_submission(payload, verify_hash=verify_hash)


def discover_submission_files(input_dir: str | Path) -> list[Path]:
    root = Path(input_dir)
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*.json") if path.is_file())


def build_registry_rows(input_dir: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_hashes: defaultdict[str, int] = defaultdict(int)
    for path in discover_submission_files(input_dir):
        payload, payload_errors = validate_submission_file(path)
        if payload_errors:
            errors.extend(f"{path}: {error}" for error in payload_errors)
            continue
        seen_hashes[payload["reproducibility_hash"]] += 1
        rows.append(
            {
                "scenario_id": payload["scenario_id"],
                "agent_type": payload["agent"]["agent_type"],
                "model_family": payload["agent"]["model_family"],
                "model_redacted": payload["agent"]["model_identifier_redacted"],
                "data_source": payload["data_source"]["name"],
                "frequency": payload["data_source"]["frequency"],
                "symbols": len(payload["data_source"]["symbols"]),
                "total_return": payload["metrics"]["total_return"],
                "max_drawdown": payload["metrics"]["max_drawdown"],
                "fill_rate": payload["metrics"]["execution_fill_rate"],
                "rejected_orders": payload["metrics"]["rejected_order_count"],
                "risk_edits": payload["metrics"]["risk_clipped_decisions"],
                "audit_coverage": payload["metrics"]["trajectory_reproducibility_coverage"],
                "reproducibility_hash": payload["reproducibility_hash"],
                "source_file": path.as_posix(),
            }
        )
    for fingerprint, count in seen_hashes.items():
        if count > 1:
            errors.append(f"duplicate reproducibility_hash appears {count} times: {fingerprint}")
    return rows, errors


def write_registry_markdown(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Community Benchmark Registry",
        "",
        "This registry is generated from redacted benchmark submission manifests.",
        "It is designed to compare audit-ready runs without exposing raw provider",
        "prompts, responses, private portfolios, or credentials.",
        "",
        "| Scenario | Agent | Data | Return | Max DD | Fill | Rejected | Risk edits | Audit | Hash |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        agent = f"{row['agent_type']} / {row['model_family']}"
        data = f"{row['data_source']} ({row['frequency']}, {row['symbols']} symbols)"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["scenario_id"]),
                    agent,
                    data,
                    _fmt_float(row["total_return"]),
                    _fmt_float(row["max_drawdown"]),
                    _fmt_float(row["fill_rate"]),
                    str(row["rejected_orders"]),
                    str(row["risk_edits"]),
                    _fmt_float(row["audit_coverage"]),
                    f"`{str(row['reproducibility_hash'])[:18]}...`",
                ]
            )
            + " |"
        )
    if not rows:
        lines.append("| _No accepted submissions yet._ |  |  |  |  |  |  |  |  |  |")
    lines.extend(
        [
            "",
            "## Submission Rules",
            "",
            "- Submit redacted manifests, not raw model prompt/response caches.",
            "- Do not include broker credentials, API keys, or private holdings.",
            "- Keep `reproducibility_hash` stable for the same scenario, data,",
            "  execution config, risk config, agent metadata, and trajectory manifest.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_registry_html(rows: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table_rows = "\n".join(
        "<tr>"
        f"<td>{row['scenario_id']}</td>"
        f"<td>{row['agent_type']} / {row['model_family']}</td>"
        f"<td>{row['data_source']} ({row['frequency']})</td>"
        f"<td>{float(row['total_return']):.4f}</td>"
        f"<td>{float(row['max_drawdown']):.4f}</td>"
        f"<td>{float(row['fill_rate']):.4f}</td>"
        f"<td>{row['rejected_orders']}</td>"
        f"<td>{row['risk_edits']}</td>"
        f"<td><code>{str(row['reproducibility_hash'])[:22]}...</code></td>"
        "</tr>"
        for row in rows
    )
    if not table_rows:
        table_rows = '<tr><td colspan="9">No accepted submissions yet.</td></tr>'
    html_text = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TradeArena Community Benchmark Registry</title>
<style>
body {{ margin: 0; font-family: Inter, Arial, sans-serif; background: #f8fafc; color: #0f172a; }}
main {{ max-width: 1120px; margin: 0 auto; padding: 38px 24px 52px; }}
h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
p {{ color: #475569; line-height: 1.55; }}
table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d8e2ed; }}
th, td {{ padding: 10px 11px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 13px; }}
th {{ background: #eff6ff; color: #1e3a8a; }}
code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
</style>
<main>
  <h1>TradeArena Community Benchmark Registry</h1>
  <p>Generated from redacted benchmark submission manifests. Raw provider
  prompts, responses, credentials, and private portfolio data are not included.</p>
  <table>
    <thead>
      <tr>
        <th>Scenario</th><th>Agent</th><th>Data</th><th>Return</th>
        <th>Max DD</th><th>Fill</th><th>Rejected</th><th>Risk edits</th><th>Hash</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</main>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def _require_keys(payload: Any, keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append(f"{label} must be an object")
        return
    for key in keys:
        if key not in payload:
            errors.append(f"{label}.{key} is required")


def _get_path(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _fmt_float(value: Any) -> str:
    return f"{float(value):.4f}"
