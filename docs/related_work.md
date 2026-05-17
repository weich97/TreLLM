# Related Work And Positioning

TradeArena is designed to complement, not replace, existing financial AI and
agent frameworks. Its niche is auditability, realistic execution, risk gates,
and replayable benchmark artifacts for LLM trading agents.

## Trading-Agent Frameworks

### TradingAgents

TradingAgents focuses on multi-agent LLM trading workflows.

TradeArena is complementary: it focuses on replayable trajectories, risk-gate
intervention logs, execution realism, and benchmark artifacts.

### FinRobot

FinRobot focuses on financial analysis and equity-research agents.

TradeArena is a simulation, audit, and evaluation layer for decision traces
rather than an analyst-only assistant.

## Financial AI And Quant Platforms

### FinRL / FinRL-Meta

FinRL and FinRL-Meta focus on financial reinforcement learning environments and
benchmarks.

TradeArena can host quant or RL-style baselines, but centers LLM decision
chains, tool traces, risk reports, and realistic order simulation.

### FinGPT

FinGPT focuses on financial LLM data and adaptation.

TradeArena evaluates how model-backed agents behave under market constraints,
risk feedback, and execution friction.

### Qlib

Qlib focuses on quantitative investment research workflows.

TradeArena is lighter-weight and agent-native, with emphasis on reproducible
audit logs and execution-aware evaluation.

## Backtesting And Data Tooling

### Backtrader / Zipline

Backtrader and Zipline are classic backtesting engines.

TradeArena adds agent traces, risk lifecycle reports, memory state, and
LLM-specific replay metadata.

### OpenBB

OpenBB focuses on financial data and research tooling.

TradeArena can consume market data adapters, but its core contribution is the
benchmark and audit protocol.

## General Agent Orchestration

### LangGraph / AutoGen / CrewAI

These systems focus on general agent orchestration.

TradeArena provides finance-specific schemas, risk gates, execution simulators,
and trading-agent metrics.

## Why This Distinction Matters

Many trading-agent demos report a return curve. That is not enough for LLM
agents because the result depends on prompt version, retrieved context, tool
outputs, memory state, model version, market timestamp, risk constraints,
portfolio state, execution simulator state, and random seed.

TradeArena asks a different question:

> Can the agent's decision be replayed, audited, risk-checked, and compared
> under realistic execution assumptions?

This makes the framework useful alongside stronger forecasting, research, and
RL systems. Those systems can plug into TradeArena as analysts, strategies, risk
modules, or baselines while the benchmark layer keeps the evaluation traceable.
