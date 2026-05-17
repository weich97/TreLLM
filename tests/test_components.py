from trading_agent_os.core.domain import Order, PortfolioState, Side
from trading_agent_os.data import SyntheticMarketDataProvider
from trading_agent_os.tools import RealisticOrderSimulator, RiskCalculator, SimpleOrderSimulator


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
