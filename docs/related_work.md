# Related Work And Positioning

TradeArena is designed to complement, not replace, existing financial AI and
agent frameworks. Its niche is auditability, realistic execution, risk gates,
and replayable benchmark artifacts for LLM trading agents.

| Project | Primary orientation | How TradeArena differs |
| --- | --- | --- |
| TradingAgents | Multi-agent LLM trading workflows | TradeArena focuses on replayable trajectories, risk-gate intervention logs, execution realism, and benchmark artifacts. |
| FinRobot | Financial analysis and equity-research agents | TradeArena is a simulation, audit, and evaluation layer for decision traces rather than an analyst-only assistant. |
| FinRL / FinRL-Meta | Financial reinforcement learning environments and benchmarks | TradeArena can host quant/RL baselines, but centers LLM decision chains, tool traces, risk reports, and realistic order simulation. |
| FinGPT | Financial LLM data and adaptation | TradeArena evaluates how model-backed agents behave under market constraints and risk feedback. |
| Qlib | Quantitative investment research platform | TradeArena is lighter-weight and agent-native, with emphasis on reproducible audit logs and execution-aware evaluation. |
| Backtrader / Zipline | Backtesting engines | TradeArena adds agent traces, risk lifecycle reports, memory state, and LLM-specific replay metadata. |
| OpenBB | Financial data and research tooling | TradeArena can consume market data adapters, but its core contribution is benchmark and audit protocol. |
| LangGraph / AutoGen / CrewAI | General agent orchestration | TradeArena provides finance-specific schemas, risk gates, execution simulators, and trading-agent metrics. |

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
