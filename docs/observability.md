# Observability Roadmap

TreLLM trajectories are already structured logs. The next step is to make
them portable into common experiment-tracking and trace-inspection systems
without changing the runner.

## Trace Mapping

| TreLLM record | OpenTelemetry-style span | Evals or trace-style field |
| --- | --- | --- |
| market snapshot | `market.observe` | input context |
| analyst signal | `agent.analyze` | tool or model-derived signal |
| strategy decision | `agent.decide` | output candidate |
| risk report | `risk.approve` or `risk.monitor` | grader or guardrail result |
| order and fill | `execution.simulate` | tool call and tool result |
| memory record | `agent.memory` | state update |
| evaluator metrics | `eval.metrics` | score payload |

## Export Targets

| Target | Useful for | Design constraint |
| --- | --- | --- |
| OpenTelemetry | local span inspection and service traces | no raw provider text by default |
| W&B | experiment dashboards and artifact lineage | optional dependency and offline mode |
| MLflow | metric comparison and artifact tracking | plain file-store support first |
| OpenAI Evals-style JSON | evaluation exchange | preserve redaction boundaries |
| LangSmith-style traces | agent step inspection | map risk and execution as explicit tools |

## Implementation Principles

- Exporters should be optional and disabled by default.
- Raw prompts and responses should be excluded unless the user opts in locally.
- Every exported artifact should include scenario, data, risk, execution, agent,
  and hash metadata.
- Exporters should accept an existing trajectory JSON rather than rerunning an
  experiment.

## First Implementable Slice

1. Add `tradearena export-trace trajectory.json --format opentelemetry-json`.
2. Convert each step into spans with stable parent IDs.
3. Add a fixture-based test that verifies span count, event names, and redacted
   fields.
4. Document one local viewer command.

This keeps observability work useful without adding live services to the default
path.

The first slice is now implemented as a local JSON exporter:

```bash
tradearena export-trace outputs/examples/audit_walkthrough_trajectory.json \
  --format opentelemetry-json \
  --output outputs/examples/audit_walkthrough_trace.json
```

The exporter reads an existing trajectory and does not rerun experiments. It
emits `market.observe`, `agent.analyze`, `agent.decide`, `risk.approve`, and
`execution.simulate` spans with stable parent IDs. Raw prompts, raw responses,
and raw rationales are excluded; model and memory identifiers are represented
as hashes or structured counts.
