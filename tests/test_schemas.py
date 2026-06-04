from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

import scripts.validate_reproduction_report as reproduction_validator
from tradearena.core.domain import Order, OrderType, Side
from tradearena.core.trajectory import StepRecord, Trajectory
from tradearena.evaluation.submissions import validate_submission_file
from tradearena.tools import (
    AlpacaPaperExportAdapter,
    BrokerAdapterMode,
    BrokerApproval,
    BrokerOrderStatus,
    BrokerResponse,
    BrokerSafetyConfig,
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
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
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


def test_broker_response_artifact_schema_rejects_malformed_timestamps(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-recon-time")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-schema-time-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["broker_timestamp"] = "June 2, 2026"

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "broker_timestamp") in paths


def test_broker_response_artifact_schema_rejects_nonpositive_submitted_quantity(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-recon-submitted")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                rejection_reason="paper account symbol permission mismatch",
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["submitted_quantity"] = 0.0

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "submitted_quantity") in paths


@pytest.mark.parametrize(
    ("status", "fill_quantity", "fill_price"),
    [
        (BrokerOrderStatus.ACCEPTED, None, None),
        (BrokerOrderStatus.PARTIALLY_FILLED, 0.5, 100.0),
        (BrokerOrderStatus.FILLED, 1.0, 100.0),
    ],
)
def test_broker_response_artifact_schema_rejects_nonpositive_accepted_quantity_for_active_statuses(
    tmp_path: Path,
    status: BrokerOrderStatus,
    fill_quantity: float | None,
    fill_price: float | None,
):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"schema-recon-accepted-{status.value}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=f"paper-schema-accepted-{status.value}",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=fill_quantity,
                fill_price=fill_price,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["accepted_quantity"] = 0.0

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "accepted_quantity") in paths


def test_broker_response_artifact_schema_rejects_empty_rejection_reason_for_rejected_status(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-recon-rejected-reason")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                rejection_reason="paper account symbol permission mismatch",
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["rejection_reason"] = ""

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "rejection_reason") in paths


def test_broker_response_artifact_schema_rejects_empty_reason_for_unknown_status(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-recon-unknown-reason")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.UNKNOWN,
                submitted_quantity=1.0,
                rejection_reason="broker response status could not be mapped",
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["rejection_reason"] = ""

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "rejection_reason") in paths


@pytest.mark.parametrize(
    ("status", "accepted_quantity", "fill_quantity", "fill_price"),
    [
        (BrokerOrderStatus.ACCEPTED, 1.0, None, None),
        (BrokerOrderStatus.PARTIALLY_FILLED, 1.0, 0.5, 100.0),
        (BrokerOrderStatus.FILLED, 1.0, 1.0, 100.0),
        (BrokerOrderStatus.CANCELED, None, None, None),
        (BrokerOrderStatus.EXPIRED, None, None, None),
    ],
)
def test_broker_response_artifact_schema_rejects_empty_broker_order_id_for_broker_statuses(
    tmp_path: Path,
    status: BrokerOrderStatus,
    accepted_quantity: float | None,
    fill_quantity: float | None,
    fill_price: float | None,
):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"schema-recon-broker-id-{status.value}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=f"paper-schema-broker-id-{status.value}",
                submitted_quantity=1.0,
                accepted_quantity=accepted_quantity,
                fill_quantity=fill_quantity,
                fill_price=fill_price,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["broker_order_id"] = ""

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "broker_order_id") in paths


@pytest.mark.parametrize(
    ("status", "fill_quantity"),
    [
        (BrokerOrderStatus.PARTIALLY_FILLED, 0.5),
        (BrokerOrderStatus.FILLED, 1.0),
    ],
)
def test_broker_response_artifact_schema_rejects_nonpositive_fill_quantity_for_fill_statuses(
    tmp_path: Path,
    status: BrokerOrderStatus,
    fill_quantity: float,
):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"schema-recon-fill-qty-{status.value}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=f"paper-schema-fill-qty-{status.value}",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=fill_quantity,
                fill_price=100.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["fill_quantity"] = 0.0

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "fill_quantity") in paths


@pytest.mark.parametrize(
    ("status", "fill_quantity"),
    [
        (BrokerOrderStatus.PARTIALLY_FILLED, 0.5),
        (BrokerOrderStatus.FILLED, 1.0),
    ],
)
def test_broker_response_artifact_schema_rejects_nonpositive_fill_price_for_fill_statuses(
    tmp_path: Path,
    status: BrokerOrderStatus,
    fill_quantity: float,
):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"schema-recon-fill-price-{status.value}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=f"paper-schema-fill-price-{status.value}",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=fill_quantity,
                fill_price=100.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["fill_price"] = 0.0

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "fill_price") in paths


@pytest.mark.parametrize(
    ("status", "broker_order_id", "accepted_quantity", "rejection_reason"),
    [
        (BrokerOrderStatus.ACCEPTED, "paper-schema-no-fill-accepted", 1.0, None),
        (
            BrokerOrderStatus.REJECTED,
            None,
            None,
            "paper account symbol permission mismatch",
        ),
    ],
)
def test_broker_response_artifact_schema_rejects_fill_quantity_for_nonfill_statuses(
    tmp_path: Path,
    status: BrokerOrderStatus,
    broker_order_id: str | None,
    accepted_quantity: float | None,
    rejection_reason: str | None,
):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"schema-recon-no-fill-qty-{status.value}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=broker_order_id,
                submitted_quantity=1.0,
                accepted_quantity=accepted_quantity,
                fill_quantity=None,
                fill_price=None,
                rejection_reason=rejection_reason,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["fill_quantity"] = 0.5

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "fill_quantity") in paths


@pytest.mark.parametrize(
    ("status", "broker_order_id", "accepted_quantity", "rejection_reason"),
    [
        (BrokerOrderStatus.ACCEPTED, "paper-schema-no-price-accepted", 1.0, None),
        (
            BrokerOrderStatus.REJECTED,
            None,
            None,
            "paper account symbol permission mismatch",
        ),
    ],
)
def test_broker_response_artifact_schema_rejects_fill_price_for_nonfill_statuses(
    tmp_path: Path,
    status: BrokerOrderStatus,
    broker_order_id: str | None,
    accepted_quantity: float | None,
    rejection_reason: str | None,
):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"schema-recon-no-fill-price-{status.value}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=broker_order_id,
                submitted_quantity=1.0,
                accepted_quantity=accepted_quantity,
                fill_quantity=None,
                fill_price=None,
                rejection_reason=rejection_reason,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["fill_price"] = 100.0

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "fill_price") in paths


@pytest.mark.parametrize(
    ("status", "field_name", "field_value", "broker_order_id", "rejection_reason"),
    [
        (BrokerOrderStatus.REJECTED, "accepted_quantity", 1.0, None, "broker rejected order"),
        (BrokerOrderStatus.REJECTED, "fees", 0.01, None, "broker rejected order"),
        (BrokerOrderStatus.UNKNOWN, "accepted_quantity", 1.0, None, "unmapped broker status"),
        (BrokerOrderStatus.UNKNOWN, "fill_quantity", 0.5, None, "unmapped broker status"),
        (BrokerOrderStatus.UNKNOWN, "fill_price", 100.0, None, "unmapped broker status"),
        (BrokerOrderStatus.UNKNOWN, "fees", 0.01, None, "unmapped broker status"),
        (BrokerOrderStatus.CANCELED, "fill_quantity", 0.5, "paper-canceled-schema", None),
        (BrokerOrderStatus.CANCELED, "fill_price", 100.0, "paper-canceled-schema", None),
        (BrokerOrderStatus.EXPIRED, "fill_quantity", 0.5, "paper-expired-schema", None),
        (BrokerOrderStatus.EXPIRED, "fill_price", 100.0, "paper-expired-schema", None),
    ],
)
def test_broker_response_artifact_schema_rejects_status_forbidden_positive_fields(
    tmp_path: Path,
    status: BrokerOrderStatus,
    field_name: str,
    field_value: float,
    broker_order_id: str | None,
    rejection_reason: str | None,
):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"schema-response-forbidden-{status.value}-{field_name}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=broker_order_id,
                submitted_quantity=1.0,
                accepted_quantity=None,
                fill_quantity=None,
                fill_price=None,
                fees=None,
                rejection_reason=rejection_reason,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0][field_name] = field_value

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, field_name) in paths


def test_broker_response_artifact_schema_rejects_live_flag_mismatch(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-recon-mismatch")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["live_submission"] = True

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("live_submission",) in paths


def test_broker_response_artifact_schema_requires_live_account_for_live_mode(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-recon-live-account")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="schema test")])
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[],
        output=output,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
        account_mode="live",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["account_mode"] = "paper"

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("account_mode",) in paths


def test_broker_response_artifact_schema_rejects_live_account_for_non_live_mode(tmp_path: Path):
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=[],
        responses=[],
        output=output,
        adapter="schema-paper-live-account",
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["account_mode"] = "live"

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("account_mode",) in paths


def test_broker_response_artifact_schema_rejects_unknown_account_mode(tmp_path: Path):
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=[],
        responses=[],
        output=output,
        adapter="schema-response-unknown-account",
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["account_mode"] = "simulation"

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("account_mode",) in paths


def test_broker_response_artifact_schema_rejects_row_account_mode_mismatch(tmp_path: Path):
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=[],
        responses=[
            BrokerResponse(
                client_order_id="schema-response-row-account-mode",
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-schema-row-account-mode-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=None,
                fill_price=None,
                fees=0.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=output,
        adapter="schema-response-row-account-mode",
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["account_mode"] = "none"

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "account_mode") in paths


def test_broker_response_artifact_schema_rejects_live_response_account_for_non_live_mode(tmp_path: Path):
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=[],
        responses=[
            BrokerResponse(
                client_order_id="paper-response-account-1",
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                rejection_reason="paper row in paper artifact",
                account_mode="paper",
            )
        ],
        output=output,
        adapter="schema-paper-response-account",
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["account_mode"] = "live"

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "account_mode") in paths


def test_broker_response_artifact_schema_requires_live_response_accounts_for_live_mode(tmp_path: Path):
    output = tmp_path / "broker_response_artifact.json"
    write_broker_response_artifact(
        requests=[],
        responses=[
            BrokerResponse(
                client_order_id="live-response-account-1",
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                rejection_reason="paper row in live artifact",
                account_mode="live",
            )
        ],
        output=output,
        adapter="schema-live-response-account",
        adapter_mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
        account_mode="live",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["responses"][0]["account_mode"] = "paper"

    errors = sorted(_validator("broker_response_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("responses", 0, "account_mode") in paths


def test_broker_handoff_artifact_schema_validates_writer_output(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))

    _validator("broker_handoff_artifact.schema.json").validate(payload)


def test_broker_handoff_artifact_schema_rejects_mode_flag_mismatch(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff-mismatch")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["live_submission"] = True
    payload["orders"][0]["submit_live"] = True

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("live_submission",) in paths
    assert ("orders", 0, "submit_live") in paths


def test_broker_handoff_artifact_schema_rejects_order_adapter_mode_mismatch(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff-order-mode")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["orders"][0]["adapter_mode"] = "live_human_approved"
    payload["orders"][0]["account_mode"] = "live"
    payload["orders"][0]["submit_live"] = True
    payload["orders"][0]["approval_status"] = "approved"

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("orders", 0, "adapter_mode") in paths


def test_broker_handoff_artifact_schema_rejects_limit_order_without_limit_price(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff-limit-price")
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="schema test")],
        tmp_path,
    )
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["orders"][0]["limit_price"] = None

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("orders", 0, "limit_price") in paths


def test_broker_handoff_artifact_schema_rejects_market_order_with_limit_price(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff-market-price")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["orders"][0]["limit_price"] = 100.0

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("orders", 0, "limit_price") in paths


def test_broker_handoff_artifact_schema_rejects_unsupported_time_in_force(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff-tif")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["orders"][0]["time_in_force"] = "banana"

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("orders", 0, "time_in_force") in paths


def test_broker_handoff_artifact_schema_requires_live_account_for_live_mode(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-live-handoff-account")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["adapter_mode"] = "live_human_approved"
    payload["account_mode"] = "paper"
    payload["paper_only"] = False
    payload["live_submission"] = True
    payload["manual_approval_required"] = False
    payload["orders"][0]["adapter_mode"] = "live_human_approved"
    payload["orders"][0]["account_mode"] = "paper"
    payload["orders"][0]["submit_live"] = True
    payload["orders"][0]["approval_status"] = "approved"

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("account_mode",) in paths
    assert ("orders", 0, "account_mode") in paths


def test_broker_handoff_artifact_schema_rejects_live_account_for_non_live_mode(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff-paper-live-account")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["account_mode"] = "live"
    payload["orders"][0]["account_mode"] = "live"

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("account_mode",) in paths
    assert ("orders", 0, "account_mode") in paths


def test_broker_handoff_artifact_schema_rejects_unknown_account_mode(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-handoff-unknown-account")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["account_mode"] = "simulation"

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("account_mode",) in paths


def test_broker_handoff_artifact_schema_rejects_order_account_mode_mismatch(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(
        client_prefix="schema-handoff-row-account-mode",
        safety=BrokerSafetyConfig(account_mode="paper"),
    )
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["orders"][0]["account_mode"] = "none"

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("orders", 0, "account_mode") in paths


def test_broker_handoff_artifact_schema_rejects_live_kill_switch(tmp_path: Path):
    adapter = AlpacaPaperExportAdapter(client_prefix="schema-live-kill-switch")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="schema test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))
    payload["adapter_mode"] = "live_human_approved"
    payload["account_mode"] = "live"
    payload["paper_only"] = False
    payload["live_submission"] = True
    payload["manual_approval_required"] = False
    payload["kill_switch"] = True
    payload["orders"][0]["adapter_mode"] = "live_human_approved"
    payload["orders"][0]["account_mode"] = "live"
    payload["orders"][0]["submit_live"] = True
    payload["orders"][0]["approval_status"] = "approved"

    errors = sorted(_validator("broker_handoff_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("kill_switch",) in paths


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
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )

    _validator("broker_approval_artifact.schema.json").validate(payload)


def test_broker_approval_artifact_schema_requires_request_hash_binding():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-unbound-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )
    payload["request_artifact_hash"] = None

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("request_artifact_hash",) in paths


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
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )
    payload["request_artifact_hash"] = "sha256:demo-redacted-request-hash"

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)

    assert errors
    assert list(errors[0].path) == ["request_artifact_hash"]


def test_broker_approval_artifact_schema_rejects_malformed_timestamps():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-bad-time-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )
    payload["approved_at"] = "May 31, noon"
    payload["expires_at"] = "tomorrow"

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("approved_at",) in paths
    assert ("expires_at",) in paths


def test_broker_approval_artifact_schema_requires_expiry():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-null-expiry-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )
    payload["expires_at"] = None

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert ("expires_at",) in paths


def test_broker_approval_artifact_schema_requires_live_account_mode():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-paper-account-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )
    payload["account_mode"] = "paper"

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)

    assert errors
    assert list(errors[0].path) == ["account_mode"]


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_path"),
    [
        ("approval_id", "   ", ("approval_id",)),
        ("approved_by", "   ", ("approved_by",)),
        ("approval_reason", "   ", ("approval_reason",)),
        ("allowed_symbols", ["   "], ("allowed_symbols", 0)),
    ],
)
def test_broker_approval_artifact_schema_rejects_blank_text_fields(
    field_name: str, field_value: object, expected_path: tuple[object, ...]
):
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-blank-text-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )
    payload[field_name] = field_value

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert expected_path in paths


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("allowed_symbols", ["AAPL", "AAPL"]),
        ("allowed_order_types", ["market", "market"]),
    ],
)
def test_broker_approval_artifact_schema_rejects_duplicate_scopes(field_name: str, field_value: list[str]):
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=2500.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-schema-duplicate-scope-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash="sha256:" + "1" * 64,
    )
    payload[field_name] = field_value

    errors = sorted(_validator("broker_approval_artifact.schema.json").iter_errors(payload), key=lambda err: err.path)
    paths = {tuple(error.path) for error in errors}

    assert (field_name,) in paths


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


def test_reproduction_report_validator_reports_malformed_json(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text('{"schema": ', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/validate_reproduction_report.py", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Invalid reproduction report" in result.stdout
    assert "reproduction report must contain valid JSON" in result.stdout
    assert "Traceback" not in result.stderr


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
