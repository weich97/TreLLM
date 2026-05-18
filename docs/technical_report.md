# TradeArena Technical White Paper

TradeArena is an early-stage research prototype for studying whether
LLM-assisted trading agents can be evaluated through replayable trajectories,
explicit execution assumptions, and auditable risk gates. This white paper
documents the current engineering model. It is not financial advice, not a live
trading system, and not a claim that the default parameters are calibrated to a
specific broker or venue.

## 1. System Scope

The runner treats each timestamp as an explicit decision lifecycle:

```text
observation -> analyst signal -> target-weight decision -> risk gate
  -> order conversion -> paper execution -> portfolio state -> audit metrics
```

The lifecycle is implemented through narrow interfaces:

| Surface | Current implementation examples | Audit role |
| --- | --- | --- |
| Data provider | Synthetic market, normalized CSV market data | Defines observable prices, volume, news, macro, filings, and alternative data |
| Analyst | Deterministic momentum/news analysts, cache-backed LLM analyst | Emits per-symbol signals or target weights |
| Strategy | Signal-weighted, memory-aware, buy-and-hold, mean-variance, mock RL | Converts signals into target-weight decisions |
| Risk manager | `MaxPositionRiskManager`, `NoRiskManager` | Clips, blocks, monitors, and records risk interventions |
| Execution simulator | `SimpleOrderSimulator`, `RealisticOrderSimulator` | Converts orders into fills, partial fills, pending orders, and rejections |
| Evaluator | Performance, risk audit, execution realism, behavior diagnostics | Summarizes return, drawdown, fill quality, risk edits, and replay coverage |

The primary design choice is to preserve both the model's intended allocation
and the executable allocation after risk intervention. That distinction is what
lets a user inspect whether results came from a model decision, a risk gate, or
an execution assumption.

## 2. Execution Simulation Model

TradeArena has two execution simulators.

`SimpleOrderSimulator` is an idealized baseline. It fills eligible market orders
immediately at close plus fixed slippage and commission, subject to cash and
inventory constraints.

`RealisticOrderSimulator` is the default stress model. It is a paper-execution
simulator with latency, participation caps, spread, slippage, market impact,
cash checks, inventory checks, partial fills, pending orders, and rejections.

### 2.1 Order Eligibility And Liquidity

Each submitted order is placed in a pending queue:

```text
release_step = current_step + latency_steps
```

At each simulator step, only orders whose release step has arrived are eligible.
Eligible orders are processed in submission order. Per-symbol fill capacity is:

```text
available_quantity(symbol) = bar.volume(symbol) * participation_rate
```

The simulator fills:

```text
filled_quantity = min(requested_quantity, available_quantity)
```

Sells are further capped by current inventory unless `allow_short=True`. Buys
are capped by available cash after commission. Orders with zero executable
quantity are rejected. Orders that fill less than requested are recorded as
partial fills.

### 2.2 Price And Cost Equation

The simulator uses the bar close as the reference mid price. For market orders:

```text
half_spread_rate = spread_bps / 20000
participation = filled_quantity / max(1, bar.volume)
intrabar_vol = max(0, (high - low) / close)

slip_rate =
  half_spread_rate
  + base_slippage_bps / 10000
  + market_impact * participation
  + 0.1 * intrabar_vol

buy_fill_price  = close * (1 + slip_rate)
sell_fill_price = close * (1 - slip_rate)
commission      = traded_notional * commission_bps / 10000
```

Limit orders are rejected when the simulated market price does not cross the
limit. The execution report records submitted, eligible, filled, partial,
pending, and rejected orders, plus total commission, total slippage cost, and
average latency.

### 2.3 Default Parameters

The defaults are deliberately visible stress assumptions:

| Parameter | Default | Used by | Interpretation |
| --- | ---: | --- | --- |
| `commission_bps` | `1.0` | Simple and realistic simulators | Fee on traded notional |
| `base_slippage_bps` / `slippage_bps` | `2.0` | Realistic / simple simulator | Residual shortfall before spread, impact, and bar range |
| `spread_bps` | `0.0` | Realistic simulator | Full quoted spread; market orders cross half |
| `participation_rate` | `0.05` | Realistic simulator and risk budget | Max fillable fraction of each bar's volume |
| `latency_steps` | `1` | Realistic simulator | Bars an order waits before it can fill |
| `market_impact` | `0.15` | Realistic simulator | Linear coefficient on participation |
| `allow_short` | `False` | Simple and realistic simulators | Prevents sells beyond current holdings |

These values are not universal market constants. They exist so agents can be
compared under the same explicit frictions.

## 3. Execution Parameter Calibration

Execution calibration means replacing stress assumptions with parameters
estimated from a defined venue, broker, asset universe, and trading style. The
current repository includes diagnostics for what OHLCV bars can support, but
broker-grade transaction-cost calibration requires quote and fill data.

### 3.1 Calibration Inputs By Parameter

| Parameter | Preferred calibration evidence | Acceptable prototype evidence | Not identifiable from OHLCV alone |
| --- | --- | --- | --- |
| `commission_bps` | Broker/exchange fee schedule, account fee tier | User-supplied fee assumption | Yes |
| `spread_bps` | NBBO, quote snapshots, order-book top of book | User-supplied stress spread | Yes |
| `base_slippage_bps` | Real order/fill logs after removing spread and impact terms | Conservative stress setting | Yes |
| `participation_rate` | Parent-order policy, ADV participation target, broker execution policy | Scenario cap such as 1 percent, 5 percent, or 10 percent of bar volume | Partly policy-defined |
| `latency_steps` | Submission, acknowledgement, routing, and fill timestamps | Scenario delay in bars | Yes |
| `market_impact` | Regression of implementation shortfall on participation and volatility | Conservative stress coefficient | Yes |
| Intrabar volatility term | OHLCV bar high, low, close | Directly observable in bars | No |

OHLCV bars can support range and volume diagnostics. They cannot reveal quoted
spread, depth, queue priority, hidden liquidity, broker routing, or realized
shortfall for an actual order.

### 3.2 Suggested Calibration Procedure

For a broker or venue-specific study, use the following procedure:

1. Collect synchronized market data and order logs:
   quote snapshots, order submission time, acknowledgement time, fill time,
   side, quantity, fill price, fees, and parent-order identifier.
2. Compute reference prices:
   arrival mid, decision close, fill-time mid, and bar close.
3. Decompose implementation shortfall:

```text
shortfall_bps = side_adjusted((fill_price - reference_price) / reference_price) * 10000
spread_component_bps = side_adjusted(crossed_spread)
residual_bps = shortfall_bps - spread_component_bps
```

4. Estimate latency:
   map timestamp delay to the chosen bar frequency and set `latency_steps` to a
   conservative percentile, not only the mean.
5. Estimate participation caps:
   compare realized child-order quantity with bar volume and set
   `participation_rate` to the intended participation policy or a conservative
   historical percentile.
6. Fit impact:
   regress residual shortfall on participation and volatility. The current
   simulator uses a linear term, so a calibrated coefficient should be reported
   with its residual error. If the fitted relationship is nonlinear, document
   that the linear simulator is a stress approximation.
7. Record provenance:
   data range, assets, frequency, venue, broker, order type, sample size, and
   whether parameters are observed, externally supplied, or stress assumptions.

### 3.3 Built-In Diagnostic

Run:

```bash
python scripts/calibrate_execution_model.py \
  --data-dir data/real/yahoo_intraday_1h_50 \
  --output docs/results/execution_calibration_intraday_1h.json \
  --markdown-output docs/results/execution_calibration_intraday_1h.md
```

The report summarizes OHLCV-derived range and volume statistics, parameter
assumptions, and implied slippage components. If `spread_bps` is not supplied,
the diagnostic marks spread as unobserved rather than estimating it from bars.

## 4. Risk Gate Rules

The default risk manager is `MaxPositionRiskManager`. It has three phases:
pre-trade approval, in-trade monitoring, and post-trade attribution.

### 4.1 Default Risk Budget

| Risk budget field | Default | Rule type |
| --- | ---: | --- |
| `max_position_weight` / `max_abs_weight` | `0.35` | Pre-trade clipping |
| `min_confidence` | `0.05` | Pre-trade blocking |
| `max_gross_exposure` | `1.0` | Pre-trade portfolio rescaling |
| `max_single_step_turnover` | `0.75` | Pre-trade warning and violation record |
| `max_order_participation` | `0.05` | In-trade warning |
| `max_latency_steps` | `2` | In-trade warning |
| `max_slippage_bps` | `50.0` | In-trade warning |

`build_default_system` passes execution settings into the risk budget so the
in-trade monitor remains consistent with the selected participation, latency,
spread, and slippage stress settings.

### 4.2 Pre-Trade Approval

For every decision, the risk gate applies the following rules.

**Confidence floor.** If:

```text
decision.confidence < min_confidence
```

then the target weight is set to zero, the side becomes `HOLD`, metadata records
`risk_blocked="low_confidence"`, and an error-severity `min_confidence`
violation is written.

**Single-name position cap.** Each target is clipped to:

```text
target_weight_clipped =
  min(max(decision.target_weight, -max_abs_weight), max_abs_weight)
```

If clipping occurs, metadata records `risk_clipped_from`, `clipped_count`
increases, and a warning-severity `max_abs_weight` check is written.

**Projected turnover.** The gate computes:

```text
projected_turnover =
  sum(abs(approved_target_weight(symbol) - current_portfolio_weight(symbol)))
```

If projected turnover exceeds `max_single_step_turnover`, the decision set is
not blocked by default, but a warning-severity `max_single_step_turnover`
violation is recorded. This keeps the audit trail visible without silently
rewriting every high-turnover portfolio.

**Gross exposure cap.** After per-symbol clipping, the gate computes:

```text
gross_exposure = sum(abs(target_weight))
```

If gross exposure exceeds `max_gross_exposure`, all approved targets are scaled
by:

```text
scale = max_gross_exposure / gross_exposure
```

The scaled decisions retain their symbols and rationales, metadata records
`risk_scaled_by`, and a warning-severity `max_gross_exposure` check is written.

If none of the checks triggers, the report contains an informational
`all_constraints` check.

### 4.3 In-Trade Monitoring

After simulated execution, the risk monitor inspects each fill.

**Participation.**

```text
observed_participation = fill.quantity / max(1, bar.volume)
```

If this exceeds `max_order_participation`, a warning-severity
`max_order_participation` violation is written.

**Latency.**

```text
observed_latency = fill.latency_steps
```

If this exceeds `max_latency_steps`, a warning-severity `max_latency_steps`
violation is written.

**Slippage.**

```text
observed_slippage_bps =
  abs(fill.slippage) / current_price(symbol) * 10000
```

If this exceeds `max_slippage_bps`, a warning-severity `max_slippage_bps`
violation is written.

When no in-trade violations occur, the monitor writes an informational
`in_trade_monitor` check.

### 4.4 Post-Trade Attribution

The risk manager then records:

```text
realized_pnl
sum(fill.commission)
sum(abs(fill.slippage) * fill.quantity)
portfolio_weight(symbol) for each observed symbol
```

This phase does not rewrite orders. It explains how the realized paper outcome
was affected by simulated fills, fees, slippage, and final exposure.

### 4.5 Severity Semantics

Risk checks use two practical severity levels:

- `error`: a hard block that makes `RiskReport.passed` false;
- `warning`: an audit-visible intervention or budget breach that is recorded
  but may still allow the run to continue.

The default confidence floor is the main pre-trade hard block. Position caps,
gross exposure scaling, turnover excess, participation excess, latency excess,
and slippage excess are recorded as warnings so downstream experiments can
measure how often the risk layer corrected or flagged model intent.

`NoRiskManager` is included only as an ablation. It writes disabled risk reports
and should not be interpreted as a safe trading configuration.

## 5. Audit Artifacts

The runner serializes decisions, risk reports, execution reports, fills, memory
events, and metrics. A valid technical result should state:

- model or deterministic analyst path;
- data source and timestamp policy;
- execution simulator and parameter provenance;
- risk budget and whether risk feedback was visible to the analyst;
- cache or redacted manifest policy for LLM runs;
- random seeds or rolling-window definition;
- whether live provider calls were made.

## 6. Limitations

The current public defaults are useful for controlled comparisons, not for live
broker execution claims. In particular:

- OHLCV bars cannot calibrate spread, queue depth, or realized shortfall;
- the market-impact model is linear and intentionally simple;
- risk warnings are audit records, not a regulatory risk system;
- LLM provider outputs may depend on model version, routing, prompt wrappers,
  and cache state;
- paper broker exports do not prove suitability for live trading.

Future work should separate broker-specific calibration files, add quote/fill
log ingestion, and report confidence intervals for calibrated execution
parameters.
