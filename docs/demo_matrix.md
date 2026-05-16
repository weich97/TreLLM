# Demo Matrix

This matrix maps framework capabilities to hands-on repository artifacts.

| Capability | Run | Main artifact | What it shows |
| --- | --- | --- | --- |
| First-run repo tour | `python scripts/run_showcase.py` | `outputs/examples/showcase.html` | One command builds a public-facing demo surface. |
| Animated visual tour | `python examples/visual_tour_demo.py` | `outputs/examples/visual_tour_index.html` | README-style lifecycle, execution, and diagnostics GIFs become reproducible local artifacts. |
| Auditable trajectories | `python examples/audit_trajectory_walkthrough.py` and `python scripts/render_audit_report.py` | `outputs/examples/audit_report.html` | A decision can be traced from observation to risk gate to fills and memory. |
| Execution realism | `python examples/execution_realism_sweep_demo.py` | `outputs/examples/execution_realism_sweep.svg` | The same agent behaves differently under slippage, latency, liquidity, and rejections. |
| Risk lifecycle | `python examples/ashare_market_rules_demo.py` | `outputs/examples/ashare_market_rules.svg` | Hard market rules become clipped or blocked risk reports. |
| Data extensibility | `python examples/sidecar_data_demo.py` | `outputs/examples/sidecar_data/` | Optional news, macro, filings, and alt-data sidecars enter the observation schema. |
| A-share data bridge | `python examples/akshare_csv_reuse_demo.py` | `outputs/examples/akshare_csv_reuse.svg` | AkShare data can be normalized once and reused by the standard CSV provider. |
| Portfolio baselines | `python examples/portfolio_markowitz_demo.py` | `outputs/examples/portfolio_markowitz.svg` | Buy-and-hold, signal-weighted, and MVO strategies share the same evaluation stack. |
| LLM manifest portability | `python examples/llm_cache_replay_demo.py` | `outputs/examples/llm_cache_replay_summary.json` | Redacted manifests expose provider, model, prompt mode, and parse coverage without raw provider text. |
| Plugin extensibility | `python examples/custom_plugin_demo.py` | `outputs/examples/custom_plugin.svg` | A new analyst can be swapped in without editing the runner, risk, execution, memory, or evaluators. |
| Contributor extension path | `python examples/extension_walkthrough_demo.py` | `outputs/examples/extension_walkthrough.svg` | A contributor can add an analyst, risk manager, and evaluator while reusing the rest of the framework. |
