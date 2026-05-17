<p align="center">
  <img src="docs/assets/tradearena_wordmark.svg"
       alt="TradeArena wordmark"
       width="780">
</p>

<p align="center">
  <strong>
    Open-source benchmark and audit framework for evaluating LLM trading agents
    under realistic execution, risk, and replayability constraints.
  </strong>
</p>

<p align="center">
  <a href="https://github.com/weich97/TradeArena/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/weich97/TradeArena/actions/workflows/ci.yml/badge.svg">
  </a>
  <a href="https://github.com/weich97/TradeArena/actions/workflows/codeql.yml">
    <img alt="CodeQL" src="https://github.com/weich97/TradeArena/actions/workflows/codeql.yml/badge.svg">
  </a>
  <a href="https://github.com/weich97/TradeArena/releases/latest">
    <img alt="Release" src="https://img.shields.io/github/v/release/weich97/TradeArena">
  </a>
  <a href="https://pypi.org/project/tradearena-benchmark/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/tradearena-benchmark">
  </a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10--3.12-0f172a">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-f59e0b">
</p>

<p align="center">
  <a href="docs/getting_started.md">Getting started</a> |
  <a href="https://pypi.org/project/tradearena-benchmark/">PyPI</a> |
  <a href="https://weich97.github.io/TradeArena/">Project site</a> |
  <a href="https://weich97.github.io/TradeArena/benchmark-v0.1.html">Benchmark card</a> |
  <a href="docs/benchmark_submissions.md">Submit results</a> |
  <a href="docs/demo_matrix.md">Demo matrix</a> |
  <a href="docs/contributor_roadmap.md">Contribute</a> |
  <a href="SECURITY.md">Security</a>
</p>

# TradeArena

TradeArena turns every trading-agent decision into a traceable trajectory:

```text
observation -> signal -> intended allocation -> risk gate -> order
  -> fill/rejection -> portfolio state -> diagnostic report
```

It is not another "LLM trading bot." It is a framework for asking whether an
LLM trading agent can be audited, reproduced, stress-tested, and constrained
before anyone trusts its headline return.

## Quick Start

```bash
python -m pip install tradearena-benchmark
tradearena --benchmark tradearena-core
```

The PyPI distribution is `tradearena-benchmark` because `tradearena` is already
occupied on PyPI by an unrelated project. The import namespace and CLI remain
`tradearena`.

To run the full local showcase:

```bash
git clone https://github.com/weich97/TradeArena.git
cd TradeArena
python -m pip install -e ".[dev]"
python scripts/run_showcase.py
```

Then open:

```text
outputs/examples/index.html
```

The first-run path uses deterministic agents, tracked snapshots, and local demo
artifacts. It does not call DeepSeek, Poe, OpenAI, Hugging Face, AkShare, Yahoo
Finance, or broker APIs unless you opt into advanced experiments.

No local install yet?

<p>
  <a href="https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=weich97/TradeArena">
    <img alt="Open in GitHub Codespaces"
         src="https://img.shields.io/badge/Open%20in-Codespaces-181717?logo=github">
  </a>
  <a href="https://colab.research.google.com/github/weich97/TradeArena/blob/main/notebooks/tradearena_5min_colab.ipynb">
    <img alt="Open in Colab"
         src="https://colab.research.google.com/assets/colab-badge.svg">
  </a>
</p>

## Install And Run

From a clone:

```bash
python -m pip install -e ".[dev]"
tradearena --benchmark tradearena-core
python -m tradearena.cli --benchmark tradearena-core
```

From GitHub without cloning first:

```bash
python -m pip install "git+https://github.com/weich97/TradeArena.git"
tradearena --benchmark tradearena-core
```

The historical implementation package `trading_agent_os` remains available as a
compatibility namespace.

## Benchmark Result

The v0.1 benchmark card makes one compact claim:

> LLM trading-agent evaluation changes materially once intended allocations
> pass through auditable risk gates and realistic execution constraints.

Open:

- Static page:
  [`weich97.github.io/TradeArena/benchmark-v0.1.html`](https://weich97.github.io/TradeArena/benchmark-v0.1.html)
- Markdown artifact:
  [`docs/results/benchmark_v0_1.md`](docs/results/benchmark_v0_1.md)
- Community registry:
  [`docs/results/community_registry.md`](docs/results/community_registry.md)

Rebuild:

```bash
python scripts/build_benchmark_page.py
python scripts/build_benchmark_registry.py examples/benchmark_submissions
```

## Submit Or Validate A Benchmark Row

TradeArena supports redacted benchmark submissions. They share scenario,
execution, risk, metrics, and reproducibility metadata without exposing raw
provider prompts, responses, credentials, or private portfolios.

```bash
tradearena validate-submission examples/benchmark_submissions/example_redacted_submission.json
tradearena build-registry examples/benchmark_submissions --output docs/results/community_registry.md
tradearena hash-run outputs/examples/audit_walkthrough_trajectory.json
```

See [`docs/benchmark_submissions.md`](docs/benchmark_submissions.md).

## Visual Preview

<table>
  <tr>
    <th>Audit lifecycle</th>
    <th>Execution realism</th>
    <th>Diagnostic loop</th>
  </tr>
  <tr>
    <td>
      <img src="docs/assets/readme_audit_lifecycle.gif"
           alt="Animated observe-plan-risk-execute-reflect audit trace"
           width="280">
    </td>
    <td>
      <img src="docs/assets/readme_execution_realism.gif"
           alt="Animated execution comparison of ideal, realistic, high-spread,
                low-liquidity, and high-latency fills"
           width="280">
    </td>
    <td>
      <img src="docs/assets/readme_diagnostics_loop.gif"
           alt="Animated representation, risk-feedback, and concentration diagnostics"
           width="280">
    </td>
  </tr>
</table>

The browser-playable launch video is here:
[`weich97.github.io/TradeArena/demo_video.html`](https://weich97.github.io/TradeArena/demo_video.html).

## What TradeArena Provides

| Need | TradeArena surface |
| --- | --- |
| Replayable decisions | Trajectory logs with prompts, memory digests, risk reports, fills, and metrics |
| Execution realism | Fees, spread, slippage, latency, liquidity caps, partial fills, and rejections |
| Risk-aware evaluation | Pre-trade gates, in-trade monitors, post-trade attribution, violations |
| Extensibility | Data, analyst, strategy, risk, simulator, memory, planner, evaluator plugins |
| Community benchmarks | Redacted submission schema, registry builder, reproducibility hashes |

## Extension Path

Start with one small plugin:

```bash
python examples/custom_plugin_demo.py
python examples/extension_walkthrough_demo.py
```

The walkthrough swaps in a custom analyst, risk manager, and evaluator while
reusing the existing runner, data provider, strategy, execution simulator,
memory store, trajectory logger, and metric stack.

Useful entry points:

- [`examples/README.md`](examples/README.md)
- [`docs/demo_matrix.md`](docs/demo_matrix.md)
- [`docs/extension_walkthrough.md`](docs/extension_walkthrough.md)
- [`docs/contributor_roadmap.md`](docs/contributor_roadmap.md)

## Documentation Map

- Quickstart: [`docs/getting_started.md`](docs/getting_started.md)
- Schemas: [`docs/schemas.md`](docs/schemas.md)
- Benchmark submissions: [`docs/benchmark_submissions.md`](docs/benchmark_submissions.md)
- Related work: [`docs/related_work.md`](docs/related_work.md)
- Retail planning sandbox: [`docs/retail_planning.md`](docs/retail_planning.md)
- Research protocol: [`docs/research_protocol.md`](docs/research_protocol.md)
- Security policy: [`SECURITY.md`](SECURITY.md)
- Governance: [`GOVERNANCE.md`](GOVERNANCE.md)

## Local Checks

Each checkout can use its own `.venv`, so public and private repos do not
fight over editable installs:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_local.ps1
```

The script installs the current checkout in editable mode, runs compile checks,
Ruff critical checks, tests, release-readiness checks, submission validation,
artifact-contract validation, and JSON validation.

## Safety Boundary

TradeArena does not promise profitable trading, does not provide financial
advice, and does not execute live trades by default. Public examples are
offline, paper-only, or human-review oriented. Broker and provider integrations
must follow [`SECURITY.md`](SECURITY.md) and [`GOVERNANCE.md`](GOVERNANCE.md).

## Cite

See [`CITATION.cff`](CITATION.cff). If you use TradeArena in research or
software, cite the repository release you used.
