# Execution Model And Calibration

TradeArena's execution layer is a configurable paper-execution stress model. It
is designed to make execution assumptions explicit and replayable. It should not
be read as broker-grade transaction-cost analysis unless the parameters are
calibrated with venue quotes, broker fee schedules, order timestamps, and
realized fills.

## Simulator Equation

`RealisticOrderSimulator` delays orders by `latency_steps`, caps per-symbol
fills by `bar.volume * participation_rate`, enforces cash and inventory
constraints, and prices market orders with:

```text
slip_rate =
  spread_bps / 20000
  + base_slippage_bps / 10000
  + market_impact * (filled_quantity / volume)
  + 0.1 * ((high - low) / close)
```

For buys, `fill_price = close * (1 + slip_rate)`. For sells,
`fill_price = close * (1 - slip_rate)`. Commissions are charged as basis points
of traded notional.

## Parameter Provenance

| Parameter | Role in simulator | Default | What is needed for calibration | Current default status |
| --- | --- | ---: | --- | --- |
| `commission_bps` | Explicit fee on traded notional | `1.0` | Broker or exchange fee schedule | User assumption |
| `spread_bps` | Full quoted bid-ask spread; market order crosses half | `0.0` | Quote/NBBO or order-book snapshots | User-supplied; high-spread demos set it explicitly |
| `base_slippage_bps` | Residual shortfall before spread, impact, and bar volatility | `2.0` | Historical order/fill shortfall after spread adjustment | Stress assumption or OHLCV proxy |
| `participation_rate` | Maximum fillable fraction of bar volume | `0.05` | Execution policy or parent-order participation target | Policy cap |
| `latency_steps` | Number of bars before an order becomes eligible | `1` | Order submission and acknowledgement/fill timestamps | Scenario assumption |
| `market_impact` | Linear coefficient on participation | `0.15` | Regression of implementation shortfall on participation using fill logs | Conservative stress assumption |
| `(high-low)/close` | Intrabar volatility component | data-derived | OHLCV bars | Observable in historical bars |

The default parameters are intentionally conservative stress-test settings for
comparing agents under identical frictions. They are not claimed to be universal
market constants.

## What OHLCV Can And Cannot Identify

The tracked Yahoo Finance daily and hourly files provide open, high, low, close,
and volume. They can support diagnostics such as median range, tail range, dollar
volume, and whether a participation cap is plausible for a proposed order size.
They do not contain:

- quoted bid and ask;
- queue depth or order-book imbalance;
- broker/exchange fee tier;
- order submission, acknowledgement, cancellation, or fill timestamps;
- realized execution shortfall for a real order.

As a result, OHLCV-based calibration can only produce a bar-level diagnostic. A
proper transaction-cost calibration should use quote and fill logs, then fit the
spread, residual slippage, latency, and impact terms against realized shortfall.

## Reproducible Diagnostic

Run:

```bash
python scripts/calibrate_execution_model.py \
  --data-dir data/real/yahoo_intraday_1h_50 \
  --output docs/results/execution_calibration_intraday_1h.json \
  --markdown-output docs/results/execution_calibration_intraday_1h.md
```

The generated report records the data coverage, OHLCV-derived range and volume
statistics, the explicit assumptions, and the model-implied slippage components.
If `--spread-bps` is omitted, the report marks spread as unobserved rather than
pretending it was estimated from OHLCV data.

## Interpretation Boundary

Use the default execution model to compare agents under the same transparent
frictions, to stress-test risk gates, and to measure how decisions change after
partial fills or rejections. Use calibrated quote/fill parameters before making
claims about live venue execution quality, expected alpha after costs, or
broker-specific implementation shortfall.
