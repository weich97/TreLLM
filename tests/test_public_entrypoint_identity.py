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
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_claim_and_validation_docs_use_trellm_for_system_claims():
    required_snippets = {
        "docs/benchmark_maturity.md": [
            "TreLLM should be presented as an early-stage research prototype until three forms of evidence exist in public:",
            "TradeArena can credibly describe its leaderboard as a niche benchmark only after the following minimum evidence exists:",
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
        "scripts/run_showcase.py": [
            'description="Build the public-facing TreLLM showcase."',
            "print(\"TreLLM showcase\", flush=True)",
            "<title>TreLLM - Trading Audit And Control Showcase</title>",
            "<h1>TreLLM: LLM Trading Audit And Control</h1>",
            "What TreLLM is not:",
            "TradeArena is the public leaderboard and benchmark module",
        ],
    }
    for path, snippets in required_snippets.items():
        text = _normalized(_read_text(path))
        for snippet in snippets:
            assert _normalized(snippet) in text
