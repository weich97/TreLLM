from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

from tradearena.core.domain import Order, OrderType, Side
from tradearena.factory import build_default_system, default_registry
from tradearena.planning import load_holdings_csv
from tradearena.tools import (
    AlpacaPaperExportAdapter,
    BrokerAdapter,
    BrokerAdapterContractError,
    BrokerAdapterMode,
    BrokerApproval,
    BrokerOrderStatus,
    BrokerResponse,
    BrokerSafetyConfig,
    DryRunBrokerAdapter,
    FuturesContractMetadata,
    FuturesRollRiskEngine,
    broker_approval_from_artifact,
    broker_handoff_artifact_hash,
    broker_safety_from_approval_artifact,
    build_broker_approval_artifact,
    reconcile_broker_responses,
    validate_broker_approval_artifact,
    validate_broker_approval_artifact_file,
    validate_broker_approval_request_binding,
    validate_broker_handoff_artifact,
    validate_broker_handoff_artifact_file,
    validate_broker_response_artifact,
    validate_broker_response_artifact_file,
    write_broker_response_artifact,
)

ROOT = Path(__file__).resolve().parents[1]


def test_alpaca_paper_export_adapter_requires_human_approval(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="unit")
    result = adapter.write([Order("AAPL", Side.BUY, 3.5, reason="unit test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))

    assert result["order_count"] == 1
    assert payload["schema"] == "tradearena_broker_handoff_artifact_v0.1"
    assert payload["adapter_mode"] == "offline_export"
    assert payload["account_mode"] == "none"
    assert payload["live_submission"] is False
    assert payload["manual_approval_required"] is True
    assert payload["orders"][0]["adapter_mode"] == "offline_export"
    assert payload["orders"][0]["approval_status"] == "requires_human_approval"
    assert validate_broker_handoff_artifact(payload) == []


def test_broker_handoff_artifact_validator_and_cli_reject_mode_mismatch(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="handoff-validate")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path)
    artifact = tmp_path / "alpaca_paper_orders.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-broker-handoff", str(artifact)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/validate_broker_handoff_artifact.py", str(artifact)],
        cwd=ROOT,
        check=True,
    )

    payload["orders"][0]["submit_live"] = True
    broken = tmp_path / "broken_alpaca_paper_orders.json"
    broken.write_text(json.dumps(payload), encoding="utf-8")
    errors = validate_broker_handoff_artifact(payload)
    result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-broker-handoff", str(broken)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert "orders[0].submit_live must match live_human_approved mode" in errors
    assert result.returncode == 1
    assert "orders[0].submit_live must match live_human_approved mode" in result.stdout


def test_broker_handoff_artifact_rejects_order_account_mode_mismatch(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="handoff-account-mode")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path)
    artifact = tmp_path / "alpaca_paper_orders.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["account_mode"] = "paper"
    payload["orders"][0]["account_mode"] = "live"

    errors = validate_broker_handoff_artifact(payload)

    assert "orders[0].account_mode must match artifact account_mode" in errors


def test_broker_handoff_artifact_rejects_limit_order_without_limit_price(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="handoff-limit-price")
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="unit test")],
        tmp_path,
    )
    artifact = tmp_path / "alpaca_paper_orders.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["orders"][0]["limit_price"] = None

    errors = validate_broker_handoff_artifact(payload)

    assert "orders[0].limit orders require a positive limit_price" in errors


def test_broker_handoff_artifact_rejects_market_order_with_limit_price(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="handoff-market-price")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path)
    artifact = tmp_path / "alpaca_paper_orders.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["orders"][0]["limit_price"] = 100.0

    errors = validate_broker_handoff_artifact(payload)

    assert "orders[0].market orders must not include limit_price" in errors


def test_broker_handoff_artifact_rejects_nonfinite_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="handoff-nonfinite")
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path)
    artifact = tmp_path / "alpaca_paper_orders.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["orders"][0]["quantity"] = float("nan")

    errors = validate_broker_handoff_artifact(payload)

    assert "orders[0].quantity must be a positive finite number" in errors


def test_broker_safety_config_blocks_disallowed_orders(tmp_path):
    adapter = AlpacaPaperExportAdapter(
        safety=BrokerSafetyConfig(
            allowed_symbols=("MSFT",),
            max_quantity=2.0,
        )
    )

    try:
        adapter.write([Order("AAPL", Side.BUY, 3.5, reason="unit test")], tmp_path)
    except BrokerAdapterContractError as exc:
        assert "allow-list" in str(exc)
    else:
        raise AssertionError("expected broker adapter allow-list failure")


def test_broker_safety_config_requires_reference_price_for_market_notional_limit(tmp_path):
    adapter = AlpacaPaperExportAdapter(
        safety=BrokerSafetyConfig(
            account_mode="paper",
            max_notional=100.0,
            max_quantity=10.0,
        )
    )

    try:
        adapter.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path)
    except BrokerAdapterContractError as exc:
        assert "reference_price" in str(exc)
    else:
        raise AssertionError("expected reference price failure for max_notional market order")


def test_dry_run_broker_adapter_writes_validated_handoff_without_live_submission(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="dry-unit",
        safety=BrokerSafetyConfig(
            account_mode="paper",
            max_quantity=2.0,
            allowed_symbols=("AAPL",),
        ),
    )
    assert isinstance(adapter, BrokerAdapter)

    result = adapter.write([Order("AAPL", Side.BUY, 1.25, reason="dry run unit")], tmp_path)
    payload = json.loads((tmp_path / "dry_run_orders.json").read_text(encoding="utf-8"))

    assert result["order_count"] == 1
    assert result["adapter_mode"] == "dry_run"
    assert result["paper_only"] is True
    assert payload["adapter"] == "dry-run-broker-adapter"
    assert payload["adapter_mode"] == "dry_run"
    assert payload["live_submission"] is False
    assert payload["orders"][0]["submit_live"] is False
    assert validate_broker_handoff_artifact(payload) == []


def test_live_human_approved_mode_requires_approval_and_marks_live(tmp_path):
    missing_limits = AlpacaPaperExportAdapter(
        safety=BrokerSafetyConfig(mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED)
    )
    try:
        missing_limits.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path / "limits")
    except BrokerAdapterContractError as exc:
        assert "max_notional and max_quantity" in str(exc)
    else:
        raise AssertionError("expected missing live limit failure")

    missing_approval = AlpacaPaperExportAdapter(
        safety=BrokerSafetyConfig(
            mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
            max_notional=1000.0,
            max_quantity=10.0,
        )
    )
    try:
        missing_approval.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path / "missing")
    except BrokerAdapterContractError as exc:
        assert "approved human approval record" in str(exc)
    else:
        raise AssertionError("expected missing approval failure")

    approved = AlpacaPaperExportAdapter(
        safety=BrokerSafetyConfig(
            mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
            account_mode="live",
            max_notional=1000.0,
            max_quantity=10.0,
            approval=BrokerApproval(
                approval_status="approved",
                approved_by="unit-operator",
                approved_at="2026-05-31T12:00:00Z",
                max_notional=100.0,
                allowed_symbols=("AAPL",),
                approval_reason="unit test approval",
            ),
        )
    )
    try:
        approved.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path / "no-reference-price")
    except BrokerAdapterContractError as exc:
        assert "reference_price" in str(exc)
    else:
        raise AssertionError("expected live order reference price failure")

    too_large_for_approval = Order(
        "AAPL",
        Side.BUY,
        1.0,
        order_type=OrderType.LIMIT,
        limit_price=200.0,
        reason="unit test",
    )
    try:
        approved.write([too_large_for_approval], tmp_path / "approval-notional")
    except BrokerAdapterContractError as exc:
        assert "approval max_notional" in str(exc)
    else:
        raise AssertionError("expected approval max_notional failure")

    approved.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=50.0, reason="unit test")],
        tmp_path / "approved",
    )
    payload = json.loads((tmp_path / "approved" / "alpaca_paper_orders.json").read_text(encoding="utf-8"))

    assert payload["adapter_mode"] == "live_human_approved"
    assert payload["account_mode"] == "live"
    assert payload["live_submission"] is True
    assert payload["manual_approval_required"] is False
    assert payload["orders"][0]["approval_status"] == "approved"


def test_live_human_approved_handoff_requires_live_account_mode(tmp_path):
    adapter = AlpacaPaperExportAdapter(
        safety=BrokerSafetyConfig(
            mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
            account_mode="paper",
            max_notional=1000.0,
            max_quantity=10.0,
            approval=BrokerApproval(
                approval_status="approved",
                approved_by="unit-operator",
                approved_at="2026-05-31T12:00:00Z",
                max_notional=1000.0,
                allowed_symbols=("AAPL",),
                approval_reason="unit test approval",
            ),
        )
    )

    try:
        adapter.write(
            [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=50.0, reason="unit test")],
            tmp_path,
        )
    except BrokerAdapterContractError as exc:
        assert "live_human_approved mode requires account_mode live" in str(exc)
    else:
        raise AssertionError("expected live account_mode failure")

    payload = {
        "schema": "tradearena_broker_handoff_artifact_v0.1",
        "adapter": "live-unit-adapter",
        "adapter_mode": "live_human_approved",
        "account_mode": "paper",
        "paper_only": False,
        "live_submission": True,
        "manual_approval_required": False,
        "kill_switch": False,
        "orders": [],
    }

    assert "account_mode must be live for live_human_approved broker handoff artifacts" in validate_broker_handoff_artifact(
        payload
    )


def test_broker_response_artifact_summarizes_reconciliation(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="recon")
    requests = adapter.convert(
        [
            Order("AAPL", Side.BUY, 2.0, reason="unit test"),
            Order("MSFT", Side.SELL, 1.0, reason="unit test"),
        ]
    )
    responses = [
        BrokerResponse(
            client_order_id=requests[0].client_order_id,
            status=BrokerOrderStatus.PARTIALLY_FILLED,
            broker_order_id="paper-1",
            submitted_quantity=2.0,
            accepted_quantity=2.0,
            fill_quantity=1.0,
            fill_price=190.0,
            fees=0.02,
            account_mode="paper",
        ),
        BrokerResponse(
            client_order_id="unknown-order",
            status=BrokerOrderStatus.REJECTED,
            submitted_quantity=1.0,
            rejection_reason="symbol not enabled",
            account_mode="paper",
        ),
    ]

    summary = reconcile_broker_responses(requests, responses)
    assert summary.response_count == 2
    assert summary.partial_fill_count == 1
    assert summary.rejected_count == 1
    assert summary.unmatched_response_count == 1
    assert summary.missing_response_count == 1
    assert summary.fill_ratio_mean == 0.5

    artifact = tmp_path / "broker_response.json"
    result = write_broker_response_artifact(
        requests=requests,
        responses=responses,
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert result["response_count"] == 2
    assert payload["schema"] == "tradearena_broker_response_artifact_v0.1"
    assert payload["live_submission"] is False
    assert payload["reconciliation"]["missing_response_count"] == 1
    assert payload["responses"][0]["status"] == "partially_filled"


def test_broker_response_artifact_writer_emits_validator_clean_defaults(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="writer-defaults")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"

    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                rejection_reason="paper sandbox rejected order",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert validate_broker_response_artifact(payload) == []


def test_broker_response_artifact_writer_rejects_submitted_quantity_mismatch(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-request-quantity")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])

    try:
        write_broker_response_artifact(
            requests=requests,
            responses=[
                BrokerResponse(
                    client_order_id=requests[0].client_order_id,
                    status=BrokerOrderStatus.REJECTED,
                    submitted_quantity=2.0,
                    rejection_reason="broker reported a different submitted quantity",
                    account_mode="paper",
                )
            ],
            output=tmp_path / "broker_response.json",
            adapter=adapter.name,
            adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
            account_mode="paper",
        )
    except BrokerAdapterContractError as exc:
        assert "submitted_quantity 2.0 does not match request quantity 1.0" in str(exc)
    else:
        raise AssertionError("expected submitted quantity mismatch failure")


def test_broker_response_artifact_writer_rejects_account_mode_mismatch(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-account-binding")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])

    try:
        write_broker_response_artifact(
            requests=requests,
            responses=[
                BrokerResponse(
                    client_order_id=requests[0].client_order_id,
                    status=BrokerOrderStatus.REJECTED,
                    submitted_quantity=1.0,
                    rejection_reason="broker account mismatch",
                    account_mode="live",
                )
            ],
            output=tmp_path / "broker_response.json",
            adapter=adapter.name,
            adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
            account_mode="paper",
        )
    except BrokerAdapterContractError as exc:
        assert "responses[0].account_mode live does not match artifact account_mode paper" in str(exc)
    else:
        raise AssertionError("expected response account_mode mismatch failure")


def test_broker_response_artifact_writer_requires_live_account_for_live_mode(tmp_path):
    try:
        write_broker_response_artifact(
            requests=[],
            responses=[],
            output=tmp_path / "broker_response.json",
            adapter="live-writer-unit",
            adapter_mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
            account_mode="paper",
        )
    except BrokerAdapterContractError as exc:
        assert "live_human_approved response artifacts require account_mode live" in str(exc)
    else:
        raise AssertionError("expected live response account_mode failure")


def test_broker_response_artifact_validator_and_cli_reject_count_mismatch(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="validate-recon")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.FILLED,
                broker_order_id="paper-filled-count-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=1.0,
                fill_price=190.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert validate_broker_response_artifact(payload) == []
    subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-broker-response", str(artifact)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/validate_broker_response_artifact.py", str(artifact)],
        cwd=ROOT,
        check=True,
    )

    payload["reconciliation"]["filled_count"] = 0
    broken = tmp_path / "broken_broker_response.json"
    broken.write_text(json.dumps(payload), encoding="utf-8")
    errors = validate_broker_response_artifact(payload)
    result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-broker-response", str(broken)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert "reconciliation.filled_count must be 1; got 0" in errors
    assert result.returncode == 1
    assert "reconciliation.filled_count must be 1; got 0" in result.stdout


def test_broker_response_artifact_rejects_impossible_fill_quantities(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-quantity")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.PARTIALLY_FILLED,
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=2.0,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].fill_quantity cannot exceed submitted_quantity" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_rejects_impossible_accepted_quantities(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-accepted-quantity")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                submitted_quantity=1.0,
                accepted_quantity=2.0,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].accepted_quantity cannot exceed submitted_quantity" in validate_broker_response_artifact(
        payload
    )


def test_broker_response_artifact_rejects_fill_exceeding_accepted_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-fill-vs-accepted")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.PARTIALLY_FILLED,
                submitted_quantity=1.0,
                accepted_quantity=0.5,
                fill_quantity=1.0,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].fill_quantity cannot exceed accepted_quantity" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_rejects_rejection_without_reason(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-rejection-reason")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                rejection_reason=None,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].rejection_reason must be non-empty for rejected responses" in validate_broker_response_artifact(
        payload
    )


def test_broker_response_artifact_rejects_partial_fill_with_full_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-partial-full")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.PARTIALLY_FILLED,
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=1.0,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].partial fill_quantity must be less than submitted_quantity" in validate_broker_response_artifact(
        payload
    )


def test_broker_response_artifact_rejects_filled_without_fill_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-filled-quantity")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.FILLED,
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=None,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].filled responses require a positive fill_quantity" in validate_broker_response_artifact(
        payload
    )


def test_broker_response_artifact_rejects_filled_with_partial_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-filled-partial")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.FILLED,
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=0.5,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].filled fill_quantity must equal submitted_quantity" in validate_broker_response_artifact(
        payload
    )


@pytest.mark.parametrize(
    "status",
    [BrokerOrderStatus.PARTIALLY_FILLED, BrokerOrderStatus.FILLED],
)
def test_broker_response_artifact_rejects_fills_without_fill_price(tmp_path, status):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"response-{status.value}-price")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=0.5 if status is BrokerOrderStatus.PARTIALLY_FILLED else 1.0,
                fill_price=None,
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].filled or partially_filled responses require a positive fill_price" in (
        validate_broker_response_artifact(payload)
    )


@pytest.mark.parametrize("field_name", ["submitted_at", "broker_timestamp"])
def test_broker_response_artifact_rejects_malformed_timestamps(tmp_path, field_name):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"response-{field_name}")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    response = BrokerResponse(
        client_order_id=requests[0].client_order_id,
        status=BrokerOrderStatus.ACCEPTED,
        submitted_quantity=1.0,
        accepted_quantity=1.0,
        submitted_at="2026-06-02T09:30:00Z",
        broker_timestamp="2026-06-02T09:30:01Z",
        account_mode="paper",
    )
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[response],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["responses"][0][field_name] = "June 2, 2026"

    assert f"responses[0].{field_name} must be an ISO timestamp with timezone" in (
        validate_broker_response_artifact(payload)
    )


def test_broker_response_artifact_rejects_duplicate_client_order_ids(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-duplicate-id")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-duplicate-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            ),
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-duplicate-2",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:02Z",
                broker_timestamp="2026-06-02T09:30:03Z",
                account_mode="paper",
            ),
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[1].client_order_id duplicates an earlier response" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_requires_broker_order_id_for_accepted_responses(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-broker-order-id")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id=None,
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].broker_order_id must be non-empty for accepted broker responses" in (
        validate_broker_response_artifact(payload)
    )


def test_broker_response_artifact_rejects_duplicate_broker_order_ids(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-duplicate-broker-id")
    requests = adapter.convert(
        [
            Order("AAPL", Side.BUY, 1.0, reason="unit test"),
            Order("MSFT", Side.BUY, 1.0, reason="unit test"),
        ]
    )
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-duplicate-broker-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            ),
            BrokerResponse(
                client_order_id=requests[1].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-duplicate-broker-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:02Z",
                broker_timestamp="2026-06-02T09:30:03Z",
                account_mode="paper",
            ),
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[1].broker_order_id duplicates an earlier response" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_rejects_row_account_mode_mismatch(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-account-mode")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-account-mode-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["responses"][0]["account_mode"] = "live"

    assert "responses[0].account_mode must match artifact account_mode" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_rejects_broker_timestamp_before_submission(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-time-order")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-time-order-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                submitted_at="2026-06-02T09:30:01Z",
                broker_timestamp="2026-06-02T09:30:00Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].broker_timestamp must be at or after submitted_at" in validate_broker_response_artifact(
        payload
    )


def test_broker_response_artifact_rejects_filled_without_accepted_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-filled-accepted")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.FILLED,
                broker_order_id="paper-filled-accepted-1",
                submitted_quantity=1.0,
                accepted_quantity=None,
                fill_quantity=1.0,
                fill_price=190.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].filled responses require a positive accepted_quantity" in validate_broker_response_artifact(
        payload
    )


@pytest.mark.parametrize(
    "status",
    [BrokerOrderStatus.ACCEPTED, BrokerOrderStatus.PARTIALLY_FILLED],
)
def test_broker_response_artifact_rejects_active_status_without_accepted_quantity(tmp_path, status):
    adapter = AlpacaPaperExportAdapter(client_prefix=f"response-{status.value}-accepted")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=status,
                broker_order_id=f"paper-{status.value}-accepted-1",
                submitted_quantity=1.0,
                accepted_quantity=None,
                fill_quantity=0.5 if status is BrokerOrderStatus.PARTIALLY_FILLED else None,
                fill_price=190.0 if status is BrokerOrderStatus.PARTIALLY_FILLED else None,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert f"responses[0].{status.value} responses require a positive accepted_quantity" in (
        validate_broker_response_artifact(payload)
    )


def test_broker_response_artifact_rejects_accepted_status_with_fill_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-accepted-with-fill")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-accepted-fill-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=0.5,
                fill_price=190.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].accepted responses must not report fill_quantity" in validate_broker_response_artifact(
        payload
    )


def test_broker_response_artifact_rejects_accepted_status_with_fill_price(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-accepted-with-price")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.ACCEPTED,
                broker_order_id="paper-accepted-price-1",
                submitted_quantity=1.0,
                accepted_quantity=1.0,
                fill_quantity=None,
                fill_price=190.0,
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].accepted responses must not report fill_price" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_rejects_rejected_status_with_fill_quantity(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-rejected-with-fill")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                fill_quantity=0.5,
                rejection_reason="paper account symbol permission mismatch",
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].rejected responses must not report fill_quantity" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_rejects_rejected_status_with_fill_price(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-rejected-with-price")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=1.0,
                fill_price=190.0,
                rejection_reason="paper account symbol permission mismatch",
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].rejected responses must not report fill_price" in validate_broker_response_artifact(payload)


@pytest.mark.parametrize("submitted_quantity", [None, 0.0])
def test_broker_response_artifact_rejects_missing_or_zero_submitted_quantity(tmp_path, submitted_quantity):
    adapter = AlpacaPaperExportAdapter(client_prefix="response-submitted-quantity")
    requests = adapter.convert([Order("AAPL", Side.BUY, 1.0, reason="unit test")])
    artifact = tmp_path / "broker_response.json"
    write_broker_response_artifact(
        requests=requests,
        responses=[
            BrokerResponse(
                client_order_id=requests[0].client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_quantity=submitted_quantity,
                rejection_reason="paper account symbol permission mismatch",
                submitted_at="2026-06-02T09:30:00Z",
                broker_timestamp="2026-06-02T09:30:01Z",
                account_mode="paper",
            )
        ],
        output=artifact,
        adapter=adapter.name,
        adapter_mode=BrokerAdapterMode.PAPER_SANDBOX,
        account_mode="paper",
    )
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert "responses[0].submitted_quantity must be a positive number" in validate_broker_response_artifact(payload)


def test_broker_response_artifact_rejects_live_mode_with_paper_account():
    payload = {
        "schema": "tradearena_broker_response_artifact_v0.1",
        "adapter": "live-unit-adapter",
        "adapter_mode": "live_human_approved",
        "account_mode": "paper",
        "live_submission": True,
        "reconciliation": {
            "response_count": 0,
            "accepted_count": 0,
            "rejected_count": 0,
            "partial_fill_count": 0,
            "filled_count": 0,
            "canceled_count": 0,
            "expired_count": 0,
            "unknown_count": 0,
            "unmatched_response_count": 0,
            "missing_response_count": 0,
            "fill_ratio_mean": None,
        },
        "responses": [],
    }

    assert "account_mode must be live for live_human_approved broker response artifacts" in validate_broker_response_artifact(
        payload
    )


def test_broker_approval_artifact_validator_and_cli_reject_unredacted_operator(tmp_path):
    approval = BrokerApproval(
        approval_status="approved",
        approved_by="operator-7",
        approved_at="2026-05-31T12:00:00Z",
        max_notional=2500.0,
        allowed_symbols=("AAPL", "MSFT"),
        approval_reason="paper shadow checks passed",
    )
    payload = build_broker_approval_artifact(
        approval,
        approval_id="approval-unit-001",
        account_mode="live",
        max_quantity=5.0,
        allowed_order_types=(OrderType.MARKET, OrderType.LIMIT),
        expires_at="2026-05-31T13:00:00Z",
    )
    artifact = tmp_path / "broker_approval.json"
    artifact.write_text(json.dumps(payload), encoding="utf-8")

    assert validate_broker_approval_artifact(payload) == []
    subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-broker-approval", str(artifact)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/validate_broker_approval_artifact.py", str(artifact)],
        cwd=ROOT,
        check=True,
    )

    payload["approved_by"] = "operator@example.com"
    broken = tmp_path / "broken_broker_approval.json"
    broken.write_text(json.dumps(payload), encoding="utf-8")
    errors = validate_broker_approval_artifact(payload)
    result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "validate-broker-approval", str(broken)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert "approved_by must be a redacted operator id, not an email address" in errors
    assert result.returncode == 1
    assert "approved_by must be a redacted operator id, not an email address" in result.stdout


def test_broker_approval_artifact_requires_live_account_mode():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-paper-account-001",
        account_mode="paper",
        max_quantity=5.0,
    )

    assert "account_mode must be live for broker approval artifacts" in validate_broker_approval_artifact(payload)


def test_broker_approval_artifact_builds_live_safety_config(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-safety",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL", "MSFT")),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 2.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="approved")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL", "MSFT"),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-safety-001",
        account_mode="live",
        max_quantity=5.0,
        allowed_order_types=(OrderType.LIMIT,),
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )

    approval = broker_approval_from_artifact(payload)
    safety = broker_safety_from_approval_artifact(payload, request_artifact=request_path)

    assert approval.allowed_symbols == ("AAPL", "MSFT")
    assert safety.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED
    assert safety.account_mode == "live"
    assert safety.max_notional == 250.0
    assert safety.max_quantity == 5.0
    assert safety.allowed_order_types == (OrderType.LIMIT,)
    safety.validate_order(
        Order("AAPL", Side.BUY, 2.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="approved"),
        reference_price=100.0,
    )

    try:
        safety.validate_order(
            Order("AAPL", Side.BUY, 3.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="too large"),
            reference_price=100.0,
        )
    except BrokerAdapterContractError as exc:
        assert (
            "does not match an approved broker handoff order" in str(exc)
            or "approved broker handoff order count 0" in str(exc)
        )
    else:
        raise AssertionError("expected unreviewed-order failure from approval artifact safety")


def test_broker_safety_from_approval_artifact_requires_reviewed_request_artifact():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-unbound-safety-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash="sha256:" + "1" * 64,
    )

    try:
        broker_safety_from_approval_artifact(payload)
    except BrokerAdapterContractError as exc:
        assert "request_artifact is required to build live safety from a broker approval artifact" in str(exc)
    else:
        raise AssertionError("expected unbound live safety creation to be rejected")


def test_broker_approval_artifact_rejects_expired_approval():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-expired-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
    )

    errors = validate_broker_approval_artifact(payload, now="2026-05-31T14:00:00Z")
    assert "approval artifact is expired" in errors
    try:
        broker_safety_from_approval_artifact(payload, now="2026-05-31T14:00:00Z")
    except BrokerAdapterContractError as exc:
        assert "approval artifact is expired" in str(exc)
    else:
        raise AssertionError("expected expired approval artifact failure")


def test_broker_approval_validator_cli_and_script_reject_expired_approval_with_now(tmp_path):
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-expired-command-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
    )
    artifact = tmp_path / "broker_approval.json"
    artifact.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tradearena.cli",
            "validate-broker-approval",
            str(artifact),
            "--now",
            "2026-05-31T14:00:00Z",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    script_result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_broker_approval_artifact.py",
            str(artifact),
            "--now",
            "2026-05-31T14:00:00Z",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert script_result.returncode == 1
    assert "approval artifact is expired" in result.stdout
    assert "approval artifact is expired" in script_result.stdout


def test_broker_approval_validator_cli_rejects_malformed_now_even_without_expiry(tmp_path):
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-bad-now-001",
        account_mode="live",
        max_quantity=5.0,
    )
    artifact = tmp_path / "broker_approval.json"
    artifact.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tradearena.cli",
            "validate-broker-approval",
            str(artifact),
            "--now",
            "not-a-time",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "now must be an ISO timestamp" in result.stdout


def test_broker_approval_artifact_rejects_malformed_timestamps():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="May 31, noon",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-bad-time-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="tomorrow",
    )

    errors = validate_broker_approval_artifact(payload)
    assert "approved_at must be an ISO timestamp with timezone" in errors
    assert "expires_at must be an ISO timestamp with timezone or null" in errors


def test_broker_approval_artifact_rejects_expiry_before_approval_time():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-reversed-window-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T11:59:59Z",
    )

    assert "expires_at must be after approved_at" in validate_broker_approval_artifact(payload)


def test_broker_approval_artifact_rejects_malformed_request_hash():
    payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-bad-hash-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash="sha256:demo-redacted-request-hash",
    )

    assert validate_broker_approval_artifact(payload) == [
        "request_artifact_hash must be sha256:<64 lowercase hex chars> or null"
    ]


def test_broker_artifact_file_validators_report_malformed_json(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text('{"schema": ', encoding="utf-8")

    for validator in (
        validate_broker_handoff_artifact_file,
        validate_broker_approval_artifact_file,
        validate_broker_response_artifact_file,
    ):
        payload, errors = validator(broken)

        assert payload == {}
        assert errors == ["broker artifact file must contain valid JSON"]


def test_broker_artifact_validator_scripts_report_malformed_json(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text('{"schema": ', encoding="utf-8")

    for script in (
        "scripts/validate_broker_handoff_artifact.py",
        "scripts/validate_broker_approval_artifact.py",
        "scripts/validate_broker_response_artifact.py",
    ):
        result = subprocess.run(
            [sys.executable, script, str(broken)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "broker artifact file must contain valid JSON" in result.stdout
        assert "Traceback" not in result.stderr


def test_broker_handoff_hash_helper_reports_malformed_json_path(tmp_path):
    broken = tmp_path / "broken_handoff.json"
    broken.write_text('{"schema": ', encoding="utf-8")

    try:
        broker_handoff_artifact_hash(broken)
    except BrokerAdapterContractError as exc:
        assert str(exc) == "broker artifact file must contain valid JSON"
    else:
        raise AssertionError("malformed broker handoff JSON was hashed")


def test_broker_approval_artifact_binds_to_handoff_request_hash(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-bind",
        safety=BrokerSafetyConfig(
            account_mode="paper",
            max_quantity=5.0,
            allowed_symbols=("AAPL",),
        ),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 2.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="binding unit")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    request_hash = broker_handoff_artifact_hash(request_payload)
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-bound-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=request_hash,
    )

    assert request_hash.startswith("sha256:")
    assert validate_broker_approval_request_binding(approval_payload, request_payload) == []
    assert validate_broker_approval_request_binding(approval_payload, request_path) == []

    approval_payload["request_artifact_hash"] = "sha256:" + "0" * 64
    assert validate_broker_approval_request_binding(approval_payload, request_payload) == [
        "request_artifact_hash does not match broker handoff artifact"
    ]


def test_broker_approval_binding_rejects_already_live_handoff_request(tmp_path):
    adapter = AlpacaPaperExportAdapter(
        client_prefix="approval-live-request",
        safety=BrokerSafetyConfig(
            mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
            account_mode="live",
            max_notional=1000.0,
            max_quantity=10.0,
            approval=BrokerApproval(
                approval_status="approved",
                approved_by="operator-7",
                approved_at="2026-05-31T12:00:00Z",
                max_notional=1000.0,
                allowed_symbols=("AAPL",),
                approval_reason="unit test approval",
            ),
        ),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="already live")],
        tmp_path,
    )
    request_path = tmp_path / "alpaca_paper_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:05:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-live-request-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )

    assert validate_broker_approval_request_binding(approval_payload, request_path) == [
        "request artifact must be a pre-live broker-review handoff, not live_human_approved"
    ]


def test_broker_handoff_hash_cli_and_script_validate_before_printing_hash(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="hash-cli",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="hash cli")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    expected_hash = broker_handoff_artifact_hash(request_path)

    cli_result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "hash-broker-handoff", str(request_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    script_result = subprocess.run(
        [sys.executable, "scripts/hash_broker_handoff_artifact.py", str(request_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert cli_result.stdout.strip() == expected_hash
    assert script_result.stdout.strip() == expected_hash

    payload = json.loads(request_path.read_text(encoding="utf-8"))
    payload["orders"][0]["submit_live"] = True
    broken_path = tmp_path / "broken_dry_run_orders.json"
    broken_path.write_text(json.dumps(payload), encoding="utf-8")
    broken_result = subprocess.run(
        [sys.executable, "-m", "tradearena.cli", "hash-broker-handoff", str(broken_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert broken_result.returncode == 1
    assert "Invalid broker handoff artifact" in broken_result.stdout


def test_broker_handoff_hash_helper_rejects_invalid_artifacts(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="hash-helper",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="hash helper")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    payload["orders"][0]["submit_live"] = True

    try:
        broker_handoff_artifact_hash(payload)
    except BrokerAdapterContractError as exc:
        assert "orders[0].submit_live must match live_human_approved mode" in str(exc)
    else:
        raise AssertionError("invalid broker handoff artifact was hashed")


def test_broker_approval_binding_reports_invalid_handoff_without_raising(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-invalid-request",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="invalid request")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    request_hash = broker_handoff_artifact_hash(request_payload)
    request_payload["orders"][0]["submit_live"] = True
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=500.0,
            allowed_symbols=("AAPL",),
            approval_reason="unit test",
        ),
        approval_id="approval-invalid-request",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=request_hash,
    )

    errors = validate_broker_approval_request_binding(approval_payload, request_payload)

    assert "orders[0].submit_live must match live_human_approved mode" in errors


def test_broker_approval_request_binding_rejects_orders_outside_approval_scope(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-scope",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 2.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="scope unit")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=150.0,
            allowed_symbols=("MSFT",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-scope-001",
        account_mode="live",
        max_quantity=1.0,
        allowed_order_types=(OrderType.MARKET,),
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )

    errors = validate_broker_approval_request_binding(approval_payload, request_path)
    assert "orders[0].symbol AAPL is outside approval allowed_symbols" in errors
    assert "orders[0].order_type limit is outside approval allowed_order_types" in errors
    assert "orders[0].quantity 2.0 exceeds approval max_quantity 1.0" in errors
    assert "orders[0].notional 200.00 exceeds approval max_notional 150.00" in errors
    try:
        broker_safety_from_approval_artifact(approval_payload, request_artifact=request_path)
    except BrokerAdapterContractError as exc:
        assert "outside approval allowed_symbols" in str(exc)
    else:
        raise AssertionError("expected approval request scope failure before live safety creation")


def test_broker_approval_request_binding_requires_calculable_notional(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-unpriced",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write([Order("AAPL", Side.BUY, 1.0, reason="unpriced market order")], tmp_path)
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=150.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-unpriced-001",
        account_mode="live",
        max_quantity=5.0,
        allowed_order_types=(OrderType.MARKET,),
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )

    assert validate_broker_approval_request_binding(approval_payload, request_path) == [
        "orders[0].notional cannot be checked without a positive limit_price"
    ]


def test_broker_safety_from_approval_artifact_can_require_request_binding(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-safety-bind",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="safety bind")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-safety-bound-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )

    safety = broker_safety_from_approval_artifact(approval_payload, request_artifact=request_path)
    assert safety.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED

    approval_payload["request_artifact_hash"] = "sha256:" + "0" * 64
    try:
        broker_safety_from_approval_artifact(approval_payload, request_artifact=request_path)
    except BrokerAdapterContractError as exc:
        assert "request_artifact_hash does not match broker handoff artifact" in str(exc)
    else:
        raise AssertionError("expected request binding failure before live safety creation")


def test_broker_safety_from_bound_approval_rejects_unreviewed_order(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-runtime-bind",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="reviewed order")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-runtime-bound-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )
    safety = broker_safety_from_approval_artifact(approval_payload, request_artifact=request_path)
    live_adapter = AlpacaPaperExportAdapter(client_prefix="runtime-bound-live", safety=safety)

    live_adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="reviewed order")],
        tmp_path / "approved",
    )
    try:
        live_adapter.write(
            [Order("AAPL", Side.BUY, 2.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="unreviewed order")],
            tmp_path / "unreviewed",
        )
    except BrokerAdapterContractError as exc:
        assert (
            "does not match an approved broker handoff order" in str(exc)
            or "approved broker handoff order count 0" in str(exc)
        )
    else:
        raise AssertionError("expected unreviewed order to be rejected by bound live safety")


def test_broker_safety_from_bound_approval_rejects_duplicate_reviewed_order_reuse(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-duplicate-bind",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    reviewed_order = Order(
        "AAPL",
        Side.BUY,
        1.0,
        order_type=OrderType.LIMIT,
        limit_price=100.0,
        reason="reviewed order",
    )
    adapter.write([reviewed_order], tmp_path)
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-duplicate-bound-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )
    safety = broker_safety_from_approval_artifact(approval_payload, request_artifact=request_path)
    live_adapter = AlpacaPaperExportAdapter(client_prefix="duplicate-bound-live", safety=safety)

    try:
        live_adapter.write([reviewed_order, reviewed_order], tmp_path / "duplicate")
    except BrokerAdapterContractError as exc:
        assert "approved broker handoff order count" in str(exc)
    else:
        raise AssertionError("expected duplicate reuse of one reviewed order to be rejected")


def test_broker_safety_from_bound_approval_rejects_time_in_force_change(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-tif-bind",
        time_in_force="day",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    reviewed_order = Order(
        "AAPL",
        Side.BUY,
        1.0,
        order_type=OrderType.LIMIT,
        limit_price=100.0,
        reason="reviewed order",
    )
    adapter.write([reviewed_order], tmp_path)
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-tif-bound-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )
    safety = broker_safety_from_approval_artifact(approval_payload, request_artifact=request_path)
    live_adapter = AlpacaPaperExportAdapter(client_prefix="tif-bound-live", time_in_force="gtc", safety=safety)

    try:
        live_adapter.write([reviewed_order], tmp_path / "changed-tif")
    except BrokerAdapterContractError as exc:
        assert "time_in_force" in str(exc)
    else:
        raise AssertionError("expected changed time_in_force to be rejected by bound live safety")


def test_broker_approval_binding_cli_and_script_reject_hash_mismatch(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-bind-cli",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="binding cli")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-bound-cli-001",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )
    approval_path = tmp_path / "broker_approval.json"
    approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "tradearena.cli",
            "validate-broker-approval-binding",
            str(approval_path),
            str(request_path),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/validate_broker_approval_binding.py",
            str(approval_path),
            str(request_path),
        ],
        cwd=ROOT,
        check=True,
    )

    approval_payload["request_artifact_hash"] = "sha256:" + "0" * 64
    approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tradearena.cli",
            "validate-broker-approval-binding",
            str(approval_path),
            str(request_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    script_result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_broker_approval_binding.py",
            str(approval_path),
            str(request_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert script_result.returncode == 1
    assert "request_artifact_hash does not match broker handoff artifact" in result.stdout
    assert "request_artifact_hash does not match broker handoff artifact" in script_result.stdout


def test_broker_approval_binding_script_reports_malformed_request_json(tmp_path):
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=500.0,
            allowed_symbols=("AAPL",),
            approval_reason="unit test",
        ),
        approval_id="approval-malformed-request",
        account_mode="live",
        max_quantity=5.0,
        request_artifact_hash="sha256:" + "0" * 64,
    )
    approval_path = tmp_path / "broker_approval.json"
    approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")
    request_path = tmp_path / "broken_request.json"
    request_path.write_text('{"schema": ', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_broker_approval_binding.py",
            str(approval_path),
            str(request_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "broker artifact file must contain valid JSON" in result.stdout
    assert "Traceback" not in result.stderr


def test_broker_approval_binding_cli_and_script_reject_expired_approval(tmp_path):
    adapter = DryRunBrokerAdapter(
        client_prefix="approval-expired-cli",
        safety=BrokerSafetyConfig(account_mode="paper", max_quantity=5.0, allowed_symbols=("AAPL",)),
    )
    adapter.write(
        [Order("AAPL", Side.BUY, 1.0, order_type=OrderType.LIMIT, limit_price=100.0, reason="expired binding")],
        tmp_path,
    )
    request_path = tmp_path / "dry_run_orders.json"
    approval_payload = build_broker_approval_artifact(
        BrokerApproval(
            approval_status="approved",
            approved_by="operator-7",
            approved_at="2026-05-31T12:00:00Z",
            max_notional=250.0,
            allowed_symbols=("AAPL",),
            approval_reason="paper shadow checks passed",
        ),
        approval_id="approval-expired-cli-001",
        account_mode="live",
        max_quantity=5.0,
        expires_at="2026-05-31T13:00:00Z",
        request_artifact_hash=broker_handoff_artifact_hash(request_path),
    )
    approval_path = tmp_path / "broker_approval.json"
    approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tradearena.cli",
            "validate-broker-approval-binding",
            str(approval_path),
            str(request_path),
            "--now",
            "2026-05-31T14:00:00Z",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    script_result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_broker_approval_binding.py",
            str(approval_path),
            str(request_path),
            "--now",
            "2026-05-31T14:00:00Z",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert script_result.returncode == 1
    assert "approval artifact is expired" in result.stdout
    assert "approval artifact is expired" in script_result.stdout


def test_broker_approval_safety_demo_writes_valid_artifact():
    subprocess.run([sys.executable, "examples/broker_approval_safety_demo.py"], cwd=ROOT, check=True)
    artifact = ROOT / "outputs/examples/broker_approval_safety/broker_approval_artifact.json"
    summary = json.loads((ROOT / "outputs/examples/broker_approval_safety/summary.json").read_text(encoding="utf-8"))
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert summary["approval_validated"] is True
    assert summary["request_hash_bound"] is True
    assert summary["adapter_mode"] == "live_human_approved"
    assert summary["approved_order_passed"] is True
    assert summary["oversized_order_blocked"] is True
    assert payload["request_artifact_hash"] == summary["request_artifact_hash"]
    assert validate_broker_approval_artifact(payload) == []
    assert summary["verification_commands"] == [
        "python scripts/validate_broker_handoff_artifact.py outputs/examples/broker_approval_safety/dry_run_orders.json",
        "python scripts/hash_broker_handoff_artifact.py outputs/examples/broker_approval_safety/dry_run_orders.json",
        (
            "python scripts/validate_broker_approval_artifact.py "
            "outputs/examples/broker_approval_safety/broker_approval_artifact.json "
            "--now 2026-05-31T12:30:00Z"
        ),
        (
            "python scripts/validate_broker_approval_binding.py "
            "outputs/examples/broker_approval_safety/broker_approval_artifact.json "
            "outputs/examples/broker_approval_safety/dry_run_orders.json "
            "--now 2026-05-31T12:30:00Z"
        ),
    ]


def test_broker_approval_safety_demo_contract_validates_with_fixed_now():
    manifest = (ROOT / "docs/demo_artifacts.yaml").read_text(encoding="utf-8")

    assert (
        "python scripts/validate_broker_approval_artifact.py "
        "outputs/examples/broker_approval_safety/broker_approval_artifact.json "
        "--now 2026-05-31T12:30:00Z"
    ) in manifest
    assert (
        "python scripts/validate_broker_approval_binding.py "
        "outputs/examples/broker_approval_safety/broker_approval_artifact.json "
        "outputs/examples/broker_approval_safety/dry_run_orders.json "
        "--now 2026-05-31T12:30:00Z"
    ) in manifest


def test_dry_run_broker_adapter_demo_writes_valid_handoff():
    subprocess.run([sys.executable, "examples/dry_run_broker_adapter_demo.py"], cwd=ROOT, check=True)
    artifact = ROOT / "outputs/examples/dry_run_broker_adapter/dry_run_orders.json"
    summary = json.loads((ROOT / "outputs/examples/dry_run_broker_adapter/summary.json").read_text(encoding="utf-8"))
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert summary["adapter_mode"] == "dry_run"
    assert summary["live_submission"] is False
    assert summary["validated"] is True
    assert payload["adapter"] == "dry-run-broker-adapter"
    assert validate_broker_handoff_artifact(payload) == []


def test_holdings_csv_import_fixture_loads_retail_holdings():
    holdings = load_holdings_csv(ROOT / "examples/fixtures/retail_holdings.csv")

    assert len(holdings) == 4
    assert holdings[0].symbol == "CASH"
    assert sum(item.market_value for item in holdings) == 100000


def test_futures_roll_engine_flags_roll_window():
    report = FuturesRollRiskEngine().review(
        timestamp=datetime(2026, 6, 14),
        contracts=(
            FuturesContractMetadata(
                symbol="MESM26",
                root_symbol="MES",
                expiry=date(2026, 6, 19),
                roll_start=date(2026, 6, 12),
                roll_end=date(2026, 6, 17),
                contract_multiplier=5.0,
                initial_margin_rate=0.08,
            ),
        ),
        positions={"MESM26": 1.0},
    )

    assert any(item.constraint == "futures_roll_window" for item in report.violations)
    assert report.blocked_count == 0


def test_mock_rl_policy_baseline_reuses_standard_stack():
    registry = default_registry()
    assert "mock-rl-policy" in registry.names("strategy")

    system = build_default_system(
        symbols=("SYN", "ALT", "DEF"),
        periods=12,
        seed=5,
        analyst_names=(),
        strategy_name="mock-rl-policy",
        max_position_weight=0.2,
    )
    trajectory, metrics = system.run()

    assert metrics["steps"] == 12
    assert trajectory.steps[-1].decisions
    assert all(float(decision["target_weight"]) <= 0.2 for decision in trajectory.steps[-1].decisions)


def test_new_issue_examples_write_expected_artifacts():
    examples = (
        ("examples/alpaca_paper_export_demo.py", "outputs/examples/alpaca_paper_export/summary.json"),
        (
            "examples/broker_response_reconciliation_demo.py",
            "outputs/examples/broker_response_reconciliation/summary.json",
        ),
        ("examples/holdings_csv_import_demo.py", "outputs/examples/holdings_csv_import/summary.json"),
        ("examples/futures_roll_risk_demo.py", "outputs/examples/futures_roll_risk/summary.json"),
        ("examples/crypto_microstructure_stress_demo.py", "outputs/examples/crypto_microstructure_stress/summary.json"),
        ("examples/rl_policy_baseline_demo.py", "outputs/examples/rl_policy_baseline/summary.json"),
    )
    for script, artifact in examples:
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
        assert (ROOT / artifact).exists()

    crypto = json.loads(
        (ROOT / "outputs/examples/crypto_microstructure_stress/summary.json").read_text(encoding="utf-8")
    )
    assert crypto["rejected_order_count"] >= 0
    assert "total_slippage_cost" in crypto

    futures = json.loads((ROOT / "outputs/examples/futures_roll_risk/summary.json").read_text(encoding="utf-8"))
    assert futures["roll_flagged"] is True

    reconciliation = json.loads(
        (ROOT / "outputs/examples/broker_response_reconciliation/summary.json").read_text(encoding="utf-8")
    )
    assert reconciliation["live_submission"] is False
    assert reconciliation["reconciliation"]["partial_fill_count"] == 1
    assert reconciliation["reconciliation"]["missing_response_count"] == 1
