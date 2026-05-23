from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tradearena.core.trajectory import StepRecord, Trajectory
from tradearena.evaluation.submissions import validate_submission_file
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


def test_all_example_benchmark_submissions_match_schema_and_runtime_validator():
    validator = _validator("benchmark_submission.schema.json")

    for path in sorted((ROOT / "examples/benchmark_submissions").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        validator.validate(payload)
        _, errors = validate_submission_file(path)

        assert errors == [], path


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
