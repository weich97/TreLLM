from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["agent", "kind", "dose", "decay", "risk", "seed", "sample",
          "memory_driven_leverage_amplification", "max_memory_driven_leverage_amplification",
          "memory_pollution_ratio", "total_return", "max_drawdown", "turnover_events", "hold_ratio"]


def _load():
    path = ROOT / "scripts" / "analyze_memory_pollution_llm.py"
    spec = importlib.util.spec_from_file_location("analyze_memory_pollution_llm", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def _row(agent, kind, dose, risk, seed, sample, hold, turn):
    return {"agent": agent, "kind": kind, "dose": dose, "decay": 0.85, "risk": risk,
            "seed": seed, "sample": sample, "memory_driven_leverage_amplification": "",
            "max_memory_driven_leverage_amplification": "", "memory_pollution_ratio": 0.0,
            "total_return": 0.05, "max_drawdown": -0.05, "turnover_events": turn, "hold_ratio": hold}


def test_dose_response_averages_samples_and_pairs(tmp_path):
    mod = _load()
    rows = []
    for seed in (1, 2, 3, 4, 5, 6):
        for s, h in enumerate((0.20, 0.22, 0.24)):  # dose0 hold ~0.22
            rows.append(_row("poe:m", "fake_violations", 0.0, "max-position", seed, s, h, 10))
        for s, h in enumerate((0.40, 0.42, 0.44)):  # dose0.75 hold ~0.42
            rows.append(_row("poe:m", "fake_violations", 0.75, "max-position", seed, s, h, 5))
    _write(tmp_path / "m" / "memory_pollution_runs.csv", rows)
    runs = mod.load_runs([tmp_path / "m"])
    dr = mod.dose_response_rows(runs)
    hold = [r for r in dr if r["outcome"] == "hold_ratio" and r["dose"] == 0.75]
    assert len(hold) == 1
    assert round(float(hold[0]["mean_delta"]), 4) == 0.20  # 0.42 - 0.22
    assert hold[0]["paired_n"] == 6


def test_main_writes_tables(tmp_path):
    mod = _load()
    rows = []
    for seed in (1, 2, 3):
        for dose in (0.0, 0.75):
            rows.append(_row("poe:m", "fake_violations", dose, "max-position", seed, 0, 0.3, 8))
    _write(tmp_path / "m" / "memory_pollution_runs.csv", rows)
    assert mod.main(["--input-dirs", str(tmp_path / "m"), "--output-dir", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "dose_response.csv").exists()
    assert (tmp_path / "out" / "model_difference.csv").exists()
    assert (tmp_path / "out" / "memory_pollution_llm.md").read_text(encoding="utf-8").startswith("# Memory Pollution")
