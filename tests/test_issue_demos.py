from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from tradearena.core.domain import Order, OrderType, Side
from tradearena.factory import build_default_system, default_registry
from tradearena.planning import load_holdings_csv
from tradearena.tools import (
    AlpacaPaperExportAdapter,
    BrokerAdapter,
    BrokerAdapterContractError,
    BrokerAdapterMode,
    BrokerOrderStatus,
    BrokerApproval,
    BrokerResponse,
    BrokerSafetyConfig,
    DryRunBrokerAdapter,
    FuturesContractMetadata,
    FuturesRollRiskEngine,
    build_broker_approval_artifact,
    broker_approval_from_artifact,
    broker_handoff_artifact_hash,
    broker_safety_from_approval_artifact,
    reconcile_broker_responses,
    validate_broker_approval_artifact,
    validate_broker_approval_request_binding,
    validate_broker_handoff_artifact,
    validate_broker_response_artifact,
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
                submitted_quantity=1.0,
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


def test_broker_approval_artifact_builds_live_safety_config():
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
    )

    approval = broker_approval_from_artifact(payload)
    safety = broker_safety_from_approval_artifact(payload)

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
        assert "max_notional" in str(exc)
    else:
        raise AssertionError("expected max_notional failure from approval artifact safety")


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
