from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_agent_os.core.serialization import to_jsonable, write_json
from trading_agent_os.evaluation import BenchmarkCase, BenchmarkRunner
from trading_agent_os.experiments import PaperExperimentConfig, run_paper_experiment
from trading_agent_os.factory import build_default_system, default_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Trading Agent OS experiments.")
    parser.add_argument(
        "--benchmark",
        default="tradearena-core",
        choices=["tradearena-core", "momentum-vs-buyhold"],
        help="Benchmark suite. momentum-vs-buyhold is kept as a compatibility alias.",
    )
    parser.add_argument("--symbols", default="SYN,ALT", help="Comma-separated symbols for synthetic benchmark.")
    parser.add_argument("--periods", type=int, default=120)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--execution", default="realistic", choices=["realistic", "ideal"])
    parser.add_argument(
        "--spread-bps",
        type=float,
        default=0.0,
        help="Full bid-ask spread in basis points for realistic execution; market orders cross half the spread.",
    )
    parser.add_argument("--risk", default="max-position", choices=["max-position", "none"])
    parser.add_argument("--data-source", default="synthetic", choices=["synthetic", "csv"], help="Data source for non-paper benchmarks.")
    parser.add_argument("--output", default="", help="Optional JSON trajectory output path.")
    parser.add_argument("--paper-output", default="", help="Run the paper-grade experiment suite and write tables/charts/artifacts to this directory.")
    parser.add_argument("--paper-seeds", default="3,7,11", help="Comma-separated seeds for --paper-output.")
    parser.add_argument("--no-stress", action="store_true", help="Skip cost/liquidity/latency stress tests in --paper-output.")
    parser.add_argument("--no-extended", action="store_true", help="Skip extended paper ablations in --paper-output.")
    parser.add_argument("--no-real-data", action="store_true", help="Skip historical Yahoo Finance experiments in --paper-output.")
    parser.add_argument("--real-data-dir", default="data/real/yahoo_daily_2021_2026", help="Directory containing normalized historical OHLCV CSV files.")
    parser.add_argument("--real-symbols", default="GSPC,BTC-USD,ETH-USD", help="Comma-separated symbols for historical CSV experiments.")
    parser.add_argument("--real-frequency", default="weekly", choices=["daily", "weekly"], help="Decision frequency for historical CSV experiments.")
    parser.add_argument("--real-start", default="", help="Optional start date for --data-source csv benchmarks.")
    parser.add_argument("--real-end", default="", help="Optional end date for --data-source csv benchmarks.")
    parser.add_argument("--real-max-periods", type=int, default=0, help="Optional max periods for --data-source csv benchmarks.")
    parser.add_argument("--no-llm", action="store_true", help="Skip direct-provider LLM analyst sanity checks in --paper-output.")
    parser.add_argument("--llm-model", default="deepseek-v4-flash", help="Direct-provider model for LLM analyst sanity checks.")
    parser.add_argument("--llm-models", default="deepseek-v4-flash,deepseek-v4-pro", help="Comma-separated direct-provider models for LLM comparison sanity checks.")
    parser.add_argument("--no-model-matrix", action="store_true", help="Skip Poe-mediated frontier model matrix risk-adaptation experiments.")
    parser.add_argument("--model-matrix-models", default="gpt-5.5,gemini-3.1-pro,kimi-k2.5,glm-5,claude-opus-4.7", help="Comma-separated Poe model/cache names for frontier model matrix experiments.")
    parser.add_argument("--llm-cache", default="data/llm_cache/deepseek_analyst.jsonl", help="JSONL cache for LLM prompts and responses.")
    parser.add_argument("--llm-periods", type=int, default=52, help="Most recent historical periods to use for LLM experiments.")
    parser.add_argument("--no-statistical", action="store_true", help="Skip 30-seed statistical robustness tables in --paper-output.")
    parser.add_argument("--statistical-seeds", default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30", help="Comma-separated seeds for statistical robustness tables.")
    parser.add_argument("--no-synthetic-market-stress", action="store_true", help="Skip heterogeneous synthetic parallel-market stress tests in --paper-output.")
    parser.add_argument("--synthetic-stress-markets", type=int, default=120, help="Number of heterogeneous synthetic parallel markets for stress testing.")
    parser.add_argument("--no-rolling-windows", action="store_true", help="Skip historical rolling-window robustness tables in --paper-output.")
    parser.add_argument("--no-representation-analysis", action="store_true", help="Skip LLM plan/reflect embedding drift analysis in --paper-output.")
    parser.add_argument("--no-hallucination-analysis", action="store_true", help="Skip LLM hallucination proxy versus risk audit analysis in --paper-output.")
    parser.add_argument("--hallucination-annotation-path", default="data/annotations/hallucination_gold.csv", help="Optional CSV with blind human labels for hallucination-proxy calibration.")
    parser.add_argument("--no-memory-learning", action="store_true", help="Skip LLM memory-learning curve analysis in --paper-output.")
    parser.add_argument("--no-intraday-complex", action="store_true", help="Skip 50-stock 1h intraday portfolio complexity tables in --paper-output.")
    parser.add_argument("--intraday-llm-probe", action="store_true", help="Include the expensive 51-stock LLM intraday probe.")
    parser.add_argument("--no-risk-feedback-ablation", action="store_true", help="Skip risk-feedback on/off LLM intent evolution ablation.")
    parser.add_argument("--no-cot-free-ablation", action="store_true", help="Skip CoT-free target-weight ablation for cached frontier Poe models.")
    parser.add_argument("--no-noise-injection", action="store_true", help="Skip representation-signature robustness under noisy OHLCV perturbations.")
    parser.add_argument("--no-contrarian-audit", action="store_true", help="Skip contrarian false-risk-report trust-calibration experiment.")
    parser.add_argument("--intraday-data-dir", default="data/real/yahoo_intraday_1h_50", help="Directory containing 1h intraday Yahoo Finance CSV files.")
    parser.add_argument("--intraday-periods", type=int, default=40, help="Most recent hourly bars for the 50-stock intraday LLM experiment.")
    parser.add_argument("--intraday-llm-steps", type=int, default=8, help="Hourly decisions for the expensive 51-stock LLM intraday probe; set to 40 for the full-week version.")
    parser.add_argument("--intraday-llm-model", default="deepseek-v4-pro", help="Direct-provider model for the 50-stock intraday experiment.")
    parser.add_argument("--intraday-llm-models", default="", help="Comma-separated model names for multiple intraday LLM probes.")
    parser.add_argument("--intraday-llm-provider", default="deepseek", choices=["deepseek", "poe"], help="Provider adapter for the intraday LLM probe.")
    parser.add_argument("--list-plugins", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_plugins:
        registry = default_registry()
        for category in registry.categories():
            print(f"{category}: {', '.join(registry.names(category))}")
        return 0

    symbols = tuple(symbol.strip() for symbol in args.symbols.split(",") if symbol.strip())
    benchmark_data_kwargs = {
        "data_source": args.data_source,
        "real_data_dir": args.real_data_dir,
        "real_data_frequency": args.real_frequency,
        "real_data_start": args.real_start or None,
        "real_data_end": args.real_end or None,
        "real_data_max_periods": args.real_max_periods or None,
    }
    if args.paper_output:
        seeds = tuple(int(seed.strip()) for seed in args.paper_seeds.split(",") if seed.strip())
        statistical_seeds = tuple(int(seed.strip()) for seed in args.statistical_seeds.split(",") if seed.strip())
        llm_models = tuple(model.strip() for model in args.llm_models.split(",") if model.strip())
        model_matrix_models = tuple(model.strip() for model in args.model_matrix_models.split(",") if model.strip())
        intraday_llm_models = tuple(model.strip() for model in args.intraday_llm_models.split(",") if model.strip())
        result = run_paper_experiment(
            PaperExperimentConfig(
                output_dir=args.paper_output,
                symbols=symbols,
                periods=args.periods,
                seeds=seeds,
                include_stress=not args.no_stress,
                include_extended=not args.no_extended,
                include_real_data=not args.no_real_data,
                real_data_dir=args.real_data_dir,
                real_symbols=tuple(symbol.strip() for symbol in args.real_symbols.split(",") if symbol.strip()),
                real_data_frequency=args.real_frequency,
                include_llm=not args.no_llm,
                llm_model=args.llm_model,
                llm_models=llm_models or (args.llm_model,),
                include_model_matrix=not args.no_model_matrix,
                model_matrix_models=model_matrix_models,
                llm_cache_path=args.llm_cache,
                llm_periods=args.llm_periods,
                include_statistical=not args.no_statistical,
                statistical_seeds=statistical_seeds,
                include_synthetic_market_stress=not args.no_synthetic_market_stress,
                synthetic_stress_markets=args.synthetic_stress_markets,
                include_rolling_windows=not args.no_rolling_windows,
                include_representation_analysis=not args.no_representation_analysis,
                include_hallucination_analysis=not args.no_hallucination_analysis,
                hallucination_annotation_path=args.hallucination_annotation_path,
                include_memory_learning=not args.no_memory_learning,
                include_intraday_complex=not args.no_intraday_complex,
                include_intraday_llm_probe=args.intraday_llm_probe,
                include_risk_feedback_ablation=not args.no_risk_feedback_ablation,
                include_cot_free_ablation=not args.no_cot_free_ablation,
                include_noise_injection=not args.no_noise_injection,
                include_contrarian_audit=not args.no_contrarian_audit,
                intraday_data_dir=args.intraday_data_dir,
                intraday_max_periods=args.intraday_periods,
                intraday_llm_max_periods=args.intraday_llm_steps,
                intraday_llm_model=args.intraday_llm_model,
                intraday_llm_models=intraday_llm_models,
                intraday_llm_provider=args.intraday_llm_provider,
            )
        )
        print(json.dumps(to_jsonable(result["artifacts"]), indent=2))
        return 0

    cases = [
        BenchmarkCase(
            name="risk_aware_realistic_agent",
            build_system=lambda: build_default_system(
                name="risk_aware_realistic_agent",
                symbols=symbols,
                periods=args.periods,
                seed=args.seed,
                strategy_name="signal-weighted",
                risk_name=args.risk,
                execution_mode=args.execution,
                spread_bps=args.spread_bps,
                **benchmark_data_kwargs,
            ),
            description="Momentum plus macro/news agent with configurable risk and execution realism.",
        ),
        BenchmarkCase(
            name="buy_and_hold_realistic",
            build_system=lambda: build_default_system(
                name="buy_and_hold_realistic",
                symbols=symbols,
                periods=args.periods,
                seed=args.seed,
                strategy_name="buy-and-hold",
                risk_name=args.risk,
                execution_mode=args.execution,
                spread_bps=args.spread_bps,
                **benchmark_data_kwargs,
            ),
            description="Equal-weight buy-and-hold baseline.",
        ),
        BenchmarkCase(
            name="ideal_execution_ablation",
            build_system=lambda: build_default_system(
                name="ideal_execution_ablation",
                symbols=symbols,
                periods=args.periods,
                seed=args.seed,
                strategy_name="signal-weighted",
                risk_name=args.risk,
                execution_mode="ideal",
                spread_bps=0.0,
                **benchmark_data_kwargs,
            ),
            description="Same agent under idealized execution for cost/realism ablation.",
        ),
        BenchmarkCase(
            name="no_risk_ablation",
            build_system=lambda: build_default_system(
                name="no_risk_ablation",
                symbols=symbols,
                periods=args.periods,
                seed=args.seed,
                strategy_name="signal-weighted",
                risk_name="none",
                execution_mode=args.execution,
                spread_bps=args.spread_bps,
                **benchmark_data_kwargs,
            ),
            description="Same agent with the risk gate disabled.",
        ),
    ]
    if args.benchmark == "momentum-vs-buyhold":
        cases = cases[:2]
    results = BenchmarkRunner(cases=cases).run()
    print(json.dumps(to_jsonable(results), indent=2))

    if args.output:
        trajectories = {}
        for case in cases:
            trajectory, metrics = case.build_system().run()
            trajectories[case.name] = {"trajectory": trajectory.to_dict(), "metrics": metrics}
        write_json(Path(args.output), trajectories)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
