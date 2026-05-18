from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class StepRecord:
    timestamp: datetime
    observation: dict[str, Any]
    signals: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    approved_decisions: list[dict[str, Any]]
    orders: list[dict[str, Any]]
    fills: list[dict[str, Any]]
    portfolio: dict[str, Any]
    reproducibility_state: dict[str, Any] = field(default_factory=dict)
    agent_trace: dict[str, Any] = field(default_factory=dict)
    risk_report: dict[str, Any] = field(default_factory=dict)
    in_trade_report: dict[str, Any] = field(default_factory=dict)
    post_trade_report: dict[str, Any] = field(default_factory=dict)
    execution_report: dict[str, Any] = field(default_factory=dict)
    risk_violations: list[dict[str, Any]] = field(default_factory=list)
    memory_events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Trajectory:
    experiment_name: str
    seed: int
    steps: list[StepRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def append(self, step: StepRecord) -> None:
        self.steps.append(step)

    def equity_curve(self) -> list[tuple[datetime, float]]:
        return [(step.timestamp, float(step.portfolio["equity"])) for step in self.steps]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
