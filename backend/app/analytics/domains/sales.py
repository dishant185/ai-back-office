from __future__ import annotations

import pandas as pd


class SalesAnalytics:
    def analyze(self, frame: pd.DataFrame) -> dict[str, float | int | str]:
        revenue = pd.to_numeric(frame.get("revenue", pd.Series(dtype="float64")), errors="coerce").dropna()
        profit = pd.to_numeric(frame.get("profit", pd.Series(dtype="float64")), errors="coerce").dropna()
        quantity = pd.to_numeric(frame.get("quantity", pd.Series(dtype="float64")), errors="coerce").dropna()

        region = frame.get("region")
        if region is not None and not region.empty:
            top_region = region.mode().iloc[0] if not region.mode().empty else "Unknown"
        else:
            top_region = "Unknown"

        total_revenue = float(revenue.sum()) if not revenue.empty else 0.0
        total_profit = float(profit.sum()) if not profit.empty else 0.0
        total_quantity = int(quantity.sum()) if not quantity.empty else 0
        margin = (total_profit / total_revenue) if total_revenue else 0.0

        return {
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "total_quantity": total_quantity,
            "top_region": str(top_region),
            "profit_margin": float(margin),
        }
