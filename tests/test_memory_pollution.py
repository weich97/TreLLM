import pytest

from tradearena.factory import build_default_system
from tradearena.memory import InMemoryResearchMemory, PollutedResearchMemory, PollutionConfig


def _seed_steps(memory: InMemoryResearchMemory, count: int = 6) -> None:
    for index in range(count):
        memory.record(
            "step",
            {
                "equity": 100_000.0 + 100.0 * index,
                "execution_report": {"rejected_orders": 0},
                "risk_violations": [],
            },
        )


def test_zero_dose_returns_events_unchanged():
    base = InMemoryResearchMemory()
    _seed_steps(base)
    polluted = PollutedResearchMemory(base=base, config=PollutionConfig(kind="fake_rejections", dose=0.0))

    events = polluted.recent("step", 5)

    assert events == base.recent("step", 5)
    assert not any(event.get("injected") for event in events)


def test_full_dose_fake_rejections_marks_every_event():
    base = InMemoryResearchMemory()
    _seed_steps(base)
    polluted = PollutedResearchMemory(base=base, config=PollutionConfig(kind="fake_rejections", dose=1.0))

    events = polluted.recent("step", 5)

    assert all(event["injected"] for event in events)
    assert all(event["payload"]["execution_report"]["rejected_orders"] >= 2 for event in events)
    # The journal itself stays clean.
    assert all("injected" not in event for event in base.events)
    assert all(event["payload"]["execution_report"]["rejected_orders"] == 0 for event in base.events)


def test_partial_dose_is_deterministic_for_fixed_journal_state():
    base = InMemoryResearchMemory()
    _seed_steps(base)
    polluted = PollutedResearchMemory(base=base, config=PollutionConfig(kind="fake_violations", dose=0.4, seed=11))

    first = polluted.recent("step", 5)
    second = polluted.recent("step", 5)

    assert first == second
    injected = [event for event in first if event.get("injected")]
    assert len(injected) == 2  # round(0.4 * 5)
    assert all(event["payload"]["risk_violations"][-1]["rule"] == "fabricated_max_abs_weight" for event in injected)


def test_missing_equity_removes_the_mark():
    base = InMemoryResearchMemory()
    _seed_steps(base)
    polluted = PollutedResearchMemory(base=base, config=PollutionConfig(kind="missing_equity", dose=1.0))

    events = polluted.recent("step", 5)

    assert all("equity" not in event["payload"] for event in events)


def test_loss_streak_rewrites_recent_equity_downward():
    base = InMemoryResearchMemory()
    _seed_steps(base)
    polluted = PollutedResearchMemory(
        base=base,
        config=PollutionConfig(kind="loss_streak", dose=0.0, loss_streak_length=3, loss_step_return=-0.05),
    )

    events = polluted.recent("step", 5)

    streak = events[-3:]
    equities = [event["payload"]["equity"] for event in streak]
    assert all(event["injected"] for event in streak)
    assert equities[0] > equities[1] > equities[2]
    assert not any(event.get("injected") for event in events[:-3])


def test_non_step_events_and_other_types_pass_through():
    base = InMemoryResearchMemory()
    base.record("thesis", {"symbol": "SYN", "text": "hold"})
    polluted = PollutedResearchMemory(base=base, config=PollutionConfig(kind="fake_rejections", dose=1.0))

    assert polluted.recent("thesis", 5) == base.recent("thesis", 5)
    assert polluted.theses == {"SYN": "hold"}


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        PollutionConfig(kind="unknown", dose=0.5)
    with pytest.raises(ValueError):
        PollutionConfig(kind="fake_rejections", dose=1.5)


def test_pollution_reaches_llm_risk_feedback_path():
    from tradearena.agents.llm import _recent_risk_feedback

    base = InMemoryResearchMemory()
    _seed_steps(base)
    polluted = PollutedResearchMemory(base=base, config=PollutionConfig(kind="fake_rejections", dose=1.0))

    clean_feedback = _recent_risk_feedback(base)
    polluted_feedback = _recent_risk_feedback(polluted)

    assert all(item["rejected_orders"] == 0 for item in clean_feedback)
    assert all(item["rejected_orders"] >= 2 for item in polluted_feedback)


def test_pollution_sweep_writes_agent_and_sample_columns(tmp_path):
    import csv
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts" / "run_memory_pollution_sweep.py"
    spec = importlib.util.spec_from_file_location("run_memory_pollution_sweep", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    exit_code = module.main(
        [
            "--kinds", "fake_rejections",
            "--doses", "0,0.5",
            "--decays", "0.85",
            "--risks", "max-position",
            "--seeds", "3,5",
            "--periods", "15",
            "--output-dir", str(tmp_path),
        ]
    )

    assert exit_code == 0
    rows = list(csv.DictReader((tmp_path / "memory_pollution_runs.csv").open(encoding="utf-8")))
    assert len(rows) == 4
    assert all(row["agent"] == "memory-aware" for row in rows)
    assert all(row["sample"] == "0" for row in rows)
    assert all(row["hold_ratio"] != "" for row in rows)
    # Resume skips everything already checkpointed.
    assert module.main(
        [
            "--kinds", "fake_rejections",
            "--doses", "0,0.5",
            "--decays", "0.85",
            "--risks", "max-position",
            "--seeds", "3,5",
            "--periods", "15",
            "--output-dir", str(tmp_path),
        ]
    ) == 0
    rows_after = list(csv.DictReader((tmp_path / "memory_pollution_runs.csv").open(encoding="utf-8")))
    assert len(rows_after) == 4


def test_factory_wires_polluted_memory_and_run_records_pollution_ratio():
    system = build_default_system(
        name="pollution_smoke",
        symbols=("SYN",),
        periods=20,
        seed=5,
        strategy_name="memory-aware",
        analyst_names=("momentum",),
        memory_pollution_kind="fake_rejections",
        memory_pollution_dose=0.75,
        memory_pollution_seed=5,
    )

    assert isinstance(system.memory, PollutedResearchMemory)
    _, metrics = system.run()
    # Manipulation check: the strategy's perceived pollution must respond to dose.
    assert metrics["max_memory_pollution_ratio"] > 0.0

    clean = build_default_system(
        name="pollution_smoke_clean",
        symbols=("SYN",),
        periods=20,
        seed=5,
        strategy_name="memory-aware",
        analyst_names=("momentum",),
    )
    assert isinstance(clean.memory, InMemoryResearchMemory)
