"""Tool plugins for simulation, features, risk, optimization, and backtesting."""

from tradearena.tools.backtester import BacktestResult, Backtester
from tradearena.tools.calibration import (
    ExecutionCalibrationConfig,
    discover_ohlcv_files,
    summarize_execution_calibration,
    write_calibration_json,
    write_calibration_markdown,
)
from tradearena.tools.features import RollingFeatureStore
from tradearena.tools.optimizer import EqualRiskBudgetOptimizer
from tradearena.tools.risk import RiskCalculator
from tradearena.tools.simulator import RealisticOrderSimulator, SimpleOrderSimulator

__all__ = [
    "BacktestResult",
    "Backtester",
    "ExecutionCalibrationConfig",
    "EqualRiskBudgetOptimizer",
    "RiskCalculator",
    "RollingFeatureStore",
    "RealisticOrderSimulator",
    "SimpleOrderSimulator",
    "discover_ohlcv_files",
    "summarize_execution_calibration",
    "write_calibration_json",
    "write_calibration_markdown",
]
