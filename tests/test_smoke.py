from tradearena.factory import build_default_system, default_registry


def test_default_system_runs_and_records_trajectory():
    system = build_default_system(symbols=("SYN", "ALT"), periods=40, seed=3)
    trajectory, metrics = system.run()

    assert len(trajectory.steps) == 40
    assert metrics["steps"] == 40
    assert metrics["final_equity"] > 0
    assert trajectory.steps[-1].portfolio["equity"] == metrics["final_equity"]
    assert "reasoning_consistency" in metrics
    assert "execution_fill_rate" in metrics
    assert "risk_audit_coverage" in metrics
    assert trajectory.steps[-1].risk_report
    assert trajectory.steps[-1].in_trade_report
    assert trajectory.steps[-1].post_trade_report
    assert trajectory.steps[-1].execution_report
    assert trajectory.steps[-1].reproducibility_state["prompt_version"] == "baseline-v0"
    assert "observe" in trajectory.steps[-1].agent_trace
    assert metrics["risk_lifecycle_coverage"] == 1.0
    assert metrics["trajectory_reproducibility_coverage"] == 1.0
    assert metrics["agent_trace_coverage"] == 1.0


def test_reproducible_seed():
    first = build_default_system(symbols=("SYN",), periods=30, seed=9).run()[1]
    second = build_default_system(symbols=("SYN",), periods=30, seed=9).run()[1]

    assert first["final_equity"] == second["final_equity"]
    assert first["total_return"] == second["total_return"]


def test_registry_lists_default_plugins():
    registry = default_registry()

    assert "synthetic-market" in registry.names("data")
    assert "signal-weighted" in registry.names("strategy")
    assert "mean-variance" in registry.names("strategy")
    assert "performance" in registry.names("evaluator")
    assert "realistic" in registry.names("simulator")
    assert "none" in registry.names("risk")


def test_markowitz_baseline_runs_with_realistic_execution():
    system = build_default_system(symbols=("SYN", "ALT", "DEF"), periods=32, seed=4, strategy_name="mean-variance", max_position_weight=0.2)
    trajectory, metrics = system.run()

    assert len(trajectory.steps) == 32
    assert metrics["final_equity"] > 0
    assert trajectory.steps[-1].decisions
    assert all(float(decision["target_weight"]) <= 0.2 for decision in trajectory.steps[-1].decisions)
