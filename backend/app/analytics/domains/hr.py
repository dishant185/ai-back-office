from __future__ import annotations

import pandas as pd


class HRAnalytics:
    def analyze(self, frame: pd.DataFrame) -> dict[str, float | int | str]:
        age = pd.to_numeric(frame.get("age", pd.Series(dtype="float64")), errors="coerce").dropna()
        leave = pd.to_numeric(frame.get("leave_or_not", pd.Series(dtype="float64")), errors="coerce").dropna()
        city = frame.get("city")

        if city is not None and not city.empty:
            top_city = city.mode().iloc[0] if not city.mode().empty else "Unknown"
        else:
            top_city = "Unknown"

        employee_count = int(len(frame.index))
        avg_age = float(age.mean()) if not age.empty else 0.0
        attrition_rate = float(leave.mean()) if not leave.empty else 0.0

        return {
            "employee_count": employee_count,
            "average_age": avg_age,
            "attrition_rate": attrition_rate,
            "top_city": str(top_city),
        }
