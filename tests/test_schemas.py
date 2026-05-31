from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

import scripts.validate_reproduction_report as reproduction_validator
from tradearena.core.domain import Order, Side
from tradearena.core.trajectory import StepRecord, Trajectory
from tradearena.evaluation.submissions import validate_submission_file
from tradearena.tools import (
    AlpacaPaperExportAdapter,
    BrokerAdapterMode,
    BrokerApproval,
    BrokerOrderStatus,
    BrokerResponse,
    build_broker_approval_artifact,
    write_broker_response_artifact,
)
from tradearena.tools.calibration import summarize_execution_calibration, summarize_quote_fill_calibration

ROOT = Path(__file__).resolve().parents[1]


def test_trajectory_schema_validates_serialized_trace():
    trajectory = Trajectory(experiment_name="schema-smoke", seed=1)
    trajectory.append(
        StepRecord(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            observation={"prices": {"SYN": 100.0}},
            signals=[],
            decisions=[],
            approved_decisions=[],
            orders=[],
            fills=[],
            portfolio={"cash": 100_000.0, "positions": {}, "equity": 100_000.0},
        )
    )
    payload = _json_round_trip(trajectory.to_dict())

    _validator("trajectory.schema.json").validate(payload)


def test_calibration_profile_schema_validates_ohlcv_diagnostic(tmp_path: Path):
    csv_path = tmp_path / "SYN_Daily.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Date,Open,High,Low,Close,Volume",
                "2026-01-01,100,102,99,101,1000",
                "2026-01-02,101,104,100,103,1200",
            ]
        ),
        encoding="utf-8",
    )
    summary = summarize_execution_calibration([csv_path])

    _validator("calibration_profile.schema.json").validate(summary)


def test_calibration_profile_schema_validates_quote_fill_profile():
    summary = summarize_quote_fill_calibration(
        ROOT / "data/public/microstructure_sample/quotes.csv",
        ROOT / "data/public/microstructure_sample/fills.csv",
    )

    _validator("calibration_profile.schema.json").validate(summary)


def test_benchmark_submission_schema_has_explicit_version_contract():
    schema = _load_schema("benchmark_submission.schema.json")

    assert schema["properties"]["schema_version"]["const"] == "0.1"
    Draft202012Validator.check_schema(schema)


def test_broker_response_artifact_schema_validates_writer_output(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-recon")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.FILLED,
                broker_order_id="paper-schema-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=1.0,
                fill_price=100.0,
                fees=0.01,
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    _validator("broker_response_artifact.schema.json").validate(payload)


def test_broker_handoff_artifact_schema_validates_writer_output(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))

    _validator("broker_handoff_artifact.schema.json").validate(payload)


def test_broker_approval_artifact_schema_validates_writer_output():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-001",
        account_mode="live",
        max_quantity=5.0,
    )

    _validator("broker_approval_artifact.schema.json").validate(payload)


def test_broker_approval_artifact_schema_rejects_malformed_request_hash():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-bad-hash-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash="sha256:demo-redacted-request-hash",
    )

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)

    assert errors
    assert list(errors[0].path) == ["request_artifact_hash"]


def test_all_example_benchmark_submissions_match_schema_and_runtime_validator():
    validator = _validator("benchmark_submission.schema.json")

    for path in sorted((ROOT / "examples/benchmark_submissions").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        validator.validate(payload)
        _, errors = validate_submission_file(path)

        assert errors == [], path


def test_reproduction_report_validator_rejects_failed_required_commands(tmp_path: Path):
    payload = _minimal_reproduction_report()
    payload["commands"][0]["returncode"] = 2
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    errors = reproduction_validator.validate_reproduction_report(payload)
    result = subprocess.run(
        [sys.executable, "scripts/validate_reproduction_report.py", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert "command trajectory returned 2" in errors
    assert result.returncode == 1
    assert "command trajectory returned 2" in result.stdout


def test_reproduction_report_validator_accepts_complete_manifest(tmp_path: Path):
    payload = _minimal_reproduction_report()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert reproduction_validator.validate_reproduction_report(payload) == []

    result = subprocess.run(
        [sys.executable, "scripts/validate_reproduction_report.py", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Valid reproduction report" in result.stdout


def test_reproduction_report_validator_has_no_dependency_fallback(monkeypatch):
    payload = _minimal_reproduction_report()
    monkeypatch.setattr(reproduction_validator, "Draft202012Validator", None)

    assert reproduction_validator.validate_reproduction_report(payload) == []

    broken = dict(payload)
    del broken["commands"]
    errors = reproduction_validator.validate_reproduction_report(broken)

    assert "missing required fields: commands" in errors

    malformed = _minimal_reproduction_report()
    malformed["commands"][0] = {"id": "trajectory"}
    errors = reproduction_validator.validate_reproduction_report(malformed)

    assert "commands[0] missing required fields: argv" in errors


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load_schema(schema_name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _load_schema(schema_name: str) -> dict[str, Any]:
    return json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))


def _json_round_trip(value: object) -> Any:
    return json.loads(json.dumps(value, default=_json_default))


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _minimal_reproduction_report() -> dict[str, Any]:
    return {
        "schema": "tradearena_external_reproduction_pack_v1",
        "created_at": "2026-05-23T00:00:00+00:00",
        "repository": "https://github.com/weich97/TradeArena",
        "commit_or_tag": "v0.2.0",
        "git_status_short": "",
        "python": {
            "version": "3.12.0",
            "implementation": "CPython",
            "executable": "python",
            "platform": "test",
        },
        "commands": [
            {
                "id": "trajectory",
                "description": "Generate trajectory",
                "argv": ["python", "examples/audit_trajectory_walkthrough.py"],
                "returncode": 0,
            }
        ],
        "artifacts": [
            {
                "path": "outputs/examples/audit_walkthrough_trajectory.json",
                "exists": True,
                "bytes": 100,
                "sha256": "sha256:" + "0" * 64,
            }
        ],
        "trajectory_hash": {
            "path": "outputs/examples/audit_walkthrough_trajectory.json",
            "file_sha256": "sha256:" + "1" * 64,
            "scenario_id": "audit_walkthrough",
            "reproducibility_hash": "sha256:" + "2" * 64,
        },
        "live_api_used": False,
        "market_data_used": "deterministic synthetic data",
        "private_fills_used": False,
    }
