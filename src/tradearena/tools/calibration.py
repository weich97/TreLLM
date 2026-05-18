from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ExecutionCalibrationConfig:
    """Inputs for OHLCV-based execution-model diagnostics.

    OHLCV bars do not identify quoted spread, queue position, or broker latency.
    The config therefore keeps those as explicit assumptions and estimates only
    bar-observable quantities such as range and dollar volume.
    """

    commission_bps: float = 1.0
    spread_bps: float | None = None
    participation_rate: float = 0.05
    latency_steps: int = 1
    market_impact: float = 0.15
    base_slippage_range_multiplier: float = 0.02


def discover_ohlcv_files(data_dir: str | Path, pattern: str = "*.csv") -> list[Path]:
    return sorted(path for path in Path(data_dir).glob(pattern) if path.is_file())


def summarize_execution_calibration(
    files: Iterable[str | Path],
    config: ExecutionCalibrationConfig | None = None,
) -> dict[str, Any]:
    config = config or ExecutionCalibrationConfig()
    symbols: set[str] = set()
    ranges_bps: list[float] = []
    dollar_volumes: list[float] = []
    volumes: list[float] = []
    closes: list[float] = []
    row_count = 0

    for file in files:
        path = Path(file)
        symbol = _symbol_from_filename(path)
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or not {"High", "Low", "Close"}.issubset(reader.fieldnames):
                continue
            for row in reader:
                high = _float(row.get("High"))
                low = _float(row.get("Low"))
                close = _float(row.get("Close"))
                volume = max(0.0, _float(row.get("Volume")))
                if close <= 0 or high <= 0 or low <= 0 or high < low:
                    continue
                symbols.add(symbol)
                row_count += 1
                range_bps = (high - low) / close * 10_000.0
                ranges_bps.append(range_bps)
                volumes.append(volume)
                closes.append(close)
                dollar_volumes.append(close * volume)

    if row_count == 0:
        raise ValueError("No valid OHLCV rows found for execution calibration.")

    median_range_bps = _percentile(ranges_bps, 0.50)
    p90_range_bps = _percentile(ranges_bps, 0.90)
    suggested_base_slippage_bps = max(0.5, min(25.0, median_range_bps * config.base_slippage_range_multiplier))
    assumed_spread_bps = 0.0 if config.spread_bps is None else max(0.0, config.spread_bps)
    impact_bps_at_cap = config.market_impact * config.participation_rate * 10_000.0
    median_volatility_component_bps = 0.1 * median_range_bps
    expected_buy_slippage_bps = (
        assumed_spread_bps / 2.0
        + suggested_base_slippage_bps
        + impact_bps_at_cap
        + median_volatility_component_bps
    )

    return {
        "data": {
            "symbols": sorted(symbols),
            "symbol_count": len(symbols),
            "row_count": row_count,
            "median_close": round(_percentile(closes, 0.50), 6),
            "median_volume": round(_percentile(volumes, 0.50), 6),
            "median_dollar_volume": round(_percentile(dollar_volumes, 0.50), 6),
            "median_intrabar_range_bps": round(median_range_bps, 6),
            "p90_intrabar_range_bps": round(p90_range_bps, 6),
        },
        "assumptions": {
            "commission_bps": config.commission_bps,
            "spread_bps": config.spread_bps,
            "participation_rate": config.participation_rate,
            "latency_steps": config.latency_steps,
            "market_impact": config.market_impact,
            "base_slippage_range_multiplier": config.base_slippage_range_multiplier,
        },
        "suggested_simulator_config": {
            "commission_bps": config.commission_bps,
            "base_slippage_bps": round(suggested_base_slippage_bps, 6),
            "spread_bps": None if config.spread_bps is None else assumed_spread_bps,
            "participation_rate": config.participation_rate,
            "latency_steps": config.latency_steps,
            "market_impact": config.market_impact,
        },
        "diagnostics": {
            "median_volatility_component_bps": round(median_volatility_component_bps, 6),
            "impact_bps_at_participation_cap": round(impact_bps_at_cap, 6),
            "expected_buy_slippage_bps_at_median_range": round(expected_buy_slippage_bps, 6),
            "spread_status": "assumed_zero_or_external" if config.spread_bps is None else "user_supplied",
            "identification_warning": (
                "OHLCV bars do not contain bid-ask quotes, order-book depth, queue position, "
                "broker fees, order timestamps, or realized execution shortfall. Treat this as "
                "a bar-level diagnostic, not broker-grade calibration."
            ),
        },
    }


def write_calibration_json(summary: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_calibration_markdown(summary: dict[str, Any], path: str | Path) -> None:
    data = summary["data"]
    config = summary["suggested_simulator_config"]
    diagnostics = summary["diagnostics"]
    spread_value = "not supplied" if config["spread_bps"] is None else str(config["spread_bps"])
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Execution Calibration Diagnostic",
        "",
        "This diagnostic is computed from OHLCV bars. It estimates bar-observable range and volume quantities, while spread, fees, market impact, and latency remain explicit assumptions unless quote, broker, or order-log data are supplied.",
        "",
        "## Data Summary",
        "",
        f"- Symbols: {data['symbol_count']}",
        f"- Rows: {data['row_count']}",
        f"- Median close: {data['median_close']}",
        f"- Median volume: {data['median_volume']}",
        f"- Median dollar volume: {data['median_dollar_volume']}",
        f"- Median intrabar range: {data['median_intrabar_range_bps']} bps",
        f"- P90 intrabar range: {data['p90_intrabar_range_bps']} bps",
        "",
        "## Suggested Simulator Configuration",
        "",
        "| Parameter | Value | Status |",
        "| --- | ---: | --- |",
        f"| `commission_bps` | {config['commission_bps']} | user/broker assumption |",
        f"| `base_slippage_bps` | {config['base_slippage_bps']} | OHLCV range proxy |",
        f"| `spread_bps` | {spread_value} | quote data required if not supplied |",
        f"| `participation_rate` | {config['participation_rate']} | policy cap |",
        f"| `latency_steps` | {config['latency_steps']} | system/broker log assumption |",
        f"| `market_impact` | {config['market_impact']} | execution-log fit required |",
        "",
        "## Model-Implied Slippage Components",
        "",
        f"- Median volatility component: {diagnostics['median_volatility_component_bps']} bps",
        f"- Impact at participation cap: {diagnostics['impact_bps_at_participation_cap']} bps",
        f"- Expected buy slippage at median range: {diagnostics['expected_buy_slippage_bps_at_median_range']} bps",
        "",
        "## Identification Warning",
        "",
        diagnostics["identification_warning"],
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def _symbol_from_filename(path: Path) -> str:
    stem = path.stem
    for suffix in ("_Daily_2021_2026", "_Daily", "_Hourly_1h", "_Hourly", "_1h", "_5m", "_15m"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = max(0.0, min(1.0, quantile)) * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction
