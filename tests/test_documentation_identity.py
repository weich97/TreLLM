from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def test_system_docs_use_trellm_identity():
    required_snippets = {
        "docs/getting_started.md": [
            "TreLLM is easiest to evaluate as a sequence of explicit run modes.",
            "TradeArena remains the public leaderboard and ranking surface",
        ],
        "docs/advanced_integrations_security.md": [
            "TreLLM supports optional model, market-data, paper-broker, and future broker-facing integration paths.",
            "TradeArena leaderboard artifacts",
            "Create review files that a human can inspect outside TreLLM",
            "Any adapter that can submit live orders is outside the public TradeArena leaderboard path",
        ],
        "docs/live_trading_readiness.md": [
            "TreLLM should grow beyond offline and paper-only research paths",
            "TradeArena remains the public leaderboard module for comparable rows",
            "| Stage | Name | What TreLLM can do | Required evidence before moving on |",
        ],
        "docs/narrative_positioning.md": [
            "TreLLM should be described as an early-stage live-ready audit and control system",
            "TradeArena should be described as the public leaderboard and benchmark module",
            "TreLLM is an early-stage live-ready audit and control system for moving autonomous",
        ],
        "docs/research_protocol.md": [
            "# TreLLM Research Protocol",
            "TreLLM is meant to support system-style AI finance papers.",
        ],
        "docs/related_work.md": [
            "TreLLM is designed to complement, not replace, existing financial AI and agent frameworks.",
            "TradeArena leaderboard layer keeps the evaluation traceable.",
        ],
        "docs/technical_report.md": [
            "# TreLLM Technical White Paper",
            "TreLLM is an early-stage research prototype and live-readiness audit and control system",
            "TreLLM has two execution simulators.",
            "TreLLM now exposes separate execution assumption classes:",
        ],
    }

    for path, snippets in required_snippets.items():
        text = _normalized(_read_doc(path))
        for snippet in snippets:
            assert _normalized(snippet) in text


def test_live_readiness_avoids_benchmark_module_system_framing():
    text = _normalized(_read_doc("docs/live_trading_readiness.md")).lower()

    assert "trellm should grow beyond a paper-only benchmark module" not in text
