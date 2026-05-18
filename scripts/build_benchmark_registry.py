from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tradearena.evaluation.submissions import build_registry_rows, write_registry_html, write_registry_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a TradeArena community benchmark registry.")
    parser.add_argument("input", help="Submission JSON file or directory containing JSON submissions.")
    parser.add_argument("--output", default="docs/results/community_registry.md")
    parser.add_argument("--csv-output", default="docs/results/community_registry.csv")
    parser.add_argument("--html-output", default="docs/results/community_registry.html")
    args = parser.parse_args(argv)

    rows, errors = build_registry_rows(args.input)
    if errors:
        print("Benchmark registry build failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    write_registry_markdown(rows, args.output)
    _write_csv(rows, args.csv_output)
    write_registry_html(rows, args.html_output)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.csv_output}")
    print(f"Wrote {args.html_output}")
    print(f"Accepted submissions: {len(rows)}")
    return 0


def _write_csv(rows: list[dict[str, object]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "scenario_id",
        "agent_type",
        "model_family",
        "model_redacted",
        "data_source",
        "frequency",
        "symbols",
        "total_return",
        "max_drawdown",
        "fill_rate",
        "rejected_orders",
        "risk_edits",
        "audit_coverage",
        "reproducibility_hash",
        "source_file",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    raise SystemExit(main())
