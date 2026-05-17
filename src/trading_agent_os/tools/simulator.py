from __future__ import annotations

from dataclasses import dataclass, field

from trading_agent_os.core.domain import ExecutionReport, Fill, MarketSnapshot, Order, PortfolioState, Side


@dataclass
class SimpleOrderSimulator:
    commission_bps: float = 1.0
    slippage_bps: float = 2.0
    allow_short: bool = False
    name: str = "simple-order-simulator"
    last_report: ExecutionReport | None = field(default=None, init=False)

    def execute(self, snapshot: MarketSnapshot, orders: list[Order], portfolio: PortfolioState) -> list[Fill]:
        portfolio.last_prices.update({symbol: bar.close for symbol, bar in snapshot.bars.items()})
        fills: list[Fill] = []
        rejected = 0
        for order in orders:
            if order.side == Side.HOLD or order.symbol not in snapshot.bars:
                rejected += 1
                continue
            mid = snapshot.price(order.symbol)
            slip = self.slippage_bps / 10_000.0
            price = mid * (1.0 + slip if order.side == Side.BUY else 1.0 - slip)
            quantity = max(0.0, order.quantity)
            trade_value = quantity * price
            commission = trade_value * self.commission_bps / 10_000.0

            if order.side == Side.BUY:
                commission_rate = self.commission_bps / 10_000.0
                affordable = max(0.0, portfolio.cash) / (price * (1.0 + commission_rate))
                quantity = min(quantity, affordable)
                if quantity <= 0:
                    continue
                trade_value = quantity * price
                commission = trade_value * self.commission_bps / 10_000.0
                portfolio.cash -= trade_value + commission
                portfolio.positions[order.symbol] = portfolio.positions.get(order.symbol, 0.0) + quantity
            elif order.side == Side.SELL:
                available = portfolio.positions.get(order.symbol, 0.0)
                if not self.allow_short:
                    quantity = min(quantity, max(0.0, available))
                if quantity <= 0:
                    continue
                trade_value = quantity * price
                commission = trade_value * self.commission_bps / 10_000.0
                portfolio.cash += trade_value - commission
                portfolio.positions[order.symbol] = available - quantity

            fills.append(
                Fill(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=quantity,
                    price=price,
                    commission=commission,
                    timestamp=snapshot.timestamp,
                    requested_quantity=order.quantity,
                    liquidity_available=order.quantity,
                    fill_ratio=1.0,
                    slippage=price - mid,
                )
            )
        self.last_report = ExecutionReport(
            timestamp=snapshot.timestamp,
            submitted_orders=len(orders),
            eligible_orders=len(orders) - rejected,
            filled_orders=len(fills),
            partial_fills=0,
            pending_orders=0,
            rejected_orders=rejected,
            total_commission=sum(fill.commission for fill in fills),
            total_slippage=sum(abs(fill.slippage) * fill.quantity for fill in fills),
            average_latency_steps=0.0,
            metadata={"mode": "idealized"},
        )
        return fills


@dataclass
class RealisticOrderSimulator:
    """Execution simulator with costs, slippage, latency, liquidity, and partial fills."""

    commission_bps: float = 1.0
    base_slippage_bps: float = 2.0
    spread_bps: float = 0.0
    participation_rate: float = 0.05
    latency_steps: int = 1
    market_impact: float = 0.15
    allow_short: bool = False
    name: str = "realistic-order-simulator"
    _pending: list[tuple[int, int, Order]] = field(default_factory=list, init=False)
    _step: int = field(default=0, init=False)
    _sequence: int = field(default=0, init=False)
    last_report: ExecutionReport | None = field(default=None, init=False)

    def execute(self, snapshot: MarketSnapshot, orders: list[Order], portfolio: PortfolioState) -> list[Fill]:
        portfolio.last_prices.update({symbol: bar.close for symbol, bar in snapshot.bars.items()})
        for order in orders:
            self._sequence += 1
            self._pending.append((self._step + self.latency_steps, self._sequence, order))

        eligible = [(release, seq, order) for release, seq, order in self._pending if release <= self._step]
        self._pending = [(release, seq, order) for release, seq, order in self._pending if release > self._step]
        eligible.sort(key=lambda item: item[1])

        remaining_liquidity = {
            symbol: max(0.0, bar.volume * self.participation_rate)
            for symbol, bar in snapshot.bars.items()
        }
        fills: list[Fill] = []
        rejected = 0
        partial = 0

        for release, _, order in eligible:
            if order.side == Side.HOLD or order.symbol not in snapshot.bars:
                rejected += 1
                continue
            bar = snapshot.bars[order.symbol]
            requested = max(0.0, order.quantity)
            available = remaining_liquidity.get(order.symbol, 0.0)
            quantity = min(requested, available)
            if order.side == Side.SELL and not self.allow_short:
                quantity = min(quantity, max(0.0, portfolio.positions.get(order.symbol, 0.0)))
            if quantity <= 0:
                rejected += 1
                continue

            fill_ratio = quantity / requested if requested else 0.0
            was_partial = fill_ratio < 0.999999
            if fill_ratio < 0.999999:
                partial += 1
            remaining_liquidity[order.symbol] = max(0.0, available - quantity)

            participation = quantity / max(1.0, bar.volume)
            intraday_vol = max(0.0, (bar.high - bar.low) / max(1e-9, bar.close))
            # Market orders cross half the quoted bid-ask spread before impact and volatility slippage.
            half_spread_rate = max(0.0, self.spread_bps) / 20_000.0
            slip_rate = (
                half_spread_rate
                + (self.base_slippage_bps / 10_000.0)
                + self.market_impact * participation
                + 0.1 * intraday_vol
            )
            mid = bar.close
            price = mid * (1.0 + slip_rate if order.side == Side.BUY else 1.0 - slip_rate)

            if order.limit_price is not None:
                crossed = price <= order.limit_price if order.side == Side.BUY else price >= order.limit_price
                if not crossed:
                    rejected += 1
                    continue

            if order.side == Side.BUY:
                commission_rate = self.commission_bps / 10_000.0
                affordable = max(0.0, portfolio.cash) / (price * (1.0 + commission_rate))
                quantity = min(quantity, affordable)
                if quantity <= 0:
                    rejected += 1
                    continue
                fill_ratio = quantity / requested if requested else 0.0
                if fill_ratio < 0.999999 and not was_partial:
                    partial += 1
                trade_value = quantity * price
                commission = trade_value * commission_rate
                portfolio.cash -= trade_value + commission
                portfolio.positions[order.symbol] = portfolio.positions.get(order.symbol, 0.0) + quantity
            else:
                trade_value = quantity * price
                commission = trade_value * self.commission_bps / 10_000.0
                portfolio.cash += trade_value - commission
                portfolio.positions[order.symbol] = portfolio.positions.get(order.symbol, 0.0) - quantity

            fills.append(
                Fill(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=quantity,
                    price=price,
                    commission=commission,
                    timestamp=snapshot.timestamp,
                    requested_quantity=requested,
                    latency_steps=max(0, self._step - release + self.latency_steps),
                    liquidity_available=available,
                    fill_ratio=fill_ratio,
                    slippage=price - mid,
                    status="partial" if fill_ratio < 0.999999 else "filled",
                )
            )

        self.last_report = ExecutionReport(
            timestamp=snapshot.timestamp,
            submitted_orders=len(orders),
            eligible_orders=len(eligible),
            filled_orders=len(fills),
            partial_fills=partial,
            pending_orders=len(self._pending),
            rejected_orders=rejected,
            total_commission=sum(fill.commission for fill in fills),
            total_slippage=sum(abs(fill.slippage) * fill.quantity for fill in fills),
            average_latency_steps=sum(fill.latency_steps for fill in fills) / len(fills) if fills else 0.0,
            metadata={
                "mode": "realistic",
                "participation_rate": self.participation_rate,
                "latency_steps": self.latency_steps,
                "market_impact": self.market_impact,
                "spread_bps": self.spread_bps,
            },
        )
        self._step += 1
        return fills
