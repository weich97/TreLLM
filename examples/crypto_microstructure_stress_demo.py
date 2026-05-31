from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradearena.core.serialization import write_json
from tradearena.factory import build_default_system

OUTPUT_DIR = Path("outputs/examples/crypto_microstructure_stress")


def main() -> int:
    system = build_default_system(
        name="crypto_microstructure_stress",
        symbols=("BTC-USD", "ETH-USD", "SOL-USD"),
        periods=72,
        seed=21,
        strategy_name="signal-weighted",
        analyst_names=("momentum", "macro-news"),
        execution_mode="realistic",
        spread_bps=18.0,
        slippage_bps=8.0,
        participation_rate=0.003,
        latency_steps=2,
        market_impact=0.35,
        max_position_weight=0.25,
        synthetic_volatility_scale=3.2,
        synthetic_tail_df=3,
        synthetic_jump_probability=0.08,
        synthetic_jump_scale=0.10,
    )
    trajectory, metrics = system.run()
    reports = [step.execution_report for step in trajectory.steps if step.execution_report]
    summary = {
        "scenario": "no-key synthetic crypto microstructure stress",
        "symbols": ["BTC-USD", "ETH-USD", "SOL-USD"],
        "steps": len(trajectory.steps),
        "total_return": metrics["total_return"],
        "max_drawdown": metrics["max_drawdown"],
        "execution_fill_rate": metrics["execution_fill_rate"],
        "rejected_order_count": metrics["rejected_order_count"],
        "partial_fill_count": metrics["partial_fill_count"],
        "total_slippage_cost": metrics["total_slippage_cost"],
        "avg_latency_steps": metrics["avg_latency_steps"],
        "submitted_orders": sum(int(report.get("submitted_orders", 0)) for report in reports),
        "pending_orders_last": int(reports[-1].get("pending_orders", 0)) if reports else 0,
        "config": {
            "spread_bps": 18.0,
            "base_slippage_bps": 8.0,
            "participation_rate": 0.003,
            "latency_steps": 2,
            "market_impact": 0.35,
            "synthetic_volatility_scale": 3.2,
            "synthetic_tail_df": 3,
            "synthetic_jump_probability": 0.08,
            "synthetic_jump_scale": 0.10,
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", summary)
    _write_svg(OUTPUT_DIR / "crypto_microstructure_stress.svg", summary)
    print("Crypto microstructure stress demo")
    print(f"  fill_rate={summary['execution_fill_rate']:.3f} rejected={summary['rejected_order_count']} slippage={summary['total_slippage_cost']:.2f}")
    print(f"  wrote={OUTPUT_DIR / 'summary.json'}")
    print(f"  wrote={OUTPUT_DIR / 'crypto_microstructure_stress.svg'}")
    return 0


def _write_svg(path: Path, summary: dict[str, object]) -> None:
    width, height = 920, 420
    metrics = [
        ("Fill rate", float(summary["execution_fill_rate"]), 1.0, "#2563eb"),
        ("Rejected", float(summary["rejected_order_count"]), max(1.0, float(summary["submitted_orders"])), "#dc2626"),
        ("Partial fills", float(summary["partial_fill_count"]), max(1.0, float(summary["submitted_orders"])), "#f59e0b"),
        ("Latency", float(summary["avg_latency_steps"]), 3.0, "#7c3aed"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Crypto microstructure stress demo">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        _text(38, 52, "No-key crypto microstructure stress", 24, "#0f172a", 800),
        _text(38, 82, "High volatility, low participation, spread, latency, partial fills, and rejections under the same audit loop.", 13, "#64748b", 500),
    ]
    y = 130
    for idx, (label, value, denom, color) in enumerate(metrics):
        yy = y + idx * 58
        width_value = min(420.0, 420.0 * value / denom)
        parts.append(f'<rect x="38" y="{yy}" width="420" height="22" rx="6" fill="#e2e8f0"/>')
        parts.append(f'<rect x="38" y="{yy}" width="{width_value:.1f}" height="22" rx="6" fill="{color}"/>')
        parts.append(_text(478, yy + 17, f"{label}: {value:.3f}", 13, "#0f172a", 800))
    parts.append('<rect x="38" y="352" width="820" height="1" fill="#cbd5e1"/>')
    parts.append(_text(38, 382, f"Total slippage cost: ${float(summary['total_slippage_cost']):,.2f} | Max drawdown: {float(summary['max_drawdown']):.2%}", 13, "#334155", 800))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _text(x: float, y: float, value: str, size: int, color: str, weight: int) -> str:
    return f'<text x="{x}" y="{y}" font-family="Inter,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(str(value))}</text>'


if __name__ == "__main__":
    raise SystemExit(main())
