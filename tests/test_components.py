from datetime import datetime, timezone

from tradearena.agents import AlwaysHoldStrategy, MaxPositionRiskManager, MemoryAwareSignalWeightedStrategy, RandomAllocationStrategy
from tradearena.core.domain import Decision, Fill, MarketSnapshot, Order, PortfolioState, Side, Signal
from tradearena.core.trajectory import StepRecord, Trajectory
from tradearena.data import SyntheticMarketDataProvider
from tradearena.evaluation import BehavioralEvaluator
from tradearena.memory import InMemoryResearchMemory
from tradearena.tools.calibration import ExecutionCalibrationConfig, summarize_execution_calibration
from tradearena.tools import (
    CalibratedOrderSimulator,
    FillReplayOrderSimulator,
    QuoteReplayOrderSimulator,
    RealisticOrderSimulator,
    RiskCalculator,
    SimpleOrderSimulator,
)


def test_order_simulator_never_overspends_cash():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=1, seed=1).stream()[0]
    portfolio = PortfolioState(cash=100.0)
    simulator = SimpleOrderSimulator(commission_bps=10.0, slippage_bps=5.0)

    fills = simulator.execute(snapshot, [Order(symbol="SYN", side=Side.BUY, quantity=10_000)], portfolio)

    assert len(fills) == 1
    assert portfolio.cash >= -1e-9
    assert portfolio.equity() > 0


def test_risk_calculator_drawdown():
    risk = RiskCalculator()

    assert risk.max_drawdown([100.0, 120.0, 90.0, 110.0]) == -0.25


def test_drawdown_kill_switch_forces_derisk_after_rolling_loss():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=1, seed=1).stream()[0]
    memory = InMemoryResearchMemory()
    memory.record("step", {"equity": 100_000.0})
    memory.record("step", {"equity": 96_000.0})
    portfolio = PortfolioState(cash=90_000.0)
    portfolio.last_prices.update({symbol: bar.close for symbol, bar in snapshot.bars.items()})
    decision = Decision(
        symbol="SYN",
        side=Side.BUY,
        target_weight=0.30,
        confidence=0.90,
        rationale="LLM wants to add after losses",
    )
    risk = MaxPositionRiskManager(max_drawdown=0.05, drawdown_lookback=3, drawdown_de_risk_weight=0.0)

    approved = risk.approve(snapshot, [decision], portfolio, memory)

    assert approved[0].target_weight == 0.0
    assert approved[0].side == Side.HOLD
    assert approved[0].metadata["drawdown_kill_switch"] is True
    assert risk.last_report is not None
    assert risk.last_report.passed is False
    assert risk.last_report.violations[0].constraint == "drawdown_kill_switch"


def test_drawdown_kill_switch_stays_inactive_inside_limit():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=1, seed=1).stream()[0]
    memory = InMemoryResearchMemory()
    memory.record("step", {"equity": 100_000.0})
    portfolio = PortfolioState(cash=98_000.0)
    portfolio.last_prices.update({symbol: bar.close for symbol, bar in snapshot.bars.items()})
    decision = Decision(
        symbol="SYN",
        side=Side.BUY,
        target_weight=0.20,
        confidence=0.90,
        rationale="within drawdown budget",
    )
    risk = MaxPositionRiskManager(max_drawdown=0.05, drawdown_lookback=3)

    approved = risk.approve(snapshot, [decision], portfolio, memory)

    assert approved[0].target_weight == 0.20
    assert "drawdown_kill_switch" not in approved[0].metadata
    assert risk.last_report is not None
    assert risk.last_report.passed is True


def test_memory_aware_strategy_decays_polluted_memory_and_reports_amplification():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=1, seed=1).stream()[0]
    portfolio = PortfolioState(cash=100_000.0)
    signal = Signal(symbol="SYN", score=0.08, horizon="1w", confidence=1.0, rationale="positive momentum")
    memory = InMemoryResearchMemory()
    memory.record("step", {"equity": 100_000.0, "memory_pollution": True})
    memory.record("step", {"equity": 101_500.0})
    memory.record("step", {"equity": 103_000.0})

    low_decay = MemoryAwareSignalWeightedStrategy(lookback_events=3, memory_decay_rate=0.1)
    high_decay = MemoryAwareSignalWeightedStrategy(lookback_events=3, memory_decay_rate=1.0)

    low_metadata = low_decay.decide(snapshot, [signal], portfolio, memory)[0].metadata
    high_metadata = high_decay.decide(snapshot, [signal], portfolio, memory)[0].metadata

    assert low_metadata["memory_decay_rate"] == 0.1
    assert low_metadata["memory_pollution_ratio"] < high_metadata["memory_pollution_ratio"]
    assert low_metadata["memory_driven_leverage_amplification"] > high_metadata["memory_driven_leverage_amplification"]
    assert low_metadata["memory_driven_leverage_amplification"] > 1.0


def test_behavioral_evaluator_summarizes_memory_diagnostics():
    trajectory = Trajectory(experiment_name="memory-diagnostics", seed=7)
    trajectory.append(
        StepRecord(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            observation={},
            signals=[],
            decisions=[],
            approved_decisions=[
                {
                    "side": Side.BUY.value,
                    "target_weight": 0.25,
                    "metadata": {
                        "memory_driven_leverage_amplification": 1.20,
                        "memory_pollution_ratio": 0.10,
                    },
                },
                {
                    "side": Side.HOLD.value,
                    "target_weight": 0.0,
                    "metadata": {
                        "memory_driven_leverage_amplification": 0.80,
                        "memory_pollution_ratio": 0.30,
                    },
                },
            ],
            orders=[],
            fills=[],
            portfolio={"equity": 100_000.0},
        )
    )

    metrics = BehavioralEvaluator().evaluate(trajectory)

    assert metrics["memory_decision_count"] == 2
    assert metrics["memory_driven_leverage_amplification"] == 1.0
    assert metrics["max_memory_driven_leverage_amplification"] == 1.20
    assert metrics["memory_pollution_ratio"] == 0.20
    assert metrics["max_memory_pollution_ratio"] == 0.30


def test_lower_anchor_strategies_are_deterministic_and_distinct():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN", "ALT"), periods=1, seed=1).stream()[0]
    portfolio = PortfolioState(cash=100_000.0)

    hold_decisions = AlwaysHoldStrategy().decide(snapshot, [], portfolio, memory=None)
    first_random = RandomAllocationStrategy(seed=13).decide(snapshot, [], portfolio, memory=None)
    second_random = RandomAllocationStrategy(seed=13).decide(snapshot, [], portfolio, memory=None)

    assert all(decision.target_weight == 0.0 for decision in hold_decisions)
    assert [decision.target_weight for decision in first_random] == [decision.target_weight for decision in second_random]
    assert any(decision.target_weight > 0.0 for decision in first_random)


def test_realistic_simulator_records_partial_fill_and_latency():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=2, seed=1).stream()[0]
    portfolio = PortfolioState(cash=1_000_000.0)
    simulator = RealisticOrderSimulator(participation_rate=0.000001, latency_steps=0)

    fills = simulator.execute(snapshot, [Order(symbol="SYN", side=Side.BUY, quantity=10_000)], portfolio)

    assert len(fills) == 1
    assert fills[0].fill_ratio < 1.0
    assert simulator.last_report is not None
    assert simulator.last_report.partial_fills == 1


def test_realistic_simulator_spread_bps_increases_crossing_cost():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=2, seed=3).stream()[0]
    orders = [Order(symbol="SYN", side=Side.BUY, quantity=10)]

    no_spread_portfolio = PortfolioState(cash=1_000_000.0)
    wide_spread_portfolio = PortfolioState(cash=1_000_000.0)
    no_spread = RealisticOrderSimulator(participation_rate=1.0, latency_steps=0, spread_bps=0.0)
    wide_spread = RealisticOrderSimulator(participation_rate=1.0, latency_steps=0, spread_bps=100.0)

    no_spread_fill = no_spread.execute(snapshot, orders, no_spread_portfolio)[0]
    wide_spread_fill = wide_spread.execute(snapshot, orders, wide_spread_portfolio)[0]

    assert wide_spread_fill.price > no_spread_fill.price
    assert wide_spread.last_report is not None
    assert wide_spread.last_report.metadata["spread_bps"] == 100.0
    assert wide_spread.last_report.total_slippage > no_spread.last_report.total_slippage


def test_quote_replay_simulator_uses_quotes_and_level2_depth():
    base_snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=2, seed=3).stream()[0]
    snapshot = MarketSnapshot(
        timestamp=base_snapshot.timestamp,
        bars=base_snapshot.bars,
        alt_data={
            "quotes": {"SYN": {"bid": 99.9, "ask": 100.1}},
            "level2": {"SYN": {"ask_size": 3.0, "bid_size": 5.0}},
        },
    )
    portfolio = PortfolioState(cash=1_000_000.0)
    simulator = QuoteReplayOrderSimulator(
        participation_rate=1.0,
        latency_steps=0,
        base_slippage_bps=0.0,
        market_impact=0.0,
    )

    fills = simulator.execute(snapshot, [Order(symbol="SYN", side=Side.BUY, quantity=10.0)], portfolio)

    assert len(fills) == 1
    assert fills[0].quantity == 3.0
    assert fills[0].price > 100.1
    assert simulator.last_report is not None
    assert simulator.last_report.metadata["assumption_class"] == "quote_replay"
    assert simulator.last_report.metadata["level2_liquidity"] is True


def test_calibrated_simulator_marks_external_profile():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=2, seed=3).stream()[0]
    portfolio = PortfolioState(cash=1_000_000.0)
    simulator = CalibratedOrderSimulator(
        calibration_profile_id="broker-fill-fit-2026q1",
        participation_rate=1.0,
        latency_steps=0,
    )

    simulator.execute(snapshot, [Order(symbol="SYN", side=Side.BUY, quantity=1.0)], portfolio)

    assert simulator.last_report is not None
    assert simulator.last_report.metadata["assumption_class"] == "calibrated"
    assert simulator.last_report.metadata["calibration_profile_id"] == "broker-fill-fit-2026q1"


def test_fill_replay_simulator_applies_realized_fill_log():
    snapshot = SyntheticMarketDataProvider(symbols=("SYN",), periods=2, seed=3).stream()[0]
    replay_fill = Fill(
        symbol="SYN",
        side=Side.BUY,
        quantity=4.0,
        price=101.25,
        commission=0.5,
        timestamp=snapshot.timestamp,
        requested_quantity=10.0,
        fill_ratio=0.4,
        slippage=1.25,
    )
    portfolio = PortfolioState(cash=1_000.0)
    simulator = FillReplayOrderSimulator(replay_fills=[replay_fill])

    fills = simulator.execute(snapshot, [Order(symbol="SYN", side=Side.BUY, quantity=10.0)], portfolio)

    assert len(fills) == 1
    assert fills[0].quantity == 4.0
    assert fills[0].price == 101.25
    assert portfolio.positions["SYN"] == 4.0
    assert simulator.last_report is not None
    assert simulator.last_report.partial_fills == 1
    assert simulator.last_report.metadata["assumption_class"] == "fill_replay"


def test_execution_calibration_marks_ohlcv_limits(tmp_path):
    csv_path = tmp_path / "SYN_Hourly_1h.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Date,Open,High,Low,Close,Volume",
                "2026-01-01T09:30:00,100,102,99,101,1000",
                "2026-01-01T10:30:00,101,103,100,102,2000",
            ]
        ),
        encoding="utf-8",
    )

    summary = summarize_execution_calibration(
        [csv_path],
        ExecutionCalibrationConfig(spread_bps=None, participation_rate=0.05, market_impact=0.15),
    )

    assert summary["data"]["symbol_count"] == 1
    assert summary["data"]["row_count"] == 2
    assert summary["diagnostics"]["spread_status"] == "assumed_zero_or_external"
    assert "OHLCV bars do not contain bid-ask quotes" in summary["diagnostics"]["identification_warning"]
