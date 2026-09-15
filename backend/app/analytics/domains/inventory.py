from __future__ import annotations

import pandas as pd


class InventoryAnalytics:
    def analyze(self, frame: pd.DataFrame) -> dict[str, float | int | str]:
        opening = pd.to_numeric(frame.get("opening_stock", pd.Series(dtype="float64")), errors="coerce").dropna()
        received = pd.to_numeric(frame.get("received_quantity", pd.Series(dtype="float64")), errors="coerce").dropna()
        sold = pd.to_numeric(frame.get("sold_quantity", pd.Series(dtype="float64")), errors="coerce").dropna()
        closing = pd.to_numeric(frame.get("closing_stock", pd.Series(dtype="float64")), errors="coerce").dropna()

        total_opening_stock = float(opening.sum()) if not opening.empty else 0.0
        total_received_quantity = float(received.sum()) if not received.empty else 0.0
        total_sold_quantity = float(sold.sum()) if not sold.empty else 0.0
        total_closing_stock = float(closing.sum()) if not closing.empty else 0.0

        turnover = (total_sold_quantity / (total_opening_stock + total_received_quantity)) if (total_opening_stock + total_received_quantity) else 0.0

        return {
            "total_opening_stock": total_opening_stock,
            "total_received_quantity": total_received_quantity,
            "total_sold_quantity": total_sold_quantity,
            "total_closing_stock": total_closing_stock,
            "inventory_turnover": float(turnover),
        }
