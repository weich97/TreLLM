from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from statistics import fmean

from tradearena.core.domain import Order, OrderType, Side


class BrokerAdapterMode(str, Enum):
    """Runtime broker adapter mode."""

    OFFLINE_EXPORT = "offline_export"
    DRY_RUN = "dry_run"
    PAPER_SANDBOX = "paper_sandbox"
    LIVE_HUMAN_APPROVED = "live_human_approved"


class BrokerAdapterContractError(ValueError):
    """Raised when a broker handoff would violate the adapter contract."""


class BrokerOrderStatus(str, Enum):
    """Normalized broker response status."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BrokerApproval:
    """Human approval record required before live broker submission."""

    approval_status: str
    approved_by: str
    approved_at: str
    max_notional: float
    allowed_symbols: tuple[str, ...]
    approval_reason: str

    @property
    def is_approved(self) -> bool:
        return self.approval_status == "approved" and bool(self.approved_by) and bool(self.approved_at)


@dataclass(frozen=True)
class BrokerSafetyConfig:
    """Safety limits enforced before any broker handoff artifact is written."""

    mode: BrokerAdapterMode = BrokerAdapterMode.OFFLINE_EXPORT
    account_mode: str = "none"
    max_notional: float | None = None
    max_quantity: float | None = None
    allowed_symbols: tuple[str, ...] = field(default_factory=tuple)
    allowed_order_types: tuple[OrderType, ...] = field(default_factory=lambda: (OrderType.MARKET, OrderType.LIMIT))
    kill_switch: bool = False
    approval: BrokerApproval | None = None

    def validate_order(self, order: Order, *, reference_price: float | None = None) -> None:
        """Validate one order before export, dry run, sandbox, or live handoff."""

        if self.kill_switch:
            raise BrokerAdapterContractError("broker adapter kill switch is enabled")
        if self.allowed_symbols and order.symbol not in self.allowed_symbols:
            raise BrokerAdapterContractError(f"symbol {order.symbol} is not in the broker adapter allow-list")
        if order.order_type not in self.allowed_order_types:
            raise BrokerAdapterContractError(f"order type {order.order_type.value} is not allowed")
        if self.max_quantity is not None and float(order.quantity) > self.max_quantity:
            raise BrokerAdapterContractError(f"quantity {order.quantity} exceeds max_quantity {self.max_quantity}")
        if self.max_notional is not None and reference_price is not None:
            notional = abs(float(order.quantity) * float(reference_price))
            if notional > self.max_notional:
                raise BrokerAdapterContractError(
                    f"order notional {notional:.2f} exceeds max_notional {self.max_notional:.2f}"
                )
        if self.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED:
            self._validate_live_approval(order)

    def submit_live_flag(self) -> bool:
        return self.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED

    def _validate_live_approval(self, order: Order) -> None:
        if self.max_notional is None or self.max_quantity is None:
            raise BrokerAdapterContractError("live_human_approved mode requires max_notional and max_quantity limits")
        if self.approval is None or not self.approval.is_approved:
            raise BrokerAdapterContractError("live_human_approved mode requires an approved human approval record")
        if self.approval.allowed_symbols and order.symbol not in self.approval.allowed_symbols:
            raise BrokerAdapterContractError(f"symbol {order.symbol} is outside the human approval scope")
        if self.approval.max_notional <= 0:
            raise BrokerAdapterContractError("live_human_approved mode requires a positive approval max_notional")


@dataclass(frozen=True)
class AlpacaPaperOrder:
    """Neutral export-only order row for Alpaca review workflows."""

    client_order_id: str
    adapter_mode: str
    account_mode: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    time_in_force: str
    limit_price: float | None
    submit_live: bool
    approval_status: str
    max_notional: float | None
    reason: str


@dataclass(frozen=True)
class BrokerResponse:
    """Redacted broker response row used for reconciliation artifacts."""

    client_order_id: str
    status: BrokerOrderStatus
    broker_order_id: str | None = None
    submitted_quantity: float | None = None
    accepted_quantity: float | None = None
    fill_quantity: float | None = None
    fill_price: float | None = None
    fees: float | None = None
    rejection_reason: str | None = None
    submitted_at: str | None = None
    broker_timestamp: str | None = None
    account_mode: str = "unknown"


@dataclass(frozen=True)
class BrokerReconciliationSummary:
    """Aggregate reconciliation status for broker response artifacts."""

    response_count: int
    accepted_count: int
    rejected_count: int
    partial_fill_count: int
    filled_count: int
    canceled_count: int
    expired_count: int
    unknown_count: int
    unmatched_response_count: int
    missing_response_count: int
    fill_ratio_mean: float | None


class AlpacaPaperExportAdapter:
    """Convert approved TradeArena orders into broker-review files.

    The adapter deliberately does not call Alpaca or any broker API. It creates
    a neutral JSON/CSV handoff for human review before any external system sees
    the order instructions.
    """

    name = "alpaca-paper-export-adapter"

    def __init__(
        self,
        *,
        time_in_force: str = "day",
        client_prefix: str = "ta-paper",
        safety: BrokerSafetyConfig | None = None,
    ) -> None:
        self.time_in_force = time_in_force
        self.client_prefix = client_prefix
        self.safety = safety or BrokerSafetyConfig()

    def convert(self, orders: list[Order] | tuple[Order, ...]) -> list[AlpacaPaperOrder]:
        rows: list[AlpacaPaperOrder] = []
        for idx, order in enumerate(orders, start=1):
            if order.side == Side.HOLD or order.quantity <= 0:
                continue
            self.safety.validate_order(order, reference_price=order.limit_price)
            rows.append(
                AlpacaPaperOrder(
                    client_order_id=f"{self.client_prefix}-{idx:04d}-{_safe_symbol(order.symbol)}",
                    adapter_mode=self.safety.mode.value,
                    account_mode=self.safety.account_mode,
                    symbol=order.symbol,
                    side=order.side.value,
                    order_type=_alpaca_order_type(order.order_type),
                    quantity=round(float(order.quantity), 8),
                    time_in_force=self.time_in_force,
                    limit_price=order.limit_price,
                    submit_live=self.safety.submit_live_flag(),
                    approval_status=_approval_status(self.safety),
                    max_notional=self.safety.max_notional,
                    reason=order.reason,
                )
            )
        return rows

    def write(self, orders: list[Order] | tuple[Order, ...], output_dir: str | Path) -> dict[str, str | int | bool]:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        rows = self.convert(orders)
        json_path = path / "alpaca_paper_orders.json"
        csv_path = path / "alpaca_paper_orders.csv"
        payload = {
            "adapter": self.name,
            "adapter_mode": self.safety.mode.value,
            "account_mode": self.safety.account_mode,
            "paper_only": self.safety.mode in (BrokerAdapterMode.OFFLINE_EXPORT, BrokerAdapterMode.DRY_RUN),
            "live_submission": self.safety.submit_live_flag(),
            "manual_approval_required": self.safety.mode != BrokerAdapterMode.LIVE_HUMAN_APPROVED,
            "kill_switch": self.safety.kill_switch,
            "orders": [asdict(row) for row in rows],
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = list(asdict(rows[0]).keys()) if rows else list(AlpacaPaperOrder.__dataclass_fields__)
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(asdict(row) for row in rows)
        return {
            "json": str(json_path),
            "csv": str(csv_path),
            "order_count": len(rows),
            "adapter_mode": self.safety.mode.value,
            "account_mode": self.safety.account_mode,
            "paper_only": self.safety.mode in (BrokerAdapterMode.OFFLINE_EXPORT, BrokerAdapterMode.DRY_RUN),
            "manual_approval_required": self.safety.mode != BrokerAdapterMode.LIVE_HUMAN_APPROVED,
        }


def reconcile_broker_responses(
    requests: list[AlpacaPaperOrder] | tuple[AlpacaPaperOrder, ...],
    responses: list[BrokerResponse] | tuple[BrokerResponse, ...],
) -> BrokerReconciliationSummary:
    request_ids = {request.client_order_id for request in requests}
    response_ids = {response.client_order_id for response in responses}
    status_counts = {status: 0 for status in BrokerOrderStatus}
    fill_ratios: list[float] = []
    for response in responses:
        status_counts[response.status] += 1
        if response.submitted_quantity and response.fill_quantity is not None and response.submitted_quantity > 0:
            fill_ratios.append(float(response.fill_quantity) / float(response.submitted_quantity))
    return BrokerReconciliationSummary(
        response_count=len(responses),
        accepted_count=status_counts[BrokerOrderStatus.ACCEPTED],
        rejected_count=status_counts[BrokerOrderStatus.REJECTED],
        partial_fill_count=status_counts[BrokerOrderStatus.PARTIALLY_FILLED],
        filled_count=status_counts[BrokerOrderStatus.FILLED],
        canceled_count=status_counts[BrokerOrderStatus.CANCELED],
        expired_count=status_counts[BrokerOrderStatus.EXPIRED],
        unknown_count=status_counts[BrokerOrderStatus.UNKNOWN],
        unmatched_response_count=len(response_ids - request_ids),
        missing_response_count=len(request_ids - response_ids),
        fill_ratio_mean=round(fmean(fill_ratios), 8) if fill_ratios else None,
    )


def write_broker_response_artifact(
    *,
    requests: list[AlpacaPaperOrder] | tuple[AlpacaPaperOrder, ...],
    responses: list[BrokerResponse] | tuple[BrokerResponse, ...],
    output: str | Path,
    adapter: str,
    adapter_mode: BrokerAdapterMode,
    account_mode: str,
) -> dict[str, str | int | bool]:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = reconcile_broker_responses(requests, responses)
    payload = {
        "schema": "tradearena_broker_response_artifact_v0.1",
        "adapter": adapter,
        "adapter_mode": adapter_mode.value,
        "account_mode": account_mode,
        "live_submission": adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED,
        "reconciliation": asdict(summary),
        "responses": [_response_dict(response) for response in responses],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "path": str(path),
        "response_count": summary.response_count,
        "unmatched_response_count": summary.unmatched_response_count,
        "missing_response_count": summary.missing_response_count,
        "live_submission": payload["live_submission"],
    }


def validate_broker_response_artifact(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema",
        "adapter",
        "adapter_mode",
        "account_mode",
        "live_submission",
        "reconciliation",
        "responses",
    }
    missing = sorted(required - set(payload))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    extra = sorted(set(payload) - required)
    if extra:
        errors.append(f"unexpected fields: {', '.join(extra)}")
    if payload.get("schema") != "tradearena_broker_response_artifact_v0.1":
        errors.append("schema must be 'tradearena_broker_response_artifact_v0.1'")
    if not payload.get("adapter"):
        errors.append("adapter must be non-empty")
    adapter_mode = payload.get("adapter_mode")
    if adapter_mode not in {mode.value for mode in BrokerAdapterMode}:
        errors.append("adapter_mode must be one of offline_export, dry_run, paper_sandbox, live_human_approved")
    if not payload.get("account_mode"):
        errors.append("account_mode must be non-empty")
    if payload.get("live_submission") is not (adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED.value):
        errors.append("live_submission must match adapter_mode == live_human_approved")

    responses = payload.get("responses")
    if not isinstance(responses, list):
        errors.append("responses must be a list")
        responses = []
    reconciliation = payload.get("reconciliation")
    if not isinstance(reconciliation, dict):
        errors.append("reconciliation must be an object")
        reconciliation = {}

    status_counts = {status.value: 0 for status in BrokerOrderStatus}
    for idx, response in enumerate(responses):
        if not isinstance(response, dict):
            errors.append(f"responses[{idx}] must be an object")
            continue
        response_errors = _validate_broker_response_row(response, idx)
        errors.extend(response_errors)
        status = response.get("status")
        if isinstance(status, str) and status in status_counts:
            status_counts[status] += 1

    errors.extend(_validate_reconciliation(reconciliation, len(responses), status_counts))
    return errors


def validate_broker_response_artifact_file(path: str | Path) -> tuple[dict[str, object], list[str]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}, ["broker response artifact must be a JSON object"]
    return payload, validate_broker_response_artifact(payload)


def _alpaca_order_type(order_type: OrderType) -> str:
    return "limit" if order_type == OrderType.LIMIT else "market"


def _safe_symbol(symbol: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in symbol).strip("-")


def _approval_status(safety: BrokerSafetyConfig) -> str:
    if safety.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED:
        return "approved"
    return "requires_human_approval"


def _response_dict(response: BrokerResponse) -> dict[str, object]:
    row = asdict(response)
    row["status"] = response.status.value
    return row


def _validate_broker_response_row(response: dict[str, object], idx: int) -> list[str]:
    errors: list[str] = []
    required = {
        "client_order_id",
        "status",
        "broker_order_id",
        "submitted_quantity",
        "accepted_quantity",
        "fill_quantity",
        "fill_price",
        "fees",
        "rejection_reason",
        "submitted_at",
        "broker_timestamp",
        "account_mode",
    }
    missing = sorted(required - set(response))
    if missing:
        errors.append(f"responses[{idx}] missing required fields: {', '.join(missing)}")
    extra = sorted(set(response) - required)
    if extra:
        errors.append(f"responses[{idx}] has unexpected fields: {', '.join(extra)}")
    if not response.get("client_order_id"):
        errors.append(f"responses[{idx}].client_order_id must be non-empty")
    if response.get("status") not in {status.value for status in BrokerOrderStatus}:
        errors.append(f"responses[{idx}].status is not a supported broker order status")
    if not response.get("account_mode"):
        errors.append(f"responses[{idx}].account_mode must be non-empty")
    for field_name in ("submitted_quantity", "accepted_quantity", "fill_quantity", "fill_price", "fees"):
        value = response.get(field_name)
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            errors.append(f"responses[{idx}].{field_name} must be a non-negative number or null")
    return errors


def _validate_reconciliation(
    reconciliation: dict[str, object],
    response_count: int,
    status_counts: dict[str, int],
) -> list[str]:
    errors: list[str] = []
    count_fields = {
        "response_count": response_count,
        "accepted_count": status_counts[BrokerOrderStatus.ACCEPTED.value],
        "rejected_count": status_counts[BrokerOrderStatus.REJECTED.value],
        "partial_fill_count": status_counts[BrokerOrderStatus.PARTIALLY_FILLED.value],
        "filled_count": status_counts[BrokerOrderStatus.FILLED.value],
        "canceled_count": status_counts[BrokerOrderStatus.CANCELED.value],
        "expired_count": status_counts[BrokerOrderStatus.EXPIRED.value],
        "unknown_count": status_counts[BrokerOrderStatus.UNKNOWN.value],
    }
    required = set(count_fields) | {"unmatched_response_count", "missing_response_count", "fill_ratio_mean"}
    missing = sorted(required - set(reconciliation))
    if missing:
        errors.append(f"reconciliation missing required fields: {', '.join(missing)}")
    extra = sorted(set(reconciliation) - required)
    if extra:
        errors.append(f"reconciliation has unexpected fields: {', '.join(extra)}")
    for field_name, expected in count_fields.items():
        actual = reconciliation.get(field_name)
        if actual != expected:
            errors.append(f"reconciliation.{field_name} must be {expected}; got {actual}")
    for field_name in ("unmatched_response_count", "missing_response_count"):
        value = reconciliation.get(field_name)
        if not isinstance(value, int) or value < 0:
            errors.append(f"reconciliation.{field_name} must be a non-negative integer")
    fill_ratio = reconciliation.get("fill_ratio_mean")
    if fill_ratio is not None and (not isinstance(fill_ratio, (int, float)) or fill_ratio < 0):
        errors.append("reconciliation.fill_ratio_mean must be a non-negative number or null")
    return errors
