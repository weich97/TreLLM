"""TradeArena: pluggable AI trading agent research framework."""

from tradearena.core.domain import (
    Bar,
    Decision,
    AgentProtocolTrace,
    Fill,
    MarketSnapshot,
    Order,
    PortfolioState,
    ReproducibilityState,
    RiskAttribution,
    RiskBudget,
    RiskCheck,
    RiskReport,
    RiskViolation,
    Signal,
)
from tradearena.core.registry import PluginRegistry
from tradearena.core.runner import TradeArena
from tradearena.planning import FinancialGoal, Holding, InvestorProfile, RetailPlanningAgent

__all__ = [
    "Bar",
    "AgentProtocolTrace",
    "Decision",
    "Fill",
    "FinancialGoal",
    "Holding",
    "InvestorProfile",
    "MarketSnapshot",
    "Order",
    "PluginRegistry",
    "PortfolioState",
    "ReproducibilityState",
    "RiskAttribution",
    "RiskBudget",
    "RiskCheck",
    "RiskReport",
    "RiskViolation",
    "RetailPlanningAgent",
    "Signal",
    "TradeArena",
]
