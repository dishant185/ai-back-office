from __future__ import annotations

import pandas as pd


class FinanceAnalytics:
    def analyze(self, frame: pd.DataFrame) -> dict[str, float | int | str]:
        amount = pd.to_numeric(frame.get("amount", pd.Series(dtype="float64")), errors="coerce").dropna()
        target = pd.to_numeric(frame.get("target", pd.Series(dtype="float64")), errors="coerce").dropna()

        total_amount = float(amount.sum()) if not amount.empty else 0.0
        avg_amount = float(amount.mean()) if not amount.empty else 0.0

        target_total = float(target.sum()) if not target.empty else 0.0
        attainment = (total_amount / target_total) if target_total else 0.0

        return {
            "total_amount": total_amount,
            "average_amount": avg_amount,
            "target_attainment": float(attainment),
        }
