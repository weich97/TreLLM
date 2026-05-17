# Contributing to TradeArena

TradeArena is designed around narrow interfaces. A useful contribution usually
adds one small component, one clear demo, and one smoke test.

## Local Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest tests -q
python scripts/run_showcase.py --reuse-existing
```

Run the full offline-friendly showcase before a larger pull request:

```bash
python scripts/run_showcase.py
python scripts/check_release_readiness.py
```

## Good First Contributions

- Add a new analyst example under `examples/`.
- Add a CSV sidecar example for a new data field.
- Add a risk metric to `RiskAuditEvaluator`.
- Add a small visualization for an existing JSON or CSV output.
- Improve the HTML audit report navigation.
- Add documentation that maps a paper claim to a runnable script.

## Research Extensions

- A PPO or FinRL baseline on the 51-stock intraday panel.
- A direct provider adapter for a non-Poe frontier model endpoint.
- A limit-order-book execution simulator.
- A new dense embedding or hidden-state probe.
- A human annotation workflow for hallucination and audit-proxy calibration.
- An A-share sector panel and cross-market model comparison.

## Interface Pointers

Core protocols live in `src/trading_agent_os/core/interfaces.py`.

Common extension points:

- `MarketDataProvider`
- `AnalystAgent`
- `StrategyAgent`
- `RiskManagerAgent`
- `ExecutionAgent`
- `OrderSimulator`
- `MemoryStore`
- `Evaluator`

The fastest pattern is `examples/custom_plugin_demo.py`: it adds one analyst and
leaves the rest of the framework unchanged.

## Demo Standards

Every public demo should:

- Run without API keys unless the filename or docs clearly say otherwise.
- Write artifacts under `outputs/examples/`.
- Keep generated raw outputs out of Git unless they are small, stable paper
  artifacts.
- Avoid storing credentials, private data, or live trading endpoints.
- Include a short explanation in `examples/README.md`.

## Testing

Before opening a pull request:

```bash
python -m compileall src scripts examples tests -q
python -m pytest tests -q
python scripts/check_release_readiness.py
```

If your change affects a demo, run that demo directly and include the output path
in the pull request description.

## Data And Model Artifacts

Small reproducibility inputs can be tracked. Large generated trajectories, model
weights, and fresh raw outputs should stay outside Git. See
`docs/artifact_portability.md` for the current policy.

LLM responses are cacheable under `data/llm_cache/`, but API keys must never be
committed.
