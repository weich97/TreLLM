from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from score_skill_task import ABILITY_LABELS, score_answer_directory, validate_tasks

from tradearena.core.redaction import scan_public_artifact_paths
from tradearena.core.serialization import write_json

DEFAULT_MODELS = (
    "poe:gpt-5.5",
    "poe:gemini-3.1-pro",
    "poe:kimi-k2.5",
    "poe:glm-5",
    "poe:claude-opus-4.7",
)
DEFAULT_DEEPSEEK_MODELS = (
    "deepseek:deepseek-v4-flash",
    "deepseek:deepseek-v4-pro",
)
PROMPT_VERSION = "provider-skill-audit-v0.1"
ANSWER_SET_SCHEMA = "tradearena_skill_answer_set_v0.1"


@dataclass(frozen=True)
class ChatResponse:
    text: str
    latency_ms: float
    cache_hit: bool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run provider-hosted models on TradeArena financial-audit skill tasks. "
            "Bare model names use Poe; DeepSeek rows must use deepseek:<model>."
        )
    )
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS), help="Comma-separated provider:model entries. Bare names default to Poe; DeepSeek must use deepseek:<model>.")
    parser.add_argument(
        "--include-deepseek",
        action="store_true",
        help="Also run DeepSeek V4 Flash/Pro through the direct DeepSeek API, not through Poe.",
    )
    parser.add_argument("--tasks-dir", default="examples/skill_tasks")
    parser.add_argument("--skills-dir", default="skills")
    parser.add_argument("--output-dir", default="outputs/poe_skill_task_answers")
    parser.add_argument("--public-output", default="docs/results/poe_skill_task_matrix.md")
    parser.add_argument("--public-csv", default="docs/results/poe_skill_task_matrix.csv")
    parser.add_argument("--cache-dir", default="outputs/llm_cache/poe_skill_tasks")
    parser.add_argument("--repeats", type=int, default=3, help="Repeated answer sets per model. Three repeats across five models is roughly a 350k-450k token run.")
    parser.add_argument("--max-output-tokens", type=int, default=1400)
    parser.add_argument("--poe-api-base-url", default="https://api.poe.com/v1")
    parser.add_argument("--poe-api-key-env", default="POE_API_KEY")
    parser.add_argument("--deepseek-api-base-url", default="https://api.deepseek.com")
    parser.add_argument("--deepseek-api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignore cached provider answers and spend live tokens again.")
    parser.add_argument("--limit-tasks", default="", help="Comma-separated task ids for a smoke run.")
    parser.add_argument("--dry-run", action="store_true", help="Write the planned call matrix without calling provider APIs.")
    args = parser.parse_args(argv)

    tasks_dir = ROOT / args.tasks_dir
    skills_dir = ROOT / args.skills_dir
    output_root = ROOT / args.output_dir
    cache_dir = ROOT / args.cache_dir
    public_output = ROOT / args.public_output
    public_csv = ROOT / args.public_csv
    task_paths = _task_paths(tasks_dir, args.limit_tasks)
    failures = validate_tasks(task_paths)
    if failures:
        print("Skill task validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    model_specs = _parse_model_specs(args.models)
    if args.include_deepseek:
        model_specs = (*model_specs, *_parse_model_specs(",".join(DEFAULT_DEEPSEEK_MODELS)))
    run_id = datetime.now(tz=UTC).strftime("provider_skill_tasks_%Y%m%d_%H%M%S")
    run_dir = output_root / run_id
    output_root.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    planned_calls = len(model_specs) * max(args.repeats, 0) * len(task_paths)
    estimated_tokens = _estimate_total_tokens(task_paths, skills_dir, model_specs, args.repeats)
    plan = {
        "run_id": run_id,
        "models": [f"{provider}:{model}" for provider, model in model_specs],
        "tasks": [path.name for path in task_paths],
        "repeats": args.repeats,
        "planned_calls": planned_calls,
        "estimated_tokens": estimated_tokens,
        "prompt_version": PROMPT_VERSION,
        "public_outputs": {
            "markdown": str(public_output.relative_to(ROOT)),
            "csv": str(public_csv.relative_to(ROOT)),
        },
        "private_outputs": str(run_dir.relative_to(ROOT)),
        "private_cache": str(cache_dir.relative_to(ROOT)),
    }
    write_json(run_dir / "plan.json", plan)
    if args.dry_run:
        _write_public_report(public_output, public_csv, [], plan)
        print(json.dumps(plan, indent=2))
        return 0

    summaries: list[dict[str, Any]] = []
    for provider, model in model_specs:
        api_key_env = args.poe_api_key_env if provider == "poe" else args.deepseek_api_key_env
        api_base_url = args.poe_api_base_url if provider == "poe" else args.deepseek_api_base_url
        api_key = _get_secret(api_key_env)
        if not api_key:
            raise SystemExit(f"{api_key_env} is not set for provider {provider}.")
        for repeat in range(1, args.repeats + 1):
            answer_dir = run_dir / f"{provider}_{_safe_id(model)}_r{repeat}"
            answer_dir.mkdir(parents=True, exist_ok=True)
            _write_manifest(answer_dir, provider, model, repeat, task_paths)
            for task_path in task_paths:
                prompt = _build_prompt(task_path, skills_dir)
                response = _chat_completion(
                    provider=provider,
                    model=model,
                    prompt=prompt,
                    api_key=api_key,
                    api_base_url=api_base_url,
                    cache_path=cache_dir / f"{provider}_{_safe_id(model)}.jsonl",
                    max_output_tokens=args.max_output_tokens,
                    refresh_cache=args.refresh_cache,
                )
                (answer_dir / f"{task_path.name}.md").write_text(response.text.strip() + "\n", encoding="utf-8")
            scores, manifest, answer_failures = score_answer_directory(task_paths, answer_dir)
            if answer_failures:
                raise SystemExit("\n".join(answer_failures))
            summary = _summarize_answer_set(provider, model, repeat, scores, manifest.to_dict() if manifest else {})
            write_json(answer_dir / "score_summary.json", summary)
            summaries.append(summary)
            print(f"Scored {model} repeat {repeat}: {summary['tasks_passed']}/{summary['tasks']} tasks passed")

    _write_public_report(public_output, public_csv, summaries, plan)
    findings = scan_public_artifact_paths([public_output, public_csv])
    if findings:
        print("Public provider skill-task report privacy scan failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Wrote {public_output}")
    print(f"Wrote {public_csv}")
    return 0


def _task_paths(tasks_dir: Path, limit_tasks: str) -> list[Path]:
    selected = {item.strip() for item in limit_tasks.split(",") if item.strip()}
    paths = sorted(path for path in tasks_dir.iterdir() if path.is_dir())
    return [path for path in paths if not selected or path.name in selected]


def _build_prompt(task_path: Path, skills_dir: Path) -> str:
    rubric = json.loads((task_path / "rubric.json").read_text(encoding="utf-8"))
    skill_name = str(rubric["skill"])
    skill_dir = skills_dir / skill_name
    sections = [
        "# Role",
        "You are evaluating TradeArena as a financial-audit agent, not as a trader.",
        "Use only the provided public task input, skill text, and public artifacts.",
        "Do not give buy/sell recommendations, profitability promises, live-order advice, API-key requests, or broker instructions.",
        "When evidence is missing, say so before making a claim.",
        "",
        "# Skill",
        _read_text(skill_dir / "SKILL.md"),
    ]
    resource_dir = skill_dir / "resources"
    if resource_dir.exists():
        for path in sorted(resource_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".md", ".json", ".txt"}:
                sections.extend(["", f"# Skill Resource: {path.relative_to(skill_dir)}", _read_text(path)])
    sections.extend(["", "# Task Input", _read_text(task_path / "input.md")])
    for path in sorted(task_path.rglob("*")):
        if not path.is_file() or path.name in {"input.md", "rubric.json"}:
            continue
        if path.suffix.lower() not in {".md", ".json", ".csv", ".txt", ".py"}:
            continue
        sections.extend(["", f"# Public Task Artifact: {path.relative_to(task_path)}", _read_text(path, limit=24_000)])
    sections.extend(
        [
            "",
            "# Required Answer Format",
            "Return concise Markdown with these headings when relevant:",
            "Summary; Evidence Inspected; Findings; Claim Boundary; Missing Evidence; Recommended Next Command.",
            "Be specific enough that an automated rubric can check the answer.",
        ]
    )
    return "\n".join(sections)


def _chat_completion(
    *,
    provider: str,
    model: str,
    prompt: str,
    api_key: str,
    api_base_url: str,
    cache_path: Path,
    max_output_tokens: int,
    refresh_cache: bool,
) -> ChatResponse:
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    cache_key = f"{provider}:{model}:{PROMPT_VERSION}:{prompt_hash}"
    if not refresh_cache:
        cached = _read_cache(cache_path).get(cache_key)
        if cached:
            return ChatResponse(text=str(cached["response_text"]), latency_ms=0.0, cache_hit=True)

    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_output_tokens,
        "messages": [
            {
                "role": "system",
                "content": "You are a careful financial-audit benchmark reviewer. Return only Markdown.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        f"{api_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{provider} API error {exc.code}; response body omitted to avoid leaking secrets.") from exc
    latency_ms = (time.time() - started) * 1000
    text = str(payload["choices"][0]["message"]["content"])
    _append_cache(
        cache_path,
        {
            "cache_key": cache_key,
            "provider": provider,
            "model": model,
            "prompt_version": PROMPT_VERSION,
            "prompt_hash": prompt_hash,
            "prompt": prompt,
            "response_text": text,
            "response_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "latency_ms": latency_ms,
            "created_at": int(time.time()),
        },
    )
    return ChatResponse(text=text, latency_ms=latency_ms, cache_hit=False)


def _read_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            rows[str(item["cache_key"])] = item
    return rows


def _append_cache(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True) + "\n")


def _write_manifest(answer_dir: Path, provider: str, model: str, repeat: int, task_paths: list[Path]) -> None:
    manifest = {
        "schema": ANSWER_SET_SCHEMA,
        "answer_set_id": f"{provider}_{_safe_id(model)}_r{repeat}",
        "evaluator_type": "llm",
        "model_name": model,
        "provider": provider,
        "prompt_version": PROMPT_VERSION,
        "skill_commit_or_version": _git_ref(),
        "task_inputs_commit_or_version": _git_ref(),
        "skill_files_used": True,
        "hidden_artifacts_used": False,
        "task_ids": [path.name for path in task_paths],
        "notes": "Generated by scripts/run_poe_skill_task_matrix.py. Raw prompts and raw model answers remain under ignored local outputs; public reports contain aggregate scores only.",
    }
    write_json(answer_dir / "manifest.json", manifest)


def _summarize_answer_set(provider: str, model: str, repeat: int, scores: list[Any], manifest: dict[str, Any]) -> dict[str, Any]:
    rows = [score.to_dict() for score in scores]
    by_ability: dict[str, dict[str, Any]] = {}
    for ability in ABILITY_LABELS:
        matching = [row for row in rows if row["ability"] == ability]
        if not matching:
            continue
        earned = sum(int(row["score"]) for row in matching)
        possible = sum(int(row["max_score"]) for row in matching)
        by_ability[ability] = {
            "tasks": len(matching),
            "passed": sum(1 for row in matching if row["passed"]),
            "score": earned,
            "max_score": possible,
            "score_pct": earned / possible if possible else 0.0,
        }
    total_score = sum(int(row["score"]) for row in rows)
    total_max = sum(int(row["max_score"]) for row in rows)
    return {
        "schema": "tradearena_provider_skill_task_score_v0.1",
        "provider": provider,
        "model": model,
        "repeat": repeat,
        "answer_set": manifest,
        "tasks": len(rows),
        "tasks_passed": sum(1 for row in rows if row["passed"]),
        "hard_failed": sum(1 for row in rows if row["hard_failed"]),
        "score": total_score,
        "max_score": total_max,
        "score_pct": total_score / total_max if total_max else 0.0,
        "ability_summary": by_ability,
        "task_scores": rows,
    }


def _write_public_report(markdown_path: Path, csv_path: Path, summaries: list[dict[str, Any]], plan: dict[str, Any]) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Provider Skill-Task Matrix",
        "",
        "This report evaluates Poe-hosted models, and optionally direct DeepSeek models, as financial-audit agents rather than trading strategies.",
        "The public artifact contains aggregate scores only; raw prompts and raw model answers stay in ignored local outputs/cache.",
        "",
        "## Experiment Plan",
        "",
        f"- Prompt version: `{PROMPT_VERSION}`.",
        f"- Models: {', '.join(f'`{model}`' for model in plan['models'])}.",
        f"- Tasks: {len(plan['tasks'])}.",
        f"- Repeats: {plan['repeats']}.",
        f"- Planned calls: {plan['planned_calls']}.",
        f"- Estimated token budget: about {plan['estimated_tokens']:,} tokens.",
        "",
        "## Model Aggregate",
        "",
        "| Provider | Model | Repeats | Avg tasks passed | Avg points | Avg score | Hard fails |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if summaries:
        for row in _aggregate_by_model(summaries):
            lines.append(
                f"| `{row['provider']}` | `{row['model']}` | {row['repeats']} | "
                f"{row['tasks_passed_mean']:.1f}/{row['tasks']} | "
                f"{row['score_mean']:.1f}/{row['max_score']} | {row['score_pct_mean']:.1%} | "
                f"{row['hard_failed_total']} |"
            )
    else:
        lines.append("| pending | pending | 0 | 0/0 | 0/0 | 0.0% | 0 |")
    lines.extend(
        [
            "",
            "Interpretation: these are audit-skill scores, not trading-performance scores. A higher row means the model more reliably followed TradeArena's public audit, risk, execution-boundary, reproduction, claim-boundary, and plugin-review rubrics.",
            "",
        ]
    )
    lines.extend(
        [
            "## Repeat-Level Scorecard",
            "",
            "| Provider | Model | Repeat | Tasks passed | Points | Score | Hard fails |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if summaries:
        for row in summaries:
            lines.append(
                f"| `{row['provider']}` | `{row['model']}` | {row['repeat']} | {row['tasks_passed']}/{row['tasks']} | "
                f"{row['score']}/{row['max_score']} | {row['score_pct']:.1%} | {row['hard_failed']} |"
            )
        lines.extend(
            [
                "",
                "## Ability Breakdown",
                "",
                "| Provider | Model | Repeat | Ability | Tasks passed | Points | Score |",
                "| --- | --- | ---: | --- | ---: | ---: | ---: |",
            ]
        )
        for row in summaries:
            for ability, ability_row in row["ability_summary"].items():
                lines.append(
                    f"| `{row['provider']}` | `{row['model']}` | {row['repeat']} | {ABILITY_LABELS[ability]} | "
                    f"{ability_row['passed']}/{ability_row['tasks']} | "
                    f"{ability_row['score']}/{ability_row['max_score']} | {ability_row['score_pct']:.1%} |"
                )
    else:
        lines.append("| pending | pending | 0 | 0/0 | 0/0 | 0.0% | 0 |")
    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "```bash",
            "python scripts/run_poe_skill_task_matrix.py --repeats 3",
            "python scripts/run_poe_skill_task_matrix.py --repeats 3 --include-deepseek",
            "python scripts/score_skill_task.py --tasks-dir examples/skill_tasks --answers-dir outputs/poe_skill_task_answers/<run>/<model_repeat>",
            "```",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["provider", "model", "repeat", "tasks", "tasks_passed", "score", "max_score", "score_pct", "hard_failed"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in summaries:
            writer.writerow({field: row[field] for field in fieldnames})


def _aggregate_by_model(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in summaries:
        groups.setdefault((str(row["provider"]), str(row["model"])), []).append(row)
    aggregate = []
    for (provider, model), rows in groups.items():
        repeats = len(rows)
        aggregate.append(
            {
                "provider": provider,
                "model": model,
                "repeats": repeats,
                "tasks": int(rows[0]["tasks"]) if rows else 0,
                "max_score": int(rows[0]["max_score"]) if rows else 0,
                "tasks_passed_mean": sum(float(row["tasks_passed"]) for row in rows) / repeats,
                "score_mean": sum(float(row["score"]) for row in rows) / repeats,
                "score_pct_mean": sum(float(row["score_pct"]) for row in rows) / repeats,
                "hard_failed_total": sum(int(row["hard_failed"]) for row in rows),
            }
        )
    return sorted(aggregate, key=lambda row: (row["score_pct_mean"], row["tasks_passed_mean"]), reverse=True)


def _estimate_total_tokens(task_paths: list[Path], skills_dir: Path, model_specs: tuple[tuple[str, str], ...], repeats: int) -> int:
    total_chars = 0
    for task_path in task_paths:
        total_chars += len(_build_prompt(task_path, skills_dir))
    prompt_tokens = total_chars // 4
    completion_tokens = len(task_paths) * 900
    return int((prompt_tokens + completion_tokens) * len(model_specs) * max(repeats, 0))


def _parse_model_specs(raw: str) -> tuple[tuple[str, str], ...]:
    specs: list[tuple[str, str]] = []
    for item in (part.strip() for part in raw.split(",") if part.strip()):
        if ":" in item:
            provider, model = item.split(":", 1)
        else:
            provider, model = "poe", item
        provider = provider.strip().lower()
        model = model.strip()
        if provider not in {"poe", "deepseek"}:
            raise SystemExit(f"Unsupported provider {provider!r}. Use poe:<model> or deepseek:<model>.")
        if provider == "poe" and model.lower().startswith("deepseek"):
            raise SystemExit("DeepSeek models must be specified as deepseek:<model>; they are not routed through Poe.")
        specs.append((provider, model))
    return tuple(dict.fromkeys(specs))


def _read_text(path: Path, limit: int | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    if limit is not None and len(text) > limit:
        return text[:limit] + "\n[truncated]"
    return text


def _get_secret(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value.strip('"').strip("'")
    if os.name != "nt":
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            registry_value, _ = winreg.QueryValueEx(key, name)
            return str(registry_value).strip().strip('"').strip("'")
    except OSError:
        return ""


def _git_ref() -> str:
    head = ROOT / ".git" / "HEAD"
    if not head.exists():
        return "unknown"
    value = head.read_text(encoding="utf-8").strip()
    if value.startswith("ref:"):
        ref_path = ROOT / ".git" / value.split(" ", 1)[1]
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8").strip()[:12]
    return value[:12]


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
