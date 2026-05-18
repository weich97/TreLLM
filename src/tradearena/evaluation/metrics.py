from __future__ import annotations

from dataclasses import dataclass, field

from tradearena.core.domain import Side
from tradearena.core.trajectory import Trajectory
from tradearena.tools.risk import RiskCalculator


@dataclass
class PerformanceEvaluator:
    name: str = "performance-evaluator"
    risk: RiskCalculator = field(default_factory=RiskCalculator)

    def evaluate(self, trajectory: Trajectory) -> dict[str, float | int | str]:
        curve = [equity for _, equity in trajectory.equity_curve()]
        if not curve:
            return {"total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "steps": 0}
        returns = self.risk.returns(curve)
        return {
            "total_return": (curve[-1] / curve[0]) - 1.0 if curve[0] else 0.0,
            "sharpe": self.risk.sharpe(returns),
            "volatility": self.risk.volatility(returns),
            "max_drawdown": self.risk.max_drawdown(curve),
            "steps": len(curve),
            "final_equity": curve[-1],
        }


@dataclass
class BehavioralEvaluator:
    name: str = "behavioral-evaluator"

    def evaluate(self, trajectory: Trajectory) -> dict[str, float | int | str]:
        order_count = sum(len(step.orders) for step in trajectory.steps)
        fill_count = sum(len(step.fills) for step in trajectory.steps)
        hold_decisions = 0
        decisions = 0
        for step in trajectory.steps:
            for decision in step.approved_decisions:
                decisions += 1
                if decision.get("side") == Side.HOLD.value:
                    hold_decisions += 1
        return {
            "order_count": order_count,
            "fill_count": fill_count,
            "turnover_events": fill_count,
            "hold_ratio": hold_decisions / decisions if decisions else 0.0,
        }


@dataclass
class ExecutionRealismEvaluator:
    name: str = "execution-realism-evaluator"

    def evaluate(self, trajectory: Trajectory) -> dict[str, float | int | str]:
        reports = [step.execution_report for step in trajectory.steps if step.execution_report]
        fills = [fill for step in trajectory.steps for fill in step.fills]
        submitted = sum(int(report.get("submitted_orders", 0)) for report in reports)
        filled = sum(int(report.get("filled_orders", 0)) for report in reports)
        partial = sum(int(report.get("partial_fills", 0)) for report in reports)
        rejected = sum(int(report.get("rejected_orders", 0)) for report in reports)
        pending = reports[-1].get("pending_orders", 0) if reports else 0
        commission = sum(float(report.get("total_commission", 0.0)) for report in reports)
        slippage_cost = sum(float(report.get("total_slippage", 0.0)) for report in reports)
        latency = [float(fill.get("latency_steps", 0.0)) for fill in fills]
        fill_ratios = [float(fill.get("fill_ratio", 1.0)) for fill in fills]
        return {
            "submitted_orders": submitted,
            "execution_fill_rate": filled / submitted if submitted else 0.0,
            "partial_fill_count": partial,
            "partial_fill_rate": partial / filled if filled else 0.0,
            "rejected_order_count": rejected,
            "pending_order_count": int(pending),
            "total_commission": commission,
            "total_slippage_cost": slippage_cost,
            "avg_latency_steps": sum(latency) / len(latency) if latency else 0.0,
            "avg_fill_ratio": sum(fill_ratios) / len(fill_ratios) if fill_ratios else 0.0,
        }


@dataclass
class RiskAuditEvaluator:
    name: str = "risk-audit-evaluator"

    def evaluate(self, trajectory: Trajectory) -> dict[str, float | int | str]:
        reports = [step.risk_report for step in trajectory.steps if step.risk_report]
        in_trade_reports = [step.in_trade_report for step in trajectory.steps if step.in_trade_report]
        post_trade_reports = [step.post_trade_report for step in trajectory.steps if step.post_trade_report]
        blocked = sum(int(report.get("blocked_count", 0)) for report in reports)
        clipped = sum(int(report.get("clipped_count", 0)) for report in reports)
        checks = 0
        failed = 0
        warnings = 0
        violation_count = sum(len(step.risk_violations) for step in trajectory.steps)
        severe_violations = 0
        for step in trajectory.steps:
            for violation in step.risk_violations:
                if violation.get("severity") == "error":
                    severe_violations += 1
        for report in reports + in_trade_reports + post_trade_reports:
            for check in report.get("checks", []):
                checks += 1
                if not check.get("passed", True):
                    failed += 1
                if check.get("severity") == "warning":
                    warnings += 1
        reproducibility_fields = (
            "prompt_version",
            "model_version",
            "market_data_timestamp",
            "memory_digest",
            "risk_constraints",
            "portfolio_state",
            "execution_simulator_state",
            "random_seed",
        )
        reproducible_steps = 0
        trace_complete_steps = 0
        for step in trajectory.steps:
            state = step.reproducibility_state
            if state and all(field in state and state[field] not in (None, "") for field in reproducibility_fields):
                reproducible_steps += 1
            trace = step.agent_trace
            if trace and all(key in trace for key in ("observe", "plan", "propose_order", "risk_report", "revise", "act", "reflect")):
                trace_complete_steps += 1
        return {
            "risk_reports": len(reports),
            "in_trade_reports": len(in_trade_reports),
            "post_trade_reports": len(post_trade_reports),
            "risk_blocked_decisions": blocked,
            "risk_clipped_decisions": clipped,
            "risk_check_count": checks,
            "risk_failed_checks": failed,
            "risk_warning_checks": warnings,
            "risk_violation_count": violation_count,
            "severe_risk_violation_count": severe_violations,
            "risk_audit_coverage": len(reports) / len(trajectory.steps) if trajectory.steps else 0.0,
            "risk_lifecycle_coverage": (len(reports) + len(in_trade_reports) + len(post_trade_reports)) / (3 * len(trajectory.steps)) if trajectory.steps else 0.0,
            "trajectory_reproducibility_coverage": reproducible_steps / len(trajectory.steps) if trajectory.steps else 0.0,
            "agent_trace_coverage": trace_complete_steps / len(trajectory.steps) if trajectory.steps else 0.0,
        }


@dataclass
class ReasoningConsistencyEvaluator:
    name: str = "reasoning-consistency-evaluator"

    def evaluate(self, trajectory: Trajectory) -> dict[str, float | int | str]:
        checked = 0
        consistent = 0
        for step in trajectory.steps:
            for decision in step.approved_decisions:
                side = decision.get("side")
                target = float(decision.get("target_weight", 0.0))
                checked += 1
                if side == Side.BUY.value and target > 0:
                    consistent += 1
                elif side == Side.SELL.value and target < 0:
                    consistent += 1
                elif side == Side.HOLD.value and abs(target) < 1e-12:
                    consistent += 1
        return {
            "reasoning_consistency": consistent / checked if checked else 1.0,
            "reasoning_checks": checked,
        }
