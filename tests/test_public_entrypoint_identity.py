from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def test_github_templates_explain_trellm_and_tradearena_roles():
    required_snippets = {
        ".github/ISSUE_TEMPLATE/bug_report.yml": [
            "Report a reproducible TreLLM system or TradeArena leaderboard issue",
        ],
        ".github/ISSUE_TEMPLATE/research_extension.yml": [
            "Suggest an experiment that could strengthen the TreLLM system research or TradeArena leaderboard suite",
            "Paper, system, or leaderboard output",
        ],
        ".github/PULL_REQUEST_TEMPLATE.md": [
            "TreLLM system change",
            "TradeArena leaderboard or registry artifact update",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_package_docstring_uses_trellm_system_identity():
    import tradearena

    docstring = tradearena.__doc__ or ""

    assert "TreLLM: LLM-driven trading audit and control system" in docstring
    assert "TradeArena compatibility API" in docstring
    assert "TradeArena: pluggable AI trading agent research framework" not in docstring


def test_contributor_docs_keep_system_and_leaderboard_identity_separate():
    required_snippets = {
        "docs/contributor_roadmap.md": [
            "TreLLM grows best when contributions make financial AI agents easier to evaluate, audit, reproduce, control, or extend.",
            "These contributions strengthen the TradeArena leaderboard and benchmark module.",
        ],
        "docs/community_participation.md": [
            "TreLLM should not describe itself as community-backed until public, reviewable participation exists.",
            "TradeArena leaderboard row",
            'early-stage research prototype with a public TradeArena leaderboard module',
        ],
        "docs/community_milestones.md": [
            "Goal: make the first public TreLLM audit release easier to cite, reproduce, and review while keeping TradeArena benchmark rows comparable.",
            "New adapters: link the data, broker, or model interface you want TreLLM to support.",
        ],
        "docs/community_operations.md": [
            "We maintain TreLLM, an early-stage live-ready audit and control system for auditing",
            "TradeArena can package comparable benchmark manifests and leaderboard evidence",
        ],
        "docs/launch/discussion_seeds.md": [
            "We want community leaderboard submissions without exposing raw provider prompts or",
            "Reply with the fields you would be comfortable sharing in a public leaderboard row.",
        ],
        "docs/launch/issue_backlog.md": [
            "How should community leaderboard submissions redact provider prompts/responses?",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_claim_and_validation_docs_use_trellm_for_system_claims():
    required_snippets = {
        "docs/benchmark_maturity.md": [
            "TreLLM should be presented as an early-stage research prototype until three forms of evidence exist in public:",
            "TreLLM can credibly describe itself as externally validated, and TradeArena can credibly describe its leaderboard module as a niche benchmark",
        ],
        "docs/claim_boundaries.md": [
            "TreLLM separates three kinds of claims.",
            "The TradeArena leaderboard rows carry explicit evidence labels:",
        ],
        "docs/external_validation_quickstart.md": [
            "TreLLM needs external evidence",
            "TradeArena leaderboard rows",
            "TreLLM should not claim community validation",
        ],
        "docs/external_validation.md": [
            "External validation is the evidence that makes TreLLM more than a maintainer-run demo.",
            "accepted validations can be linked from the TradeArena leaderboard registry or release notes.",
        ],
        "docs/academic_report_plan.md": [
            "TreLLM currently has technical documentation and TradeArena leaderboard artifacts.",
            "TreLLM can run auditable offline and paper/sandbox agent loops",
            "TradeArena can compare agents under shared risk and execution assumptions",
        ],
        "docs/demo_matrix.md": [
            "This matrix maps TreLLM capabilities to hands-on repository artifacts.",
            "how TreLLM should progress from paper research to broker-review exports",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_skill_experiment_docs_assign_audit_research_to_trellm():
    required_snippets = {
        "docs/agent_skills.md": [
            "The task suite measures TreLLM-specific financial-audit ability rather than trading ability:",
        ],
        "docs/poe_skill_task_experiments.md": [
            "TreLLM already has synthetic, real-market, execution-shock, classical-baseline, and calibration snapshots, with TradeArena providing the comparable leaderboard surface.",
        ],
    }
    forbidden_snippets = {
        "docs/agent_skills.md": [
            "The task suite measures TradeArena-specific audit ability rather than trading ability:",
        ],
        "docs/poe_skill_task_experiments.md": [
            "TradeArena already has synthetic, real-market, execution-shock, classical-baseline, and calibration snapshots.",
        ],
    }

    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text

    for path, snippets in forbidden_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) not in text


def test_claim_review_examples_assign_recording_claims_to_trellm():
    required_snippets = {
        "docs/claim_boundary_review_quickstart.md": [
            '"TreLLM records replayable trajectory artifacts with hashes; TradeArena can publish the resulting leaderboard evidence."',
        ],
        "examples/skill_tasks/claim_boundary_001/candidate_claims.md": [
            "TreLLM records every agent decision as a replayable intent-to-execution trajectory.",
        ],
        "examples/skill_tasks/claim_boundary_provider_drift_001/candidate_claims.md": [
            '"TreLLM records model intent, risk edits, simulated fills, and replay hashes for paper-only benchmark runs summarized in TradeArena rows."',
        ],
        "examples/skill_task_answers/reference/claim_boundary_001.md": [
            "that TreLLM can record a trajectory from intent to risk and execution state.",
            "TradeArena can present the resulting evidence as a leaderboard artifact.",
            "The single-run profitability claim is unsupported and should be weakened",
        ],
        "examples/skill_task_answers/reference/claim_boundary_provider_drift_001.md": [
            "Claim 2 is an engineering claim: TreLLM records intent, risk edits, simulated fills, and replay hashes for paper-only benchmark runs.",
            "TradeArena can summarize that evidence as a leaderboard row, but the recording capability belongs to TreLLM.",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_launch_and_pages_sources_use_trellm_for_public_positioning():
    required_snippets = {
        "docs/blog/why_llm_trading_agents_need_audit_benchmarks.md": [
            "TreLLM takes a different view. It treats a financial AI agent as an auditable decision-making system:",
            "TreLLM renders this as a browser-readable audit report",
            "TradeArena is its public leaderboard and benchmark module",
        ],
        "docs/launch/README.md": [
            "# TreLLM Project Metadata",
            "TreLLM's public positioning is:",
            "TreLLM turns every financial-agent decision into a traceable trajectory:",
            "LLM-driven trading audit and control system with replayable trajectories, risk gates, paper execution, and TradeArena leaderboard artifacts.",
        ],
        "docs/launch/pages_demo.md": [
            "TreLLM publishes the project landing page and quickstart showcase",
        ],
        ".github/workflows/pages.yml": [
            "TreLLM static demo generated by:",
        ],
        "scripts/run_showcase.py": [
            'description="Build the public-facing TreLLM showcase."',
            "print(\"TreLLM showcase\", flush=True)",
            "<title>TreLLM - Trading Audit And Control Showcase</title>",
            "<h1>TreLLM: LLM Trading Audit And Control</h1>",
            "<title>TreLLM 3-Minute Demo Video</title>",
            "<h1>TreLLM 3-Minute Demo Video</h1>",
            "<h1>TreLLM Showcase: Quickstart Tour</h1>",
            'aria-label="TreLLM 3-minute demo video"',
            "What TreLLM is not:",
            "TradeArena is the public leaderboard and benchmark module",
        ],
        "scripts/build_demo_video.py": [
            'draw.text((72, 36), "TreLLM", fill="#ccfbf1", font=fonts["brand"])',
        ],
        "scripts/validate_demo_artifacts.py": [
            'description="Validate required TreLLM demo artifacts."',
        ],
        "scripts/run_launch_demo.py": [
            'description="Run the offline TreLLM launch demo."',
            'print("TreLLM launch demo", flush=True)',
            "<title>TreLLM Demo Portal</title>",
            "<h1>TreLLM Demo Portal</h1>",
        ],
        "scripts/run_paper_design_demos.py": [
            'print("TreLLM experiment-design demo suite")',
            "<title>TreLLM Experiment-Design Demos</title>",
            "<h1>TreLLM Experiment-Design Demos</h1>",
        ],
        "examples/akshare_csv_reuse_demo.py": [
            'print("AkShare -> normalized CSV -> TreLLM demo")',
            '("TreLLM", "risk + execution + trajectory")',
            "A-share data path: AkShare -> normalized CSV -> existing TreLLM runner",
        ],
        "examples/rl_policy_baseline_demo.py": [
            "A deterministic CI-safe strategy emits normal TreLLM decisions and reuses risk, execution, and evaluation.",
        ],
        "examples/visual_tour_demo.py": [
            'description="Generate animated offline TreLLM visual-tour artifacts."',
            "TreLLM turns trajectories into mechanism probes",
            "<title>TreLLM Visual Tour: Audit, Execution, Diagnostics</title>",
            "<h1>TreLLM Visual Tour: Audit, Execution, Diagnostics</h1>",
        ],
        "examples/retail_planner_demo.py": [
            "<title>TreLLM Retail Planning Demo</title>",
            "<h1>TreLLM Retail Planning Demo</h1>",
        ],
        "examples/crisis_snapshot_demo.py": [
            "<title>TreLLM Crisis Snapshot Gallery</title>",
            "<h1>TreLLM Crisis Snapshot Gallery</h1>",
        ],
        "scripts/render_audit_report.py": [
            'description="Render a TreLLM trajectory as a compact HTML audit report."',
            "Trajectory JSON written by a TreLLM run.",
            "<title>TreLLM Audit Report: Replayable Decision Trace</title>",
            "<h1>TreLLM Audit Report: Replayable Decision Trace</h1>",
        ],
        "scripts/render_agent_autopsy_dashboard.py": [
            "Trajectory JSON written by a TreLLM run.",
        ],
        "scripts/run_failure_autopsy.py": [
            'description="Classify TreLLM trajectory failure modes."',
        ],
        "scripts/run_bge_m3_probe.py": [
            'description="Validate TreLLM representation signatures with local BGE-family Transformer embeddings."',
        ],
        "docs/assets/audit_report_preview.svg": [
            'aria-label="TreLLM audit report preview"',
            ">TreLLM Audit Report<",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_developer_docs_use_trellm_for_system_surfaces():
    required_snippets = {
        "docs/artifact_portability.md": [
            "TreLLM artifacts should be easy to move between local machines",
        ],
        "docs/observability.md": [
            "TreLLM trajectories are already structured logs.",
        ],
        "docs/plugin_development.md": [
            "TreLLM plugins are small Python objects that implement one narrow protocol:",
        ],
        "docs/extension_walkthrough.md": [
            "TreLLM is designed around narrow protocol surfaces.",
        ],
        "docs/public_artifact_privacy.md": [
            "TreLLM separates local debugging records from public TradeArena leaderboard artifacts.",
        ],
        "docs/execution_model_boundaries.md": [
            "TreLLM separates execution assumptions into explicit import surfaces:",
        ],
        "docs/schemas.md": [
            "# TreLLM Schemas",
            "TreLLM treats a financial AI agent as an auditable reliability lifecycle",
        ],
        "docs/retail_planning.md": [
            "TreLLM includes an offline-friendly planning layer",
        ],
        "docs/market_rules.md": [
            "TreLLM's default simulator is market-agnostic.",
            "TreLLM now exposes these as testable rule-package helpers",
        ],
        "docs/financial_audit_agent_benchmark.md": [
            "TreLLM skills are evaluated as audit workflows, not as trading strategies.",
        ],
        "docs/execution_model.md": [
            "TreLLM's execution layer is a configurable paper-execution stress model.",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_utility_cli_help_uses_trellm_for_system_artifacts():
    required_snippets = {
        "scripts/render_agent_autopsy_dashboard.py": [
            'description="Render an Agent Autopsy Dashboard from a TreLLM trajectory."',
        ],
        "scripts/hash_run.py": [
            'description="Compute a reproducibility hash for a TreLLM trajectory JSON."',
        ],
        "scripts/validate_broker_approval_artifact.py": [
            'description="Validate a TreLLM broker approval artifact."',
        ],
        "scripts/validate_broker_handoff_artifact.py": [
            'description="Validate a TreLLM broker handoff artifact."',
        ],
        "scripts/validate_broker_response_artifact.py": [
            'description="Validate a TreLLM broker response artifact."',
        ],
        "scripts/validate_broker_approval_binding.py": [
            'description="Validate that a TreLLM broker approval binds to a handoff artifact."',
        ],
        "scripts/hash_broker_handoff_artifact.py": [
            'description="Validate and hash a TreLLM broker handoff artifact."',
        ],
        "scripts/calibrate_execution_model.py": [
            'description="Generate OHLCV-based diagnostics for the TreLLM execution simulator."',
        ],
        "scripts/compare_execution_to_fills.py": [
            'description="Compare TreLLM execution assumptions against historical order/fill logs."',
        ],
        "scripts/calibrate_quote_fill_model.py": [
            'description="Fit TreLLM execution parameters from top-of-book quotes and realized fills."',
        ],
        "scripts/download_yahoo_daily.py": [
            'description="Download normalized Yahoo Finance OHLCV CSV files for TreLLM."',
        ],
        "scripts/run_crisis_scene_experiments.py": [
            'description="Run real-market crisis-scene experiments for TreLLM."',
        ],
        "scripts/run_embedding_provider_probe.py": [
            'description="Run a 10-step embedding-provider robustness probe for TreLLM."',
        ],
        "scripts/validate_reproduction_report.py": [
            'description="Validate a TreLLM external reproduction report."',
        ],
        "src/tradearena/cli.py": [
            'description="Validate a TreLLM broker response artifact."',
            'description="Validate a TreLLM broker handoff artifact."',
            'description="Validate a TreLLM broker approval artifact."',
            'description="Validate and hash a TreLLM broker handoff artifact."',
        ],
        "src/tradearena/tools/broker_export.py": [
            "Convert TreLLM order intent into broker handoff rows.",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_broker_artifact_schemas_use_trellm_system_identity():
    required_snippets = {
        "schemas/broker_handoff_artifact.schema.json": [
            '"title": "TreLLM Broker Handoff Artifact"',
        ],
        "schemas/broker_approval_artifact.schema.json": [
            '"title": "TreLLM Broker Approval Artifact"',
        ],
        "schemas/broker_response_artifact.schema.json": [
            '"title": "TreLLM Broker Response Artifact"',
        ],
    }
    forbidden_snippets = {
        path: [snippet.replace("TreLLM", "TradeArena") for snippet in snippets]
        for path, snippets in required_snippets.items()
    }

    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text

    for path, snippets in forbidden_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) not in text

    broker_export_text = _normalized(_read_text("src/tradearena/tools/broker_export.py"))
    assert "Convert TradeArena orders into broker handoff rows." not in broker_export_text


def test_generated_public_copy_sources_use_trellm_system_identity():
    required_snippets = {
        "docs/agent_skills.md": [
            "# TreLLM Agent Skills",
            "TreLLM agent skills are repository workflow templates for audit",
        ],
        "scripts/build_demo_video.py": [
            '"title": "TreLLM in 3 Minutes"',
            "TreLLM separates intended allocation from what the market simulator can actually fill.",
            '"title": "What TreLLM is for"',
            'description="Build a captioned 3-minute TreLLM demo video."',
            '"TreLLM showcase"',
        ],
        "scripts/score_skill_task_report.py": [
            "# TreLLM Skill Task Matrix",
            "TreLLM skills help agents inspect, reproduce, audit, and extend TradeArena leaderboard artifacts.",
        ],
        "scripts/scan_public_artifacts.py": [
            "Scan public TreLLM artifacts for raw prompt/response or secret leakage.",
        ],
        "scripts/build_benchmark_page.py": [
            "TreLLM is a financial-agent reliability audit and control system. TradeArena is the",
            "public leaderboard and benchmark-card module inside that system",
        ],
        "docs/results/benchmark_v0_2.md": [
            "TreLLM is a financial-agent reliability audit and control system. TradeArena is the public leaderboard",
            "benchmark-card module inside that system",
        ],
        "docs/benchmark_submissions.md": [
            "TradeArena accepts redacted leaderboard manifests so users can compare runs",
        ],
        "docs/schemas.md": [
            "## Redacted Leaderboard Submission Schema",
            "External TradeArena rows can be shared without exposing raw provider prompts or responses.",
        ],
        "docs/launch/discussion_seeds.md": [
            "TreLLM currently records observation, signals, proposed decisions, approved",
            "If you use TreLLM in a class, project, or internal evaluation",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_public_copy_avoids_community_benchmark_submission_framing():
    forbidden_snippets = {
        "docs/schemas.md": [
            "Community Benchmark Submission Schema",
            "External benchmark rows can be shared",
        ],
        "docs/launch/discussion_seeds.md": [
            "community benchmark submissions",
            "public benchmark submission",
        ],
        "docs/launch/issue_backlog.md": [
            "community benchmark submissions",
        ],
        "docs/launch/release_notes_v0.2.0.md": [
            "Redacted benchmark submissions",
        ],
    }
    for path, snippets in forbidden_snippets.items():
        text = _normalized(_read_text(path)).lower()
        for snippet in snippets:
            assert _normalized(snippet).lower() not in text


def test_release_notes_use_trellm_for_system_release_positioning():
    required_snippets = {
        "docs/launch/release_notes_v0.2.1.md": [
            "TreLLM v0.2.1 is a patch-release candidate focused on evidence quality",
            "TreLLM remains an audit and live-readiness control system.",
            "TradeArena remains the public leaderboard and benchmark module",
            "Release readiness now checks public identity boundaries before publication.",
        ],
        "docs/launch/release_notes_v0.2.0.md": [
            "TreLLM v0.2.0 is the first protocol-focused release for the TradeArena benchmark module.",
        ],
        "docs/launch/release_notes_v0.1.0.md": [
            "# v0.1.0: TreLLM Audit And Control Release With TradeArena Benchmark Module",
            "TreLLM v0.1.0 is the first public TreLLM release for evaluating LLM",
            "TradeArena benchmark module for comparable rows.",
            "TreLLM is not a live trading bot and does not promise profitable trading.",
            "It is an audit and control system with the TradeArena benchmark module",
            "v0.1.0: TreLLM audit and control release with TradeArena benchmark module",
        ],
        "docs/launch/release_notes_v0.1.1.md": [
            "TreLLM v0.1.1 is a small maintenance release focused on making execution",
        ],
        "docs/launch/release_notes_v0.1.2.md": [
            "TreLLM v0.1.2 is the first PyPI-ready release under the",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_launch_backlog_uses_trellm_for_future_system_tasks():
    required_snippets = {
        "docs/launch/issue_backlog.md": [
            "Build an offline broker-review adapter that converts approved TreLLM orders",
            "wrapped as a TreLLM strategy or analyst through the `tradearena` package interfaces.",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_extension_and_skill_surfaces_use_trellm_system_identity():
    required_snippets = {
        "examples/README.md": [
            "# TreLLM Hands-On Examples",
            "These examples are designed for the first hour after cloning TreLLM.",
            "Shows how two leaderboard cases share the same market, risk, execution, and evaluation stack.",
            "Converts approved TreLLM orders into neutral JSON/CSV rows for Alpaca-style broker review.",
        ],
        "docs/plugin_interfaces.md": [
            "# TreLLM Plugin Interfaces",
            "The TreLLM system intentionally keeps interfaces narrow.",
            "A new LLM agent, FinRL policy, broker adapter, or risk model should be able to enter by implementing only the protocol it owns.",
        ],
        "docs/broker_adapter_contract.md": [
            "This contract defines the minimum bar for any TreLLM adapter that touches a broker",
            "- reconciliation status against the original TreLLM order.",
        ],
        "skills/README.md": [
            "# TreLLM Agent Skills",
            "TreLLM skills are workflow templates for humans, reviewers, and coding agents",
            "| `tradearena-plugin-author` | Author or review narrow TreLLM plugins |",
            "Skills should prefer existing TreLLM validation commands over ad hoc scripts.",
        ],
        "skills/skill_template/SKILL.md": [
            "# TreLLM Skill Template",
            "- inspect a TreLLM trajectory JSON;",
            "Prefer existing TreLLM commands before inventing new scripts:",
        ],
        "skills/skill_template/resources/safety_boundary.md": [
            "TreLLM skills operate on repository artifacts and local files.",
        ],
        "skills/tradearena-claim-boundary-review/SKILL.md": [
            "# TreLLM Claim Boundary Review Skill",
        ],
        "skills/tradearena-execution-calibration/SKILL.md": [
            "# TreLLM Execution Calibration Skill",
        ],
        "skills/tradearena-plugin-author/SKILL.md": [
            "# TreLLM Plugin Author Skill",
        ],
        "skills/tradearena-reproduction-review/SKILL.md": [
            "# TreLLM Reproduction Review Skill",
        ],
        "skills/tradearena-risk-gate-review/SKILL.md": [
            "# TreLLM Risk Gate Review Skill",
            "Review TreLLM risk-manager behavior without treating return as the primary outcome.",
        ],
        "skills/tradearena-trajectory-audit/SKILL.md": [
            "# TreLLM Trajectory Audit Skill",
            "Audit a TreLLM trajectory from agent intent to risk-gated decision",
        ],
        "docs/agent_skills_index.md": [
            "# TreLLM Agent Skills Index",
            "Skills are TreLLM repository workflows for audit, reproduction, calibration,",
            "unless recorded in the TradeArena run manifest.",
            "Review TreLLM risk-manager behavior without treating return as the primary outcome.",
            "Audit a TreLLM trajectory from agent intent to risk-gated decision",
        ],
        "examples/skill_tasks/README.md": [
            "# TreLLM Skill Task Suite",
            "human reviewer or coding agent can use TreLLM skills without turning them into trading prompts.",
        ],
        "examples/skill_task_answers/README.md": [
            "# TreLLM Skill Task Answers",
        ],
        "examples/skill_tasks_challenge/README.md": [
            "# TreLLM Challenge Skill Tasks",
        ],
        "scripts/build_skill_index.py": [
            'description="Build the TreLLM agent skill index."',
            '"# TreLLM Agent Skills Index"',
        ],
        "scripts/score_skill_task.py": [
            'description="Validate or score TreLLM skill task rubrics."',
        ],
        "scripts/score_skill_task_report.py": [
            'description="Build the TreLLM skill task matrix report."',
        ],
        "scripts/run_poe_skill_task_matrix.py": [
            "Run provider-hosted models on TreLLM financial-audit skill tasks.",
        ],
        "scripts/validate_skill_contract.py": [
            'description="Validate TreLLM agent skill contracts."',
        ],
        "examples/extension_walkthrough_demo.py": [
            "This run demonstrates the TreLLM contribution path:",
            'aria-label="TreLLM extension walkthrough"',
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_citation_and_research_report_keep_system_and_leaderboard_identity_separate():
    required_snippets = {
        "CITATION.cff": [
            "If you use TreLLM in research, please cite the arXiv technical report.",
            "If you use TradeArena leaderboard artifacts or a specific software release",
            "title: \"TreLLM: An LLM-Driven Trading Audit and Control System with TradeArena Leaderboard Artifacts\"",
            "title: \"Representation Signatures and Risk-Feedback Alignment in LLM Trading Agents\"",
        ],
        "docs/research_report.md": [
            "The public technical report for TreLLM research claims and TradeArena leaderboard artifacts is:",
            "Use the report for research claims about representation signatures",
            "Use repository release citations for software-version-specific reproduction.",
        ],
        "README.md": [
            "If you use TreLLM in research or cite TradeArena leaderboard artifacts, please cite the technical report:",
        ],
        "pyproject.toml": [
            'description = "TreLLM: LLM-driven trading audit and control system with replayable trajectories, risk gates, and TradeArena leaderboard artifacts."',
            'authors = [{ name = "TreLLM Contributors" }]',
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text
