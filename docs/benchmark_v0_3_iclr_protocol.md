# TreLLM v0.3 ICLR Protocol

`benchmarks/v0.3-iclr/protocol.json` is the draft research contract for moving
TreLLM from a public leaderboard release toward an ICLR-grade LLM financial-agent
evaluation protocol.

The protocol keeps the system boundary explicit:

- TreLLM is the audit, control, execution-calibration, and replayability system.
- TradeArena is the public leaderboard and benchmark-card surface for comparable
  auditable runs.

## Why v0.3 Exists

The v0.2 spec freezes a useful public benchmark card. The v0.3 ICLR protocol
adds the evidence requirements needed for a main-conference reliability claim:

- direct API provider provenance rather than routed-provider headline results;
- execution levels E0, E1, E2, and E3;
- contamination tiers C0, C1, and C2;
- repeated-seed and repeated-sample statistical requirements;
- intent-to-execution, memory-pollution, and risk-intervention mechanism
  metrics;
- FinAudit trace-auditor tasks with injected-defect ground truth;
- independent external reproduction reports.

## Validate

```bash
python scripts/validate_benchmark_spec.py benchmarks/v0.3-iclr/protocol.json
```

The validator checks the presence of the ICLR protocol gates. It does not prove
that the experiments have already been run. A missing output table, direct API
pilot, or external reproduction report should still be treated as incomplete
research work.

Validate the direct-provider manifest contract separately:

```bash
python scripts/validate_direct_provider_manifest.py examples/provider_manifests/direct_openai_example.json
```

These manifests bind a direct API call to provider, model, version, prompt hash,
response hash, redaction policy, contamination tier, execution level, seed,
sample index, and trajectory-manifest hash. Routed-provider rows must not use
this contract for headline v0.3 evidence.

## Claim Boundary

Use the v0.3 protocol to support this kind of claim:

> TreLLM evaluates how LLM financial-agent conclusions change under execution
> assumptions, contamination controls, risk gates, and audit-trace defects.

Do not use the v0.3 protocol to claim:

> An LLM is proven to be profitable in live trading.
