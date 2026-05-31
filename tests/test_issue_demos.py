from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from tradearena.core.domain import Order, Side
from tradearena.factory import build_default_system, default_registry
from tradearena.planning import load_holdings_csv
from tradearena.tools import (
    AlpacaPaperExportAdapter,
    BrokerAdapterContractError,
    BrokerAdapterMode,
    BrokerApproval,
    BrokerSafetyConfig,
    FuturesContractMetadata,
    FuturesRollRiskEngine,
)

ROOT = Path(__file__).resolve().parents[1]


def test_alpaca_paper_export_adapter_requires_human_approval(tmp_path):
    adapter = AlpacaPaperExportAdapter(client_prefix="unit")
    result = adapter.write([Order("AAPL", Side.BUY, 3.5, reason="unit test")], tmp_path)
    payload = json.loads((tmp_path / "alpaca_paper_orders.json").read_text(encoding="utf-8"))

    assert result["order_count"] == 1
    assert payload["adapter_mode"] == "offline_export"
    assert payload["account_mode"] == "none"
    assert payload["live_submission"] is False
    assert payload["manual_approval_required"] is True
    assert payload["orders"][0]["adapter_mode"] == "offline_export"
    assert payload["orders"][0]["approval_status"] == "requires_human_approval"


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
                max_notional=1000.0,
                allowed_symbols=("AAPL",),
                approval_reason="unit test approval",
            ),
        )
    )
    approved.write([Order("AAPL", Side.BUY, 1.0, reason="unit test")], tmp_path / "approved")
    payload = json.loads((tmp_path / "approved" / "alpaca_paper_orders.json").read_text(encoding="utf-8"))

    assert payload["adapter_mode"] == "live_human_approved"
    assert payload["account_mode"] == "live"
    assert payload["live_submission"] is True
    assert payload["manual_approval_required"] is False
    assert payload["orders"][0]["approval_status"] == "approved"


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
