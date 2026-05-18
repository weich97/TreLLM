from tradearena.core.domain import Order, PortfolioState, Side
from tradearena.data import SyntheticMarketDataProvider
from tradearena.tools.calibration import ExecutionCalibrationConfig, summarize_execution_calibration
from tradearena.tools import RealisticOrderSimulator, RiskCalculator, SimpleOrderSimulator


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
