from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from statistics import fmean
from typing import Protocol, cast, runtime_checkable

from tradearena.core.domain import Order, OrderType, Side

_SHA256_ARTIFACT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ISO_TIMESTAMP_WITH_TZ_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


class BrokerAdapterMode(str, Enum):
    """Runtime broker adapter mode."""

    OFFLINE_EXPORT = "offline_export"
    DRY_RUN = "dry_run"
    PAPER_SANDBOX = "paper_sandbox"
    LIVE_HUMAN_APPROVED = "live_human_approved"


class BrokerAdapterContractError(ValueError):
    """Raised when a broker handoff would violate the adapter contract."""


@runtime_checkable
class BrokerAdapter(Protocol):
    """Minimal broker adapter surface for export, dry-run, sandbox, or live modes."""

    name: str
    safety: BrokerSafetyConfig

    def convert(self, orders: list[Order] | tuple[Order, ...]) -> list[AlpacaPaperOrder]:
        """Convert TradeArena orders into broker handoff rows."""

    def write(self, orders: list[Order] | tuple[Order, ...], output_dir: str | Path) -> dict[str, str | int | bool]:
        """Write a broker handoff artifact and return a small summary."""


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
    approved_order_fingerprints: tuple[str, ...] = field(default_factory=tuple)
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
        if self.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED:
            self._validate_live_approval(order)

        notional = None
        if self.max_notional is not None:
            if reference_price is None and self.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED:
                raise BrokerAdapterContractError(
                    "live_human_approved mode requires a reference_price for max_notional checks"
                )
            if reference_price is not None:
                notional = abs(float(order.quantity) * float(reference_price))
        if self.max_notional is not None and notional is not None:
            if notional > self.max_notional:
                raise BrokerAdapterContractError(
                    f"order notional {notional:.2f} exceeds max_notional {self.max_notional:.2f}"
                )
        if self.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED:
            if notional is not None and self.approval is not None and notional > self.approval.max_notional:
                raise BrokerAdapterContractError(
                    f"order notional {notional:.2f} exceeds approval max_notional {self.approval.max_notional:.2f}"
                )

    def submit_live_flag(self) -> bool:
        return self.mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED

    def _validate_live_approval(self, order: Order) -> None:
        if self.max_notional is None or self.max_quantity is None:
            raise BrokerAdapterContractError("live_human_approved mode requires max_notional and max_quantity limits")
        if self.approval is None or not self.approval.is_approved:
            raise BrokerAdapterContractError("live_human_approved mode requires an approved human approval record")
        if self.account_mode != "live":
            raise BrokerAdapterContractError("live_human_approved mode requires account_mode live")
        if self.approved_order_fingerprints and _order_fingerprint_from_order(order) not in set(
            self.approved_order_fingerprints
        ):
            raise BrokerAdapterContractError("order does not match an approved broker handoff order")
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
            "schema": "tradearena_broker_handoff_artifact_v0.1",
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


class DryRunBrokerAdapter:
    """Validate broker handoff rows locally without submitting to any broker API."""

    name = "dry-run-broker-adapter"

    def __init__(
        self,
        *,
        time_in_force: str = "day",
        client_prefix: str = "ta-dry-run",
        safety: BrokerSafetyConfig | None = None,
    ) -> None:
        self.time_in_force = time_in_force
        self.client_prefix = client_prefix
        self.safety = _dry_run_safety(safety)

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
                    submit_live=False,
                    approval_status="requires_human_approval",
                    max_notional=self.safety.max_notional,
                    reason=order.reason,
                )
            )
        return rows

    def write(self, orders: list[Order] | tuple[Order, ...], output_dir: str | Path) -> dict[str, str | int | bool]:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        rows = self.convert(orders)
        json_path = path / "dry_run_orders.json"
        csv_path = path / "dry_run_orders.csv"
        payload = {
            "schema": "tradearena_broker_handoff_artifact_v0.1",
            "adapter": self.name,
            "adapter_mode": self.safety.mode.value,
            "account_mode": self.safety.account_mode,
            "paper_only": True,
            "live_submission": False,
            "manual_approval_required": True,
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
            "paper_only": True,
            "manual_approval_required": True,
        }


def reconcile_broker_responses(
    requests: list[AlpacaPaperOrder] | tuple[AlpacaPaperOrder, ...],
    responses: list[BrokerResponse] | tuple[BrokerResponse, ...],
) -> BrokerReconciliationSummary:
    request_ids = {request.client_order_id for request in requests}
    response_ids = {response.client_order_id for response in responses}
    status_counts = dict.fromkeys(BrokerOrderStatus, 0)
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
    live_submission = adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED
    payload: dict[str, object] = {
        "schema": "tradearena_broker_response_artifact_v0.1",
        "adapter": adapter,
        "adapter_mode": adapter_mode.value,
        "account_mode": account_mode,
        "live_submission": live_submission,
        "reconciliation": asdict(summary),
        "responses": [_response_dict(response) for response in responses],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "path": str(path),
        "response_count": summary.response_count,
        "unmatched_response_count": summary.unmatched_response_count,
        "missing_response_count": summary.missing_response_count,
        "live_submission": live_submission,
    }


def build_broker_approval_artifact(
    approval: BrokerApproval,
    *,
    approval_id: str,
    account_mode: str,
    max_quantity: float,
    allowed_order_types: tuple[OrderType, ...] = (OrderType.MARKET, OrderType.LIMIT),
    expires_at: str | None = None,
    request_artifact_hash: str | None = None,
) -> dict[str, object]:
    """Build a redacted human approval artifact for future live handoff review."""

    return {
        "schema": "tradearena_broker_approval_artifact_v0.1",
        "approval_id": approval_id,
        "approval_status": approval.approval_status,
        "approved_by": approval.approved_by,
        "approved_at": approval.approved_at,
        "expires_at": expires_at,
        "account_mode": account_mode,
        "max_notional": approval.max_notional,
        "max_quantity": max_quantity,
        "allowed_symbols": list(approval.allowed_symbols),
        "allowed_order_types": [order_type.value for order_type in allowed_order_types],
        "approval_reason": approval.approval_reason,
        "request_artifact_hash": request_artifact_hash,
    }


def validate_broker_approval_artifact(
    payload: dict[str, object],
    *,
    now: str | datetime | None = None,
) -> list[str]:
    errors: list[str] = []
    now_dt = _parse_timestamp(now) if now is not None else None
    if now is not None and now_dt is None:
        errors.append("now must be an ISO timestamp")
    required = {
        "schema",
        "approval_id",
        "approval_status",
        "approved_by",
        "approved_at",
        "expires_at",
        "account_mode",
        "max_notional",
        "max_quantity",
        "allowed_symbols",
        "allowed_order_types",
        "approval_reason",
        "request_artifact_hash",
    }
    missing = sorted(required - set(payload))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    extra = sorted(set(payload) - required)
    if extra:
        errors.append(f"unexpected fields: {', '.join(extra)}")
    if payload.get("schema") != "tradearena_broker_approval_artifact_v0.1":
        errors.append("schema must be 'tradearena_broker_approval_artifact_v0.1'")
    if not payload.get("approval_id"):
        errors.append("approval_id must be non-empty")
    if payload.get("approval_status") != "approved":
        errors.append("approval_status must be approved")
    approved_by = payload.get("approved_by")
    if not isinstance(approved_by, str) or not approved_by:
        errors.append("approved_by must be non-empty")
    elif "@" in approved_by:
        errors.append("approved_by must be a redacted operator id, not an email address")
    approved_at = payload.get("approved_at")
    approved_dt: datetime | None = None
    if not approved_at:
        errors.append("approved_at must be non-empty")
    elif not isinstance(approved_at, str) or not _is_iso_timestamp_with_timezone(approved_at):
        errors.append("approved_at must be an ISO timestamp with timezone")
    else:
        approved_dt = _parse_timestamp(approved_at)
    if payload.get("account_mode") != "live":
        errors.append("account_mode must be live for broker approval artifacts")
    for field_name in ("max_notional", "max_quantity"):
        value = payload.get(field_name)
        if not isinstance(value, (int, float)) or value <= 0:
            errors.append(f"{field_name} must be a positive number")
    allowed_symbols = payload.get("allowed_symbols")
    if (
        not isinstance(allowed_symbols, list)
        or not allowed_symbols
        or not all(isinstance(item, str) and item for item in allowed_symbols)
    ):
        errors.append("allowed_symbols must be a non-empty list of symbols")
    allowed_order_types = payload.get("allowed_order_types")
    supported_types = {OrderType.MARKET.value, OrderType.LIMIT.value}
    if (
        not isinstance(allowed_order_types, list)
        or not allowed_order_types
        or any(item not in supported_types for item in allowed_order_types)
    ):
        errors.append("allowed_order_types must contain market or limit")
    if not payload.get("approval_reason"):
        errors.append("approval_reason must be non-empty")
    request_hash = payload.get("request_artifact_hash")
    if request_hash is not None and not isinstance(request_hash, str):
        errors.append("request_artifact_hash must be a string or null")
    elif isinstance(request_hash, str) and not _SHA256_ARTIFACT_HASH_RE.fullmatch(request_hash):
        errors.append("request_artifact_hash must be sha256:<64 lowercase hex chars> or null")
    expires_at = payload.get("expires_at")
    if expires_at is not None and not isinstance(expires_at, str):
        errors.append("expires_at must be a string or null")
    elif expires_at and not _is_iso_timestamp_with_timezone(expires_at):
        errors.append("expires_at must be an ISO timestamp with timezone or null")
    elif expires_at:
        expires_dt = _parse_timestamp(expires_at)
        if approved_dt is not None and expires_dt is not None and expires_dt <= approved_dt:
            errors.append("expires_at must be after approved_at")
        if now is not None and now_dt is not None:
            if expires_dt is None:
                errors.append("expires_at must be an ISO timestamp or null")
            elif expires_dt <= now_dt:
                errors.append("approval artifact is expired")
    return errors


def validate_broker_approval_artifact_file(
    path: str | Path,
    *,
    now: str | datetime | None = None,
) -> tuple[dict[str, object], list[str]]:
    payload, errors = _read_broker_artifact_json_file(path)
    if errors:
        return {}, errors
    if not isinstance(payload, dict):
        return {}, ["broker approval artifact must be a JSON object"]
    return payload, validate_broker_approval_artifact(payload, now=now)


def broker_handoff_artifact_hash(payload_or_path: dict[str, object] | str | Path) -> str:
    """Return a stable SHA-256 hash for a valid broker handoff artifact."""

    payload = _load_broker_artifact_payload(payload_or_path)
    errors = validate_broker_handoff_artifact(payload)
    if errors:
        raise BrokerAdapterContractError("; ".join(errors))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_broker_approval_request_binding(
    approval_payload: dict[str, object],
    request_payload_or_path: dict[str, object] | str | Path,
    *,
    now: str | datetime | None = None,
) -> list[str]:
    """Validate that an approval artifact names the exact broker handoff artifact."""

    errors = validate_broker_approval_artifact(approval_payload, now=now)
    try:
        request_payload = _load_broker_artifact_payload(request_payload_or_path)
    except BrokerAdapterContractError as exc:
        return [*errors, str(exc)]
    request_errors = validate_broker_handoff_artifact(request_payload)
    errors.extend(request_errors)
    request_hash = approval_payload.get("request_artifact_hash")
    if not isinstance(request_hash, str) or not request_hash:
        errors.append("request_artifact_hash is required to bind approval to a broker handoff artifact")
    elif not request_errors and request_hash != broker_handoff_artifact_hash(request_payload):
        errors.append("request_artifact_hash does not match broker handoff artifact")
    if not errors:
        errors.extend(_validate_approval_request_scope(approval_payload, request_payload))
    return errors


def broker_approval_from_artifact(
    payload: dict[str, object],
    *,
    now: str | datetime | None = None,
    request_artifact: dict[str, object] | str | Path | None = None,
) -> BrokerApproval:
    """Convert a schema-valid broker approval artifact into a BrokerApproval."""

    errors = validate_broker_approval_artifact(payload, now=now)
    if request_artifact is not None:
        errors.extend(validate_broker_approval_request_binding(payload, request_artifact))
    if errors:
        raise BrokerAdapterContractError("; ".join(errors))
    return BrokerApproval(
        approval_status=str(payload["approval_status"]),
        approved_by=str(payload["approved_by"]),
        approved_at=str(payload["approved_at"]),
        max_notional=float(cast(str | int | float, payload["max_notional"])),
        allowed_symbols=tuple(
            str(symbol) for symbol in cast(list[object] | tuple[object, ...], payload["allowed_symbols"])
        ),
        approval_reason=str(payload["approval_reason"]),
    )


def broker_safety_from_approval_artifact(
    payload: dict[str, object],
    *,
    now: str | datetime | None = None,
    request_artifact: dict[str, object] | str | Path | None = None,
) -> BrokerSafetyConfig:
    """Build live human-approved safety limits from a broker approval artifact."""

    approval = broker_approval_from_artifact(payload, now=now, request_artifact=request_artifact)
    order_types = tuple(
        OrderType(str(order_type))
        for order_type in cast(list[object] | tuple[object, ...], payload["allowed_order_types"])
    )
    approved_order_fingerprints = (
        _approved_order_fingerprints_from_request(request_artifact) if request_artifact is not None else ()
    )
    return BrokerSafetyConfig(
        mode=BrokerAdapterMode.LIVE_HUMAN_APPROVED,
        account_mode=str(payload["account_mode"]),
        max_notional=float(cast(str | int | float, payload["max_notional"])),
        max_quantity=float(cast(str | int | float, payload["max_quantity"])),
        allowed_symbols=tuple(approval.allowed_symbols),
        allowed_order_types=order_types,
        approved_order_fingerprints=approved_order_fingerprints,
        approval=approval,
    )


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
    if adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED.value and payload.get("account_mode") != "live":
        errors.append("account_mode must be live for live_human_approved broker response artifacts")

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
    payload, errors = _read_broker_artifact_json_file(path)
    if errors:
        return {}, errors
    if not isinstance(payload, dict):
        return {}, ["broker response artifact must be a JSON object"]
    return payload, validate_broker_response_artifact(payload)


def validate_broker_handoff_artifact(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema",
        "adapter",
        "adapter_mode",
        "account_mode",
        "paper_only",
        "live_submission",
        "manual_approval_required",
        "kill_switch",
        "orders",
    }
    missing = sorted(required - set(payload))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    extra = sorted(set(payload) - required)
    if extra:
        errors.append(f"unexpected fields: {', '.join(extra)}")
    if payload.get("schema") != "tradearena_broker_handoff_artifact_v0.1":
        errors.append("schema must be 'tradearena_broker_handoff_artifact_v0.1'")
    if not payload.get("adapter"):
        errors.append("adapter must be non-empty")
    adapter_mode = payload.get("adapter_mode")
    if adapter_mode not in {mode.value for mode in BrokerAdapterMode}:
        errors.append("adapter_mode must be one of offline_export, dry_run, paper_sandbox, live_human_approved")
    if not payload.get("account_mode"):
        errors.append("account_mode must be non-empty")
    if adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED.value and payload.get("account_mode") != "live":
        errors.append("account_mode must be live for live_human_approved broker handoff artifacts")
    paper_only_modes = {BrokerAdapterMode.OFFLINE_EXPORT.value, BrokerAdapterMode.DRY_RUN.value}
    if payload.get("paper_only") is not (adapter_mode in paper_only_modes):
        errors.append("paper_only must match adapter_mode in offline_export or dry_run")
    if payload.get("live_submission") is not (adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED.value):
        errors.append("live_submission must match adapter_mode == live_human_approved")
    if payload.get("manual_approval_required") is not (adapter_mode != BrokerAdapterMode.LIVE_HUMAN_APPROVED.value):
        errors.append("manual_approval_required must be false only for live_human_approved mode")
    if not isinstance(payload.get("kill_switch"), bool):
        errors.append("kill_switch must be boolean")

    orders = payload.get("orders")
    if not isinstance(orders, list):
        errors.append("orders must be a list")
        orders = []
    for idx, order in enumerate(orders):
        if not isinstance(order, dict):
            errors.append(f"orders[{idx}] must be an object")
            continue
        errors.extend(_validate_broker_handoff_order(order, idx, adapter_mode))
    return errors


def validate_broker_handoff_artifact_file(path: str | Path) -> tuple[dict[str, object], list[str]]:
    payload, errors = _read_broker_artifact_json_file(path)
    if errors:
        return {}, errors
    if not isinstance(payload, dict):
        return {}, ["broker handoff artifact must be a JSON object"]
    return payload, validate_broker_handoff_artifact(payload)


def _read_broker_artifact_json_file(path: str | Path) -> tuple[object, list[str]]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), []
    except json.JSONDecodeError:
        return {}, ["broker artifact file must contain valid JSON"]


def _load_broker_artifact_payload(payload_or_path: dict[str, object] | str | Path) -> dict[str, object]:
    if isinstance(payload_or_path, dict):
        return payload_or_path
    payload, errors = _read_broker_artifact_json_file(payload_or_path)
    if errors:
        raise BrokerAdapterContractError("; ".join(errors))
    if not isinstance(payload, dict):
        raise BrokerAdapterContractError("broker artifact must be a JSON object")
    return payload


def _validate_approval_request_scope(
    approval_payload: dict[str, object],
    request_payload: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    allowed_symbols = {
        str(symbol) for symbol in cast(list[object] | tuple[object, ...], approval_payload["allowed_symbols"])
    }
    allowed_order_types = {
        str(order_type) for order_type in cast(list[object] | tuple[object, ...], approval_payload["allowed_order_types"])
    }
    max_quantity = float(cast(str | int | float, approval_payload["max_quantity"]))
    max_notional = float(cast(str | int | float, approval_payload["max_notional"]))
    orders = cast(list[object] | tuple[object, ...], request_payload["orders"])
    for idx, order in enumerate(orders):
        if not isinstance(order, dict):
            continue
        symbol = str(order.get("symbol"))
        order_type = str(order.get("order_type"))
        quantity = float(order.get("quantity", 0.0))
        if symbol not in allowed_symbols:
            errors.append(f"orders[{idx}].symbol {symbol} is outside approval allowed_symbols")
        if order_type not in allowed_order_types:
            errors.append(f"orders[{idx}].order_type {order_type} is outside approval allowed_order_types")
        if quantity > max_quantity:
            errors.append(f"orders[{idx}].quantity {quantity} exceeds approval max_quantity {max_quantity}")
        limit_price = order.get("limit_price")
        if not isinstance(limit_price, (int, float)) or limit_price <= 0:
            errors.append(f"orders[{idx}].notional cannot be checked without a positive limit_price")
            continue
        notional = abs(quantity * float(limit_price))
        if notional > max_notional:
            errors.append(f"orders[{idx}].notional {notional:.2f} exceeds approval max_notional {max_notional:.2f}")
    return errors


def _approved_order_fingerprints_from_request(payload_or_path: dict[str, object] | str | Path) -> tuple[str, ...]:
    request_payload = _load_broker_artifact_payload(payload_or_path)
    errors = validate_broker_handoff_artifact(request_payload)
    if errors:
        raise BrokerAdapterContractError("; ".join(errors))
    orders = cast(list[object] | tuple[object, ...], request_payload["orders"])
    fingerprints = []
    for order in orders:
        if isinstance(order, dict):
            fingerprints.append(_order_fingerprint_from_handoff(order))
    return tuple(fingerprints)


def _order_fingerprint_from_order(order: Order) -> str:
    return _order_fingerprint(
        symbol=order.symbol,
        side=order.side.value,
        order_type=_alpaca_order_type(order.order_type),
        quantity=order.quantity,
        limit_price=order.limit_price,
    )


def _order_fingerprint_from_handoff(order: dict[object, object]) -> str:
    return _order_fingerprint(
        symbol=str(order.get("symbol")),
        side=str(order.get("side")),
        order_type=str(order.get("order_type")),
        quantity=float(cast(str | int | float, order.get("quantity", 0.0))),
        limit_price=cast(float | None, order.get("limit_price")),
    )


def _order_fingerprint(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    limit_price: float | None,
) -> str:
    payload = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": round(float(quantity), 8),
        "limit_price": None if limit_price is None else round(float(limit_price), 8),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _alpaca_order_type(order_type: OrderType) -> str:
    return "limit" if order_type == OrderType.LIMIT else "market"


def _parse_timestamp(value: str | datetime) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_iso_timestamp_with_timezone(value: str) -> bool:
    return bool(_ISO_TIMESTAMP_WITH_TZ_RE.fullmatch(value)) and _parse_timestamp(value) is not None


def _dry_run_safety(safety: BrokerSafetyConfig | None) -> BrokerSafetyConfig:
    if safety is None:
        return BrokerSafetyConfig(mode=BrokerAdapterMode.DRY_RUN)
    return replace(safety, mode=BrokerAdapterMode.DRY_RUN, approval=None)


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


def _validate_broker_handoff_order(order: dict[str, object], idx: int, adapter_mode: object) -> list[str]:
    errors: list[str] = []
    required = set(AlpacaPaperOrder.__dataclass_fields__)
    missing = sorted(required - set(order))
    if missing:
        errors.append(f"orders[{idx}] missing required fields: {', '.join(missing)}")
    extra = sorted(set(order) - required)
    if extra:
        errors.append(f"orders[{idx}] has unexpected fields: {', '.join(extra)}")
    required_text_fields = (
        "client_order_id",
        "adapter_mode",
        "account_mode",
        "symbol",
        "side",
        "order_type",
        "time_in_force",
        "reason",
    )
    for field_name in required_text_fields:
        if not order.get(field_name):
            errors.append(f"orders[{idx}].{field_name} must be non-empty")
    if order.get("adapter_mode") != adapter_mode:
        errors.append(f"orders[{idx}].adapter_mode must match artifact adapter_mode")
    if order.get("side") not in {"buy", "sell"}:
        errors.append(f"orders[{idx}].side must be buy or sell")
    if order.get("order_type") not in {"market", "limit"}:
        errors.append(f"orders[{idx}].order_type must be market or limit")
    quantity = order.get("quantity")
    if not isinstance(quantity, (int, float)) or quantity <= 0:
        errors.append(f"orders[{idx}].quantity must be a positive number")
    limit_price = order.get("limit_price")
    if limit_price is not None and (not isinstance(limit_price, (int, float)) or limit_price <= 0):
        errors.append(f"orders[{idx}].limit_price must be a positive number or null")
    max_notional = order.get("max_notional")
    if max_notional is not None and (not isinstance(max_notional, (int, float)) or max_notional <= 0):
        errors.append(f"orders[{idx}].max_notional must be a positive number or null")
    if order.get("submit_live") is not (adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED.value):
        errors.append(f"orders[{idx}].submit_live must match live_human_approved mode")
    expected_approval = (
        "approved" if adapter_mode == BrokerAdapterMode.LIVE_HUMAN_APPROVED.value else "requires_human_approval"
    )
    if order.get("approval_status") != expected_approval:
        errors.append(f"orders[{idx}].approval_status must be {expected_approval}")
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
