from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tradearena.core.domain import Order, OrderType, Side


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
    reason: str


class AlpacaPaperExportAdapter:
    """Convert approved TradeArena orders into broker-review files.

    The adapter deliberately does not call Alpaca or any broker API. It creates
    a neutral JSON/CSV handoff for human review before any external system sees
    the order instructions.
    """

    name = "alpaca-paper-export-adapter"

    def __init__(self, *, time_in_force: str = "day", client_prefix: str = "ta-paper") -> None:
        self.time_in_force = time_in_force
        self.client_prefix = client_prefix

    def convert(self, orders: list[Order] | tuple[Order, ...]) -> list[AlpacaPaperOrder]:
        rows: list[AlpacaPaperOrder] = []
        for idx, order in enumerate(orders, start=1):
            if order.side == Side.HOLD or order.quantity <= 0:
                continue
            rows.append(
                AlpacaPaperOrder(
                    client_order_id=f"{self.client_prefix}-{idx:04d}-{_safe_symbol(order.symbol)}",
                    adapter_mode="offline_export",
                    account_mode="none",
                    symbol=order.symbol,
                    side=order.side.value,
                    order_type=_alpaca_order_type(order.order_type),
                    quantity=round(float(order.quantity), 8),
                    time_in_force=self.time_in_force,
                    limit_price=order.limit_price,
                    submit_live=False,
                    approval_status="requires_human_approval",
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
            "adapter_mode": "offline_export",
            "account_mode": "none",
            "paper_only": True,
            "live_submission": False,
            "manual_approval_required": True,
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
            "adapter_mode": "offline_export",
            "account_mode": "none",
            "paper_only": True,
            "manual_approval_required": True,
        }


def _alpaca_order_type(order_type: OrderType) -> str:
    return "limit" if order_type == OrderType.LIMIT else "market"


def _safe_symbol(symbol: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in symbol).strip("-")
