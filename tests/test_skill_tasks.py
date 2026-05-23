from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "examples" / "skill_tasks"
SCHEMA_PATH = ROOT / "schemas" / "skill_task_rubric.schema.json"


def test_skill_tasks_have_inputs_and_rubrics():
    task_dirs = sorted(path for path in TASKS_DIR.iterdir() if path.is_dir())

    assert {path.name for path in task_dirs} == {
        "claim_boundary_001",
        "execution_boundary_001",
        "plugin_author_001",
        "reproduction_review_001",
        "risk_gate_review_001",
        "trajectory_audit_001",
    }
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    abilities = set()
    for task_dir in task_dirs:
        assert (task_dir / "input.md").exists()
        rubric = json.loads((task_dir / "rubric.json").read_text(encoding="utf-8"))
        validator.validate(rubric)
        assert rubric["task_id"] == task_dir.name
        assert rubric["skill"].startswith("tradearena-")
        abilities.add(rubric["ability"])
        assert len(rubric["criteria"]) >= 4
        assert 1 <= int(rubric["pass_threshold"]) <= sum(criterion["points"] for criterion in rubric["criteria"])

    assert abilities == {
        "audit_accuracy",
        "claim_discipline",
        "execution_boundary_awareness",
        "plugin_engineering",
        "reproduction_awareness",
        "risk_understanding",
    }


def test_skill_task_scorer_scores_reference_like_answer(tmp_path: Path):
    answer = tmp_path / "answer.md"
    answer.write_text(
        "\n".join(
            [
                "Use tradearena hash-run and replay to report the trajectory hash.",
                "Compare raw and approved decisions and note any risk edit diff.",
                "Check both the risk report and execution report.",
                "Flag rejected orders or partial filled orders.",
                "This supports an engineering claim, not a scientific claim.",
            ]
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/score_skill_task.py",
            "examples/skill_tasks/trajectory_audit_001",
            "--answer",
            str(answer),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed=True" in result.stdout
