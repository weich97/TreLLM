from __future__ import annotations

from dataclasses import dataclass, field

from tradearena.core.domain import (
    Decision,
    Fill,
    MarketSnapshot,
    Order,
    PortfolioState,
    RiskAttribution,
    RiskBudget,
    RiskCheck,
    RiskPhase,
    RiskReport,
    RiskViolation,
    Side,
)


@dataclass
class MaxPositionRiskManager:
    max_abs_weight: float = 0.35
    min_confidence: float = 0.05
    max_gross_exposure: float = 1.0
    max_single_step_turnover: float = 0.75
    max_order_participation: float = 0.05
    max_latency_steps: int = 2
    max_slippage_bps: float = 50.0
    name: str = "max-position-risk"
    last_report: RiskReport | None = field(default=None, init=False)

    def budget(self) -> RiskBudget:
        return RiskBudget(
            max_position_weight=self.max_abs_weight,
            max_gross_exposure=self.max_gross_exposure,
            max_single_step_turnover=self.max_single_step_turnover,
            max_order_participation=self.max_order_participation,
            min_confidence=self.min_confidence,
            max_latency_steps=self.max_latency_steps,
            max_slippage_bps=self.max_slippage_bps,
        )

    def approve(self, snapshot: MarketSnapshot, decisions: list[Decision], portfolio: PortfolioState, memory: object) -> list[Decision]:
        approved = []
        checks: list[RiskCheck] = []
        violations: list[RiskViolation] = []
        blocked_count = 0
        clipped_count = 0
        projected_turnover = 0.0
        for decision in decisions:
            target = max(-self.max_abs_weight, min(self.max_abs_weight, decision.target_weight))
            side = decision.side
            rationale = decision.rationale
            metadata = dict(decision.metadata)

            if decision.confidence < self.min_confidence:
                target = 0.0
                side = Side.HOLD
                rationale = f"blocked by confidence floor: {rationale}"
                metadata["risk_blocked"] = "low_confidence"
                blocked_count += 1
                checks.append(
                    RiskCheck(
                        name="min_confidence",
                        passed=False,
                        severity="error",
                        message=f"{decision.symbol} confidence {decision.confidence:.3f} below {self.min_confidence:.3f}",
                    )
                )
                violations.append(
                    RiskViolation(
                        phase=RiskPhase.PRE_TRADE,
                        constraint="min_confidence",
                        severity="error",
                        observed=decision.confidence,
                        limit=self.min_confidence,
                        message=f"{decision.symbol} blocked by confidence floor",
                        symbol=decision.symbol,
                    )
                )
            elif target != decision.target_weight:
                metadata["risk_clipped_from"] = decision.target_weight
                clipped_count += 1
                checks.append(
                    RiskCheck(
                        name="max_abs_weight",
                        passed=True,
                        severity="warning",
                        message=f"{decision.symbol} target clipped from {decision.target_weight:.3f} to {target:.3f}",
                    )
                )

            projected_turnover += abs(target - portfolio.weight(decision.symbol))

            approved.append(
                Decision(
                    symbol=decision.symbol,
                    side=side,
                    target_weight=target,
                    confidence=decision.confidence,
                    rationale=rationale,
                    metadata=metadata,
                )
            )

        gross = sum(abs(decision.target_weight) for decision in approved)
        if gross > self.max_gross_exposure:
            scale = self.max_gross_exposure / gross
            clipped_count += len(approved)
            approved = [
                Decision(
                    symbol=decision.symbol,
                    side=decision.side if abs(decision.target_weight * scale) > 1e-12 else Side.HOLD,
                    target_weight=decision.target_weight * scale,
                    confidence=decision.confidence,
                    rationale=decision.rationale,
                    metadata={**decision.metadata, "risk_scaled_by": scale},
                )
                for decision in approved
            ]
            checks.append(
                RiskCheck(
                    name="max_gross_exposure",
                    passed=True,
                    severity="warning",
                    message=f"gross exposure {gross:.3f} scaled to {self.max_gross_exposure:.3f}",
                )
            )

        if projected_turnover > self.max_single_step_turnover:
            checks.append(
                RiskCheck(
                    name="max_single_step_turnover",
                    passed=False,
                    severity="warning",
                    message=f"projected turnover {projected_turnover:.3f} exceeds {self.max_single_step_turnover:.3f}",
                    metadata={"projected_turnover": projected_turnover},
                )
            )
            violations.append(
                RiskViolation(
                    phase=RiskPhase.PRE_TRADE,
                    constraint="max_single_step_turnover",
                    severity="warning",
                    observed=projected_turnover,
                    limit=self.max_single_step_turnover,
                    message="projected turnover exceeds configured risk budget",
                )
            )

        if not checks:
            checks.append(RiskCheck(name="all_constraints", passed=True, severity="info", message="all risk constraints passed"))

        self.last_report = RiskReport(
            timestamp=snapshot.timestamp,
            checks=tuple(checks),
            approved_count=len(approved),
            blocked_count=blocked_count,
            clipped_count=clipped_count,
            phase=RiskPhase.PRE_TRADE,
            budget=self.budget(),
            violations=tuple(violations),
        )
        return approved

    def monitor(
        self,
        snapshot: MarketSnapshot,
        orders: list[Order],
        fills: list[Fill],
        portfolio: PortfolioState,
        memory: object,
    ) -> RiskReport:
        checks: list[RiskCheck] = []
        violations: list[RiskViolation] = []
        for fill in fills:
            bar = snapshot.bars.get(fill.symbol)
            if bar is None:
                continue
            participation = fill.quantity / max(1.0, bar.volume)
            slippage_bps = abs(fill.slippage) / max(1e-9, snapshot.price(fill.symbol)) * 10_000
            if participation > self.max_order_participation:
                violations.append(
                    RiskViolation(
                        phase=RiskPhase.IN_TRADE,
                        constraint="max_order_participation",
                        severity="warning",
                        observed=participation,
                        limit=self.max_order_participation,
                        message="fill exceeded participation risk budget",
                        symbol=fill.symbol,
                    )
                )
            if fill.latency_steps > self.max_latency_steps:
                violations.append(
                    RiskViolation(
                        phase=RiskPhase.IN_TRADE,
                        constraint="max_latency_steps",
                        severity="warning",
                        observed=fill.latency_steps,
                        limit=self.max_latency_steps,
                        message="execution latency exceeded risk budget",
                        symbol=fill.symbol,
                    )
                )
            if slippage_bps > self.max_slippage_bps:
                violations.append(
                    RiskViolation(
                        phase=RiskPhase.IN_TRADE,
                        constraint="max_slippage_bps",
                        severity="warning",
                        observed=slippage_bps,
                        limit=self.max_slippage_bps,
                        message="slippage exceeded risk budget",
                        symbol=fill.symbol,
                    )
                )

        if violations:
            checks.extend(
                RiskCheck(
                    name=violation.constraint,
                    passed=False,
                    severity=violation.severity,
                    message=violation.message,
                    metadata={"observed": violation.observed, "limit": violation.limit, "symbol": violation.symbol},
                )
                for violation in violations
            )
        else:
            checks.append(RiskCheck(name="in_trade_monitor", passed=True, severity="info", message="execution within risk budget"))

        report = RiskReport(
            timestamp=snapshot.timestamp,
            checks=tuple(checks),
            approved_count=len(orders),
            blocked_count=0,
            clipped_count=0,
            phase=RiskPhase.IN_TRADE,
            budget=self.budget(),
            violations=tuple(violations),
        )
        self.last_report = report
        return report

    def attribute(
        self,
        snapshot: MarketSnapshot,
        fills: list[Fill],
        portfolio: PortfolioState,
        memory: object,
    ) -> RiskAttribution:
        exposure = {symbol: portfolio.weight(symbol) for symbol in snapshot.bars}
        attribution = RiskAttribution(
            timestamp=snapshot.timestamp,
            realized_pnl=portfolio.realized_pnl,
            commission=sum(fill.commission for fill in fills),
            slippage_cost=sum(abs(fill.slippage) * fill.quantity for fill in fills),
            exposure=exposure,
            notes=("post-trade attribution computed from simulated fills",),
        )
        return attribution


@dataclass
class NoRiskManager:
    name: str = "no-risk"
    last_report: RiskReport | None = field(default=None, init=False)

    def budget(self) -> RiskBudget:
        return RiskBudget(max_position_weight=1.0, max_gross_exposure=10.0, max_single_step_turnover=10.0)

    def approve(self, snapshot: MarketSnapshot, decisions: list[Decision], portfolio: PortfolioState, memory: object) -> list[Decision]:
        self.last_report = RiskReport(
            timestamp=snapshot.timestamp,
            checks=(RiskCheck(name="disabled", passed=True, severity="info", message="risk gate disabled"),),
            approved_count=len(decisions),
            blocked_count=0,
            clipped_count=0,
            phase=RiskPhase.PRE_TRADE,
            budget=self.budget(),
        )
        return decisions

    def monitor(self, snapshot: MarketSnapshot, orders: list[Order], fills: list[Fill], portfolio: PortfolioState, memory: object) -> RiskReport:
        return RiskReport(
            timestamp=snapshot.timestamp,
            checks=(RiskCheck(name="disabled", passed=True, severity="info", message="in-trade risk monitor disabled"),),
            approved_count=len(orders),
            blocked_count=0,
            clipped_count=0,
            phase=RiskPhase.IN_TRADE,
            budget=self.budget(),
        )

    def attribute(self, snapshot: MarketSnapshot, fills: list[Fill], portfolio: PortfolioState, memory: object) -> RiskAttribution:
        return RiskAttribution(
            timestamp=snapshot.timestamp,
            realized_pnl=portfolio.realized_pnl,
            commission=sum(fill.commission for fill in fills),
            slippage_cost=sum(abs(fill.slippage) * fill.quantity for fill in fills),
            exposure={symbol: portfolio.weight(symbol) for symbol in snapshot.bars},
            notes=("post-trade attribution computed with risk gate disabled",),
        )
