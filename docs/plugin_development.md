# Plugin Development Guide

TreLLM plugins are small Python objects that implement one narrow protocol:
data, analyst, strategy, risk, execution, simulator, memory, or evaluator. The
runner owns orchestration; plugins own one behavior boundary.

## Start From A Scaffold

```bash
tradearena new-plugin --type risk --name max-drawdown-guard
```

This creates a local plugin skeleton under `plugins/local/` with:

- a Python module;
- a README that states the interface contract;
- a pytest file that checks the generated class can be imported.

Use `--output path/to/plugins` to choose a different destination.

## Interface Contracts

The canonical protocols live in
[`src/tradearena/core/interfaces.py`](../src/tradearena/core/interfaces.py).
Each plugin should keep inputs and outputs explicit.

| Plugin type | Required methods | Main input | Main output | Typical test |
| --- | --- | --- | --- | --- |
| `data` | `stream()` | none or config | `list[MarketSnapshot]` | deterministic snapshot count and symbols |
| `analyst` | `analyze()` | snapshot, portfolio, memory | `list[Signal]` | score range, confidence range, no missing symbols |
| `strategy` | `decide()` | snapshot, signals, portfolio, memory | `list[Decision]` | target weights and side consistency |
| `risk` | `approve()`, `monitor()`, `attribute()` | decisions, orders, fills, portfolio | decisions, `RiskReport`, `RiskAttribution` | clipped or blocked decisions and report metadata |
| `execution` | `create_orders()` | approved decisions, portfolio | `list[Order]` | order side, quantity, and min-trade behavior |
| `simulator` | `execute()` | snapshot, orders, portfolio | `list[Fill]` | cash/inventory invariants and report fields |
| `memory` | `record()` | event type, payload | side effect | stored event and redaction behavior |
| `evaluator` | `evaluate()` | trajectory | metric dict | stable keys and numeric bounds |

## Minimal Risk Plugin Shape

```python
from dataclasses import dataclass

from tradearena.agents.risk import MaxPositionRiskManager
from tradearena.core.domain import Decision, MarketSnapshot, PortfolioState, Side


@dataclass
class MaxDrawdownGuard(MaxPositionRiskManager):
    name: str = "max-drawdown-guard"
    initial_equity: float = 100_000.0
    max_drawdown: float = -0.10

    def approve(
        self,
        snapshot: MarketSnapshot,
        decisions: list[Decision],
        portfolio: PortfolioState,
        memory: object,
    ) -> list[Decision]:
        approved = super().approve(snapshot, decisions, portfolio, memory)
        current_drawdown = portfolio.equity() / max(1e-9, self.initial_equity) - 1.0
        if current_drawdown <= self.max_drawdown:
            return [
                Decision(
                    symbol=decision.symbol,
                    side=Side.HOLD,
                    target_weight=0.0,
                    confidence=decision.confidence,
                    rationale=f"blocked by drawdown guard: {decision.rationale}",
                    metadata={**decision.metadata, "risk_blocked": "max_drawdown"},
                )
                for decision in approved
            ]
        return approved
```

Keep plugin-specific state small. If a plugin needs long memory, store records
through a `MemoryStore` rather than hidden module globals.

## Provider Adapters

LLM adapters should use the chat-completions-compatible analyst path whenever
possible. The built-in `poe-llm`, `deepseek-llm`, and `chat-completions-llm`
entries share the same parser and cache policy so model comparisons do not
depend on separate prompt formats.

Recommended provider metadata:

- public provider family, for example `poe`, `openai-compatible`, or `local`;
- redacted model identifier when the exact model is private;
- prompt mode, response format, and parse coverage;
- cache path under an ignored directory if raw provider text is retained
  locally.

## Tests

A useful plugin PR should include one narrow test:

```bash
python -m pytest tests/test_your_plugin.py -q
```

The test should avoid live APIs by default. For model or broker integrations,
add a cache-backed or mock-backed path and document the live environment
variables separately.

## Documentation Checklist

Every contributed plugin should state:

- which protocol it implements;
- whether it is deterministic, cache-backed, or live-provider backed;
- which command reproduces the example;
- what files are safe to commit;
- what data license or provider terms apply;
- what benchmark, if any, the plugin is meant to support.

Raw prompts, raw responses, broker credentials, private holdings, and account
statements should stay out of Git. Use redacted manifests for public benchmark
exchange.
