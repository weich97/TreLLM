from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tradearena.tools.calibration import summarize_quote_fill_calibration

ROOT = Path(__file__).resolve().parents[1]


def test_v02_spec_validates_and_names_required_surfaces():
    result = subprocess.run(
        [sys.executable, "scripts/validate_benchmark_spec.py", "benchmarks/v0.2/spec.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    spec = json.loads((ROOT / "benchmarks/v0.2/spec.json").read_text(encoding="utf-8"))

    assert payload["valid"] is True
    assert payload["canonical_sha256"].startswith("sha256:")
    assert spec["status"] == "frozen"
    assert "paired_sign_flip_permutation" in spec["statistics"]["paired_tests"]
    assert "random" in spec["baselines"]
    assert "always-hold" in spec["baselines"]


def test_benchmark_spec_validator_reports_malformed_json(tmp_path: Path):
    spec = tmp_path / "broken_spec.json"
    spec.write_text('{"schema_version": ', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/validate_benchmark_spec.py", str(spec)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert payload["errors"] == ["benchmark spec file must contain valid JSON"]
    assert "Traceback" not in result.stderr


def test_quote_fill_calibration_fixture_fits_execution_parameters():
    summary = summarize_quote_fill_calibration(
        ROOT / "data/public/microstructure_sample/quotes.csv",
        ROOT / "data/public/microstructure_sample/fills.csv",
    )

    assert summary["input"]["aligned_rows"] == 8
    assert summary["fitted_parameters"]["spread_bps_median"] > 0
    assert summary["fitted_parameters"]["spread_bps_p99"] >= summary["fitted_parameters"]["spread_bps_p90"]
    assert summary["fitted_parameters"]["market_impact"] >= 0
    assert summary["fit_quality"]["residual_mae_bps"] < 2.0
    assert summary["fit_quality"]["residual_p90_abs_bps"] >= summary["fit_quality"]["residual_mae_bps"]
    assert "stress_only_comparison" in summary
    assert summary["suggested_simulator_config"]["spread_bps"] > 0


def test_binance_public_microstructure_sample_reports_quote_fill_replay_error():
    summary = summarize_quote_fill_calibration(
        ROOT / "data/public/binance_btcusdt_perp_2024_03_01_sample/quotes.csv",
        ROOT / "data/public/binance_btcusdt_perp_2024_03_01_sample/fills.csv",
    )
    manifest = json.loads(
        (ROOT / "data/public/binance_btcusdt_perp_2024_03_01_sample/manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["provenance"]["downloaded_market_data_used"] is True
    assert summary["input"]["aligned_rows"] == 500
    assert summary["fitted_parameters"]["quote_event_lag_seconds_median"] is not None
    assert summary["fitted_parameters"]["quote_staleness_seconds_p90"] is not None
    assert summary["fit_quality"]["p90_shortfall_bps"] >= summary["fit_quality"]["median_shortfall_bps"]
    assert summary["stress_only_comparison"]["residual_mae_bps"] > summary["fit_quality"]["residual_mae_bps"]


def test_execution_replay_calibration_loop_compares_three_modes(tmp_path: Path):
    output = tmp_path / "loop.json"
    markdown = tmp_path / "loop.md"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_execution_replay_calibration_loop.py",
            "--samples",
            "fixture",
            "--output",
            str(output),
            "--markdown-output",
            str(markdown),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(output.read_text(encoding="utf-8"))
    modes = {row["mode"]: row for row in summary["mode_rows"]}

    assert set(modes) == {"ohlcv_stress", "quote_replay", "fill_replay"}
    assert "conservative proxy" in summary["claim_boundary"]
    assert modes["ohlcv_stress"]["evidence_labels"] == ["stress-only", "conservative-proxy"]
    assert "quote-replay" in modes["quote_replay"]["evidence_labels"]
    assert modes["fill_replay"]["quantity_fill_ratio"] == 1.0
    assert modes["ohlcv_stress"]["mean_slippage_bps"] > modes["fill_replay"]["mean_slippage_bps"]
    assert "not for ground-truth transaction-cost prediction" in markdown.read_text(encoding="utf-8")


def test_external_reproduction_pack_writes_manifest(tmp_path: Path):
    output_dir = tmp_path / "repro"
    subprocess.run(
        [sys.executable, "scripts/run_external_reproduction_pack.py", "--output-dir", str(output_dir)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema"] == "tradearena_external_reproduction_pack_v1"
    assert manifest["commit_or_tag"]
    assert manifest["live_api_used"] is False
    assert manifest["private_fills_used"] is False
    assert manifest["trajectory_hash"]["reproducibility_hash"].startswith("sha256:")
    assert any(artifact["path"].endswith("agent_autopsy_dashboard.html") for artifact in manifest["artifacts"])
