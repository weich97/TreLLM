from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from tradearena.core.domain import ExecutionReport, Fill, MarketSnapshot, Order, PortfolioState, Side


EXECUTION_STRESS = "stress"
EXECUTION_CALIBRATED = "calibrated"
EXECUTION_QUOTE_REPLAY = "quote_replay"
EXECUTION_FILL_REPLAY = "fill_replay"


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
            metadata={"mode": "idealized", "assumption_class": "idealized"},
        )
        return fills


@dataclass
class RealisticOrderSimulator:
    """Paper-execution stress simulator with costs, latency, liquidity, and partial fills."""

    commission_bps: float = 1.0
    base_slippage_bps: float = 2.0
    spread_bps: float = 0.0
    participation_rate: float = 0.05
    latency_steps: int = 1
    market_impact: float = 0.15
    allow_short: bool = False
    name: str = "realistic-order-simulator"
    assumption_class: str = EXECUTION_STRESS
    calibration_profile_id: str | None = None
    use_quote_replay: bool = False
    use_level2_liquidity: bool = False
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

        remaining_liquidity = {}
        liquidity_source = "bar_volume_participation"
        for symbol, bar in snapshot.bars.items():
            bar_capacity = max(0.0, bar.volume * self.participation_rate)
            if self.use_level2_liquidity:
                depth_capacity = _level2_available(snapshot, symbol, Side.BUY)
                if depth_capacity is not None:
                    bar_capacity = min(bar_capacity, depth_capacity)
                    liquidity_source = "level2_depth_and_bar_volume"
            remaining_liquidity[symbol] = bar_capacity
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
            if self.use_level2_liquidity:
                side_depth = _level2_available(snapshot, order.symbol, order.side)
                if side_depth is not None:
                    available = min(available, side_depth)
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
            quote = _quote_for(snapshot, order.symbol) if self.use_quote_replay else None
            bid = _float_or_none(quote.get("bid") if quote else None) or _float_or_none(
                quote.get("bid_price") if quote else None
            )
            ask = _float_or_none(quote.get("ask") if quote else None) or _float_or_none(
                quote.get("ask_price") if quote else None
            )
            mid = (bid + ask) / 2.0 if bid and ask else bar.close
            quoted_spread_bps = _quote_spread_bps(quote, mid) if quote else None
            effective_spread_bps = self.spread_bps if quoted_spread_bps is None else quoted_spread_bps
            residual_slip_rate = (
                (self.base_slippage_bps / 10_000.0)
                + self.market_impact * participation
                + 0.1 * intraday_vol
            )
            half_spread_rate = max(0.0, effective_spread_bps) / 20_000.0
            if quote and bid and ask:
                cross_price = ask if order.side == Side.BUY else bid
                price = cross_price * (1.0 + residual_slip_rate if order.side == Side.BUY else 1.0 - residual_slip_rate)
            else:
                slip_rate = half_spread_rate + residual_slip_rate
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
                "assumption_class": self.assumption_class,
                "calibration_profile_id": self.calibration_profile_id,
                "participation_rate": self.participation_rate,
                "latency_steps": self.latency_steps,
                "market_impact": self.market_impact,
                "spread_bps": self.spread_bps,
                "quote_replay": self.use_quote_replay,
                "level2_liquidity": self.use_level2_liquidity,
                "liquidity_source": liquidity_source,
            },
        )
        self._step += 1
        return fills


@dataclass
class CalibratedOrderSimulator(RealisticOrderSimulator):
    """Realistic simulator configured from an external quote/fill calibration profile."""

    name: str = "calibrated-order-simulator"
    assumption_class: str = EXECUTION_CALIBRATED
    calibration_profile_id: str | None = "external-calibration"


@dataclass
class QuoteReplayOrderSimulator(RealisticOrderSimulator):
    """Replay top-of-book or Level-2 quote snapshots when they are present in `snapshot.alt_data`."""

    name: str = "quote-replay-order-simulator"
    assumption_class: str = EXECUTION_QUOTE_REPLAY
    use_quote_replay: bool = True
    use_level2_liquidity: bool = True


@dataclass
class FillReplayOrderSimulator:
    """Apply realized fills from a private or licensed fill log.

    This simulator is intentionally conservative: if a submitted order has no
    matching replay fill at the current timestamp, the order is counted as
    rejected. It is meant for audit replay, not for predicting future costs.
    """

    replay_fills: list[Fill] | None = None
    csv_path: str | Path | None = None
    allow_short: bool = False
    enforce_cash: bool = True
    name: str = "fill-replay-order-simulator"
    _unused_fills: list[Fill] = field(default_factory=list, init=False)
    last_report: ExecutionReport | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        fills = list(self.replay_fills or [])
        if self.csv_path:
            fills.extend(load_replay_fills_csv(self.csv_path))
        self._unused_fills = fills

    def execute(self, snapshot: MarketSnapshot, orders: list[Order], portfolio: PortfolioState) -> list[Fill]:
        portfolio.last_prices.update({symbol: bar.close for symbol, bar in snapshot.bars.items()})
        fills: list[Fill] = []
        rejected = 0
        partial = 0
        for order in orders:
            if order.side == Side.HOLD:
                rejected += 1
                continue
            fill = self._pop_replay_fill(snapshot, order)
            if fill is None:
                rejected += 1
                continue
            quantity = min(fill.quantity, max(0.0, order.quantity))
            if order.side == Side.SELL and not self.allow_short:
                quantity = min(quantity, max(0.0, portfolio.positions.get(order.symbol, 0.0)))
            if order.side == Side.BUY and self.enforce_cash:
                affordable = max(0.0, portfolio.cash - fill.commission) / max(fill.price, 1e-9)
                quantity = min(quantity, affordable)
            if quantity <= 0:
                rejected += 1
                continue
            fill_ratio = quantity / max(order.quantity, 1e-9)
            partial += 1 if fill_ratio < 0.999999 else 0
            applied = Fill(
                symbol=fill.symbol,
                side=fill.side,
                quantity=quantity,
                price=fill.price,
                commission=fill.commission,
                timestamp=fill.timestamp,
                requested_quantity=order.quantity,
                latency_steps=fill.latency_steps,
                liquidity_available=fill.liquidity_available,
                fill_ratio=fill_ratio,
                slippage=fill.slippage,
                status="partial" if fill_ratio < 0.999999 else "filled",
            )
            if applied.side == Side.BUY:
                portfolio.cash -= applied.quantity * applied.price + applied.commission
                portfolio.positions[applied.symbol] = portfolio.positions.get(applied.symbol, 0.0) + applied.quantity
            else:
                portfolio.cash += applied.quantity * applied.price - applied.commission
                portfolio.positions[applied.symbol] = portfolio.positions.get(applied.symbol, 0.0) - applied.quantity
            fills.append(applied)
        self.last_report = ExecutionReport(
            timestamp=snapshot.timestamp,
            submitted_orders=len(orders),
            eligible_orders=len(orders),
            filled_orders=len(fills),
            partial_fills=partial,
            pending_orders=0,
            rejected_orders=rejected,
            total_commission=sum(fill.commission for fill in fills),
            total_slippage=sum(abs(fill.slippage) * fill.quantity for fill in fills),
            average_latency_steps=sum(fill.latency_steps for fill in fills) / len(fills) if fills else 0.0,
            metadata={
                "mode": "real_fill_replay",
                "assumption_class": EXECUTION_FILL_REPLAY,
                "fill_source": str(self.csv_path) if self.csv_path else "in_memory",
                "unmatched_replay_fills": len(self._unused_fills),
            },
        )
        return fills

    def _pop_replay_fill(self, snapshot: MarketSnapshot, order: Order) -> Fill | None:
        for index, fill in enumerate(self._unused_fills):
            if fill.symbol != order.symbol or fill.side != order.side:
                continue
            if fill.timestamp != snapshot.timestamp:
                continue
            return self._unused_fills.pop(index)
        return None


def load_replay_fills_csv(path: str | Path) -> list[Fill]:
    fills: list[Fill] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            timestamp = _parse_datetime(row.get("timestamp") or row.get("filled_at") or row.get("fill_time"))
            side = Side(str(row.get("side", "")).strip().lower())
            reference_price = _float_or_none(row.get("reference_price"))
            fill_price = float(row.get("fill_price") or row.get("price") or 0.0)
            slippage = 0.0 if reference_price is None else fill_price - reference_price
            fills.append(
                Fill(
                    symbol=str(row.get("symbol", "")).strip(),
                    side=side,
                    quantity=float(row.get("quantity") or 0.0),
                    price=fill_price,
                    commission=float(row.get("commission") or 0.0),
                    timestamp=timestamp,
                    requested_quantity=_float_or_none(row.get("requested_quantity")),
                    latency_steps=int(float(row.get("latency_steps") or 0.0)),
                    liquidity_available=_float_or_none(row.get("liquidity_available")),
                    fill_ratio=float(row.get("fill_ratio") or 1.0),
                    slippage=slippage,
                    status=str(row.get("status") or "filled"),
                )
            )
    return fills


def _quote_for(snapshot: MarketSnapshot, symbol: str) -> dict[str, Any] | None:
    for key in ("quotes", "quote_replay", "top_of_book"):
        payload = snapshot.alt_data.get(key)
        if isinstance(payload, dict):
            value = payload.get(symbol)
            if isinstance(value, dict):
                return value
    return None


def _quote_spread_bps(quote: dict[str, Any] | None, mid: float) -> float | None:
    if not quote:
        return None
    explicit = _float_or_none(quote.get("spread_bps"))
    if explicit is not None:
        return explicit
    bid = _float_or_none(quote.get("bid")) or _float_or_none(quote.get("bid_price"))
    ask = _float_or_none(quote.get("ask")) or _float_or_none(quote.get("ask_price"))
    if bid is None or ask is None or mid <= 0:
        return None
    return max(0.0, (ask - bid) / mid * 10_000.0)


def _level2_available(snapshot: MarketSnapshot, symbol: str, side: Side) -> float | None:
    payload = snapshot.alt_data.get("level2") or snapshot.alt_data.get("order_book")
    if not isinstance(payload, dict):
        return None
    book = payload.get(symbol)
    if not isinstance(book, dict):
        return None
    if side == Side.BUY:
        explicit = _float_or_none(book.get("ask_size")) or _float_or_none(book.get("ask_quantity"))
        levels = book.get("asks")
    else:
        explicit = _float_or_none(book.get("bid_size")) or _float_or_none(book.get("bid_quantity"))
        levels = book.get("bids")
    if explicit is not None:
        return max(0.0, explicit)
    if not isinstance(levels, list):
        return None
    total = 0.0
    for level in levels:
        if isinstance(level, dict):
            total += max(0.0, _float_or_none(level.get("size") or level.get("quantity")) or 0.0)
        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            total += max(0.0, _float_or_none(level[1]) or 0.0)
    return total


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        raise ValueError("Replay fill rows require timestamp, filled_at, or fill_time")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
