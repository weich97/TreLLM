from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from math import isfinite

from tradearena.core.domain import Decision, MarketSnapshot, PortfolioState, Side, Signal


@dataclass
class SignalWeightedStrategy:
    max_long_weight: float = 0.8
    max_short_weight: float = 0.0
    deadband: float = 0.01
    name: str = "signal-weighted-strategy"

    def decide(self, snapshot: MarketSnapshot, signals: list[Signal], portfolio: PortfolioState, memory: object) -> list[Decision]:
        grouped: dict[str, list[Signal]] = {}
        for signal in signals:
            grouped.setdefault(signal.symbol, []).append(signal)

        decisions: list[Decision] = []
        for symbol in snapshot.bars:
            symbol_signals = grouped.get(symbol, [])
            if not symbol_signals:
                combined = 0.0
                confidence = 0.0
                rationale = "no signals"
            else:
                weight_sum = sum(max(0.01, signal.confidence) for signal in symbol_signals)
                combined = sum(signal.score * max(0.01, signal.confidence) for signal in symbol_signals) / weight_sum
                confidence = min(1.0, weight_sum / max(1, len(symbol_signals)))
                rationale = " | ".join(signal.rationale for signal in symbol_signals)

            if combined > self.deadband:
                target = min(self.max_long_weight, combined * 5.0)
                side = Side.BUY
            elif combined < -self.deadband and self.max_short_weight > 0:
                target = max(-self.max_short_weight, combined * 5.0)
                side = Side.SELL
            else:
                target = 0.0
                side = Side.HOLD

            decisions.append(
                Decision(
                    symbol=symbol,
                    side=side,
                    target_weight=target,
                    confidence=confidence,
                    rationale=rationale,
                    metadata={"combined_score": combined, "strategy": self.name},
                )
            )
        return decisions


@dataclass
class BuyAndHoldStrategy:
    target_weight: float = 1.0
    name: str = "buy-and-hold"

    def decide(self, snapshot: MarketSnapshot, signals: list[Signal], portfolio: PortfolioState, memory: object) -> list[Decision]:
        if not snapshot.bars:
            return []
        target = self.target_weight / len(snapshot.bars)
        return [
            Decision(
                symbol=symbol,
                side=Side.BUY,
                target_weight=target,
                confidence=1.0,
                rationale="baseline equal buy-and-hold allocation",
                metadata={"strategy": self.name},
            )
            for symbol in snapshot.bars
        ]


@dataclass
class MeanVarianceStrategy:
    """Classical rolling Markowitz minimum-variance baseline.

    The strategy deliberately uses only realized prices from the current
    trajectory. It is included as a non-LLM quant baseline for experiments that
    compare language-agent behavior against covariance-driven allocation.
    """

    lookback: int = 24
    max_long_weight: float = 0.08
    ridge: float = 1e-4
    name: str = "mean-variance-strategy"
    _history: dict[str, deque[float]] = field(default_factory=dict)

    def decide(self, snapshot: MarketSnapshot, signals: list[Signal], portfolio: PortfolioState, memory: object) -> list[Decision]:
        symbols = sorted(snapshot.bars)
        for symbol in symbols:
            history = self._history.setdefault(symbol, deque(maxlen=self.lookback + 1))
            history.append(float(snapshot.bars[symbol].close))

        weights = self._weights(symbols)
        decisions: list[Decision] = []
        for symbol in symbols:
            target = weights.get(symbol, 0.0)
            side = Side.BUY if target > 1e-6 else Side.HOLD
            decisions.append(
                Decision(
                    symbol=symbol,
                    side=side,
                    target_weight=target,
                    confidence=1.0 if target > 0 else 0.0,
                    rationale="rolling Markowitz minimum-variance allocation using realized covariance only",
                    metadata={
                        "strategy": self.name,
                        "lookback": self.lookback,
                        "ridge": self.ridge,
                        "max_long_weight": self.max_long_weight,
                    },
                )
            )
        return decisions

    def _weights(self, symbols: list[str]) -> dict[str, float]:
        if not symbols:
            return {}
        usable = [symbol for symbol in symbols if len(self._history.get(symbol, ())) >= min(self.lookback + 1, 3)]
        if len(usable) < 2:
            return self._equal_weight(symbols)

        returns_by_symbol: dict[str, list[float]] = {}
        min_len = self.lookback
        for symbol in usable:
            prices = list(self._history[symbol])
            returns = []
            for prev, curr in zip(prices, prices[1:]):
                if prev > 0:
                    returns.append((curr / prev) - 1.0)
            if returns:
                returns_by_symbol[symbol] = returns[-self.lookback :]
                min_len = min(min_len, len(returns_by_symbol[symbol]))
        if len(returns_by_symbol) < 2 or min_len < 2:
            return self._equal_weight(symbols)

        ordered = sorted(returns_by_symbol)
        matrix = [returns_by_symbol[symbol][-min_len:] for symbol in ordered]
        covariance = self._covariance(matrix)
        for idx in range(len(covariance)):
            covariance[idx][idx] += self.ridge

        solution = self._solve(covariance, [1.0] * len(ordered))
        raw = [max(0.0, value) if isfinite(value) else 0.0 for value in solution]
        if sum(raw) <= 1e-12:
            return self._equal_weight(symbols)
        normalized = [value / sum(raw) for value in raw]
        capped = [min(self.max_long_weight, value) for value in normalized]
        total = sum(capped)
        if total <= 1e-12:
            return self._equal_weight(symbols)
        weights = {symbol: value / total for symbol, value in zip(ordered, capped)}
        return {symbol: min(self.max_long_weight, weights.get(symbol, 0.0)) for symbol in symbols}

    def _equal_weight(self, symbols: list[str]) -> dict[str, float]:
        if not symbols:
            return {}
        target = min(self.max_long_weight, 1.0 / len(symbols))
        return {symbol: target for symbol in symbols}

    def _covariance(self, series: list[list[float]]) -> list[list[float]]:
        means = [sum(values) / len(values) for values in series]
        covariance: list[list[float]] = []
        denominator = max(1, len(series[0]) - 1)
        for left, left_mean in zip(series, means):
            row = []
            for right, right_mean in zip(series, means):
                row.append(sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right)) / denominator)
            covariance.append(row)
        return covariance

    def _solve(self, matrix: list[list[float]], vector: list[float]) -> list[float]:
        n = len(vector)
        augmented = [row[:] + [rhs] for row, rhs in zip(matrix, vector)]
        for col in range(n):
            pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
            if abs(augmented[pivot][col]) < 1e-12:
                return [1.0 / n] * n
            augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
            scale = augmented[col][col]
            augmented[col] = [value / scale for value in augmented[col]]
            for row in range(n):
                if row == col:
                    continue
                factor = augmented[row][col]
                augmented[row] = [value - factor * pivot_value for value, pivot_value in zip(augmented[row], augmented[col])]
        return [augmented[row][-1] for row in range(n)]


@dataclass
class MemoryAwareSignalWeightedStrategy:
    """Signal-weighted strategy with a simple audit-memory risk-off overlay."""

    base: SignalWeightedStrategy = field(default_factory=SignalWeightedStrategy)
    lookback_events: int = 5
    drawdown_threshold: float = -0.015
    risk_off_scale: float = 0.65
    recovery_boost: float = 1.08
    name: str = "memory-aware-signal-weighted-strategy"

    def decide(self, snapshot: MarketSnapshot, signals: list[Signal], portfolio: PortfolioState, memory: object) -> list[Decision]:
        decisions = self.base.decide(snapshot, signals, portfolio, memory)
        scale, reason = self._memory_scale(memory)
        adjusted: list[Decision] = []
        for decision in decisions:
            target = decision.target_weight
            if decision.side != Side.HOLD:
                target *= scale
            metadata = dict(decision.metadata)
            metadata.update({"strategy": self.name, "memory_scale": scale, "memory_reason": reason})
            adjusted.append(
                Decision(
                    symbol=decision.symbol,
                    side=decision.side if abs(target) > self.base.deadband else Side.HOLD,
                    target_weight=target if abs(target) > self.base.deadband else 0.0,
                    confidence=decision.confidence,
                    rationale=f"{decision.rationale} | memory overlay: {reason}",
                    metadata=metadata,
                )
            )
        return adjusted

    def _memory_scale(self, memory: object) -> tuple[float, str]:
        recent_fn = getattr(memory, "recent", None)
        if not callable(recent_fn):
            return 1.0, "memory unavailable"
        recent = recent_fn("step", self.lookback_events)
        if len(recent) < 2:
            return 1.0, "insufficient memory"

        equities = []
        rejected_orders = 0
        risk_violations = 0
        for event in recent:
            payload = event.get("payload", {})
            equity = payload.get("equity")
            if isinstance(equity, (int, float)):
                equities.append(float(equity))
            execution_report = payload.get("execution_report", {})
            if isinstance(execution_report, dict):
                rejected_orders += int(execution_report.get("rejected_orders", 0))
            risk_violations += len(payload.get("risk_violations", []) or [])

        if len(equities) >= 2 and equities[0]:
            equity_change = (equities[-1] / equities[0]) - 1.0
        else:
            equity_change = 0.0

        if equity_change <= self.drawdown_threshold or rejected_orders > self.lookback_events or risk_violations:
            return self.risk_off_scale, f"risk-off after recent drawdown/rejections ({equity_change:.3f})"
        if equity_change > abs(self.drawdown_threshold) and rejected_orders == 0:
            return self.recovery_boost, f"modest recovery boost ({equity_change:.3f})"
        return 1.0, f"neutral memory state ({equity_change:.3f})"
