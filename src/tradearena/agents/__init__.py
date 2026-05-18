"""Baseline trading agents."""

from tradearena.agents.analysts import MacroNewsAnalyst, MomentumAnalyst
from tradearena.agents.execution import TargetWeightExecutionAgent
from tradearena.agents.llm import ChatCompletionsLLMAnalyst, DeepSeekLLMAnalyst
from tradearena.agents.portfolio import EqualWeightPortfolioManager
from tradearena.agents.risk import MaxPositionRiskManager, NoRiskManager
from tradearena.agents.strategy import (
    BuyAndHoldStrategy,
    MeanVarianceStrategy,
    MemoryAwareSignalWeightedStrategy,
    SignalWeightedStrategy,
)

__all__ = [
    "BuyAndHoldStrategy",
    "ChatCompletionsLLMAnalyst",
    "DeepSeekLLMAnalyst",
    "EqualWeightPortfolioManager",
    "MacroNewsAnalyst",
    "MaxPositionRiskManager",
    "MeanVarianceStrategy",
    "MemoryAwareSignalWeightedStrategy",
    "MomentumAnalyst",
    "NoRiskManager",
    "SignalWeightedStrategy",
    "TargetWeightExecutionAgent",
]
