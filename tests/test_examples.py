from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ashare_market_rules_demo_outputs_rule_events():
    _run_example("examples/ashare_market_rules_demo.py")
    summary = _read_json("outputs/examples/ashare_market_rules_summary.json")

    assert summary["summary"]["proposals"] == 5
    assert summary["summary"]["blocked"] >= 3
    assert summary["summary"]["clipped"] == 1
    assert (ROOT / "outputs/examples/ashare_market_rules.svg").exists()


def test_crisis_snapshot_demo_builds_gallery_from_tracked_artifacts():
    _run_example("examples/crisis_snapshot_demo.py")
    summary = _read_json("outputs/examples/crisis_snapshot_summary.json")

    assert summary["rows"] >= 20
    assert "deepseek-v4-pro" in summary["models"]
    assert "gpt-5.5" in summary["models"]
    assert (ROOT / "outputs/examples/crisis_snapshot_gallery.html").exists()


def test_akshare_csv_reuse_demo_uses_standard_csv_provider():
    _run_example("examples/akshare_csv_reuse_demo.py")
    summary = _read_json("outputs/examples/akshare_csv_reuse_summary.json")

    assert summary["provider_reused"] == "CsvMarketDataProvider"
    assert summary["symbols"] == ["600519.SS", "300750.SZ"]
    assert summary["steps"] == 10
    assert (ROOT / "outputs/examples/akshare_csv_reuse.svg").exists()


def test_llm_cache_replay_demo_summarizes_cached_frontier_rows():
    _run_example("examples/llm_cache_replay_demo.py")
    summary = _read_json("outputs/examples/llm_cache_replay_summary.json")

    assert summary["rows"] >= 100
    assert summary["timestamp_masked_rows"] == summary["rows"]
    assert summary["parsed_response_rate"] > 0.9
    assert summary["raw_cache_tracked_in_repo"] is False
    assert summary["redaction"]["raw_prompts_included"] is False
    assert "poe:gpt-5.5" in summary["provider_model_counts"]


def test_paper_design_demo_suite_builds_advanced_artifacts():
    subprocess.run([sys.executable, "scripts/run_paper_design_demos.py"], cwd=ROOT, check=True)

    assert (ROOT / "outputs/examples/experiment_design_index.html").exists()
    assert (ROOT / "outputs/examples/paper_design_index.html").exists()
    assert (ROOT / "outputs/examples/execution_realism_sweep.svg").exists()
    assert (ROOT / "outputs/examples/portfolio_markowitz.svg").exists()
    assert (ROOT / "outputs/examples/representation_signature.svg").exists()
    assert (ROOT / "outputs/examples/custom_plugin.svg").exists()


def test_visual_tour_demo_generates_animated_artifacts():
    _run_example("examples/visual_tour_demo.py")
    summary = _read_json("outputs/examples/visual_tour_summary.json")

    assert summary["api_free"] is True
    assert summary["requires_live_market_data"] is False
    assert (ROOT / "outputs/examples/visual_tour_index.html").exists()

    for filename in (
        "visual_tour_audit_lifecycle.gif",
        "visual_tour_execution_realism.gif",
        "visual_tour_diagnostics_loop.gif",
    ):
        path = ROOT / "outputs/examples" / filename
        assert path.exists()
        assert 0 < path.stat().st_size < 1_500_000


def test_extension_walkthrough_demo_shows_modular_contribution_path():
    _run_example("examples/extension_walkthrough_demo.py")
    summary = _read_json("outputs/examples/extension_walkthrough_summary.json")

    assert summary["custom_modules"] == {
        "analyst": "GapVolumeAnalyst",
        "risk_manager": "VolatilityCircuitBreakerRisk",
        "evaluator": "ExtensionCoverageEvaluator",
    }
    assert summary["reused_core_modules"]["order_simulator"] == "realistic-order-simulator"
    assert summary["metrics"]["extension_custom_signal_count"] > 0
    assert summary["metrics"]["extension_circuit_breaker_blocks"] > 0
    assert summary["metrics"]["risk_lifecycle_coverage"] == 1.0
    assert (ROOT / "outputs/examples/extension_walkthrough.svg").exists()


def test_showcase_index_can_be_built_from_existing_or_missing_artifacts():
    subprocess.run([sys.executable, "scripts/run_showcase.py", "--reuse-existing"], cwd=ROOT, check=True)

    html = (ROOT / "outputs/examples/showcase.html").read_text(encoding="utf-8")
    assert "TradeArena Showcase" in html
    assert "Experiment-design demos" in html
    assert "Animated visual tour" in html
    assert "Custom plugin extension" in html
    assert "Contributor extension walkthrough" in html


def _run_example(path: str) -> None:
    subprocess.run([sys.executable, path], cwd=ROOT, check=True)


def _read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))
