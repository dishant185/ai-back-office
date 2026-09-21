"""Dashboard Intelligence Service.

Produces dynamic, dataset-aware dashboard layout definitions (KPIs, primary charts,
and executive alerts) based strictly on validated dataset capabilities.
"""
from __future__ import annotations

import logging
from typing import Any
import pandas as pd

from app.reporting.dataset_intelligence import DatasetIntelligenceService
from app.reporting.insight_engine import InsightEngine

logger = logging.getLogger(__name__)


class DashboardIntelligenceService:
    """Computes a dataset-tailored dashboard layout configuration."""

    @classmethod
    def generate_layout(
        cls,
        frame: pd.DataFrame,
        dataset_id: str,
        dataset_version: int = 1,
    ) -> dict[str, Any]:
        intel = DatasetIntelligenceService.generate_profile(
            frame=frame,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
        )
        domain = intel["profile"]
        insights = InsightEngine.extract_insights(
            frame=frame,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            domain=domain,
        )

        # Domain-specific KPIs
        kpi_cards: list[dict[str, Any]] = []
        chart_widgets: list[dict[str, Any]] = []

        if domain == "hr":
            kpi_cards = [
                {"id": "headcount", "title": "Total Roster", "value": f"{len(frame):,}", "subtext": "Audited personnel"},
                {"id": "departments", "title": "Departments", "value": str(frame['Department'].nunique() if 'Department' in frame.columns else frame['department'].nunique() if 'department' in frame.columns else 1), "subtext": "Active functional tracks"},
            ]
            # Check for attrition
            for ins in insights:
                if ins.metric == "attrition_rate":
                    kpi_cards.append({"id": "attrition", "title": "Gross Attrition", "value": ins.formatted_value, "subtext": "Departure corridor"})
                elif ins.metric == "median_age":
                    kpi_cards.append({"id": "median_age", "title": "Demographic Center", "value": ins.formatted_value, "subtext": "Median age"})

            chart_widgets = [
                {"id": "dept_dist", "title": "Departmental Headcount Allocation", "type": "bar"},
                {"id": "attr_risk", "title": "Turnover Risk Corridors", "type": "donut"},
            ]

        elif domain == "sales":
            for ins in insights:
                if ins.metric == "total_revenue":
                    kpi_cards.append({"id": "revenue", "title": "Gross Revenue", "value": ins.formatted_value, "subtext": "Commercial volume"})
            kpi_cards.append({"id": "orders", "title": "Transactions", "value": f"{len(frame):,}", "subtext": "Audited orders"})

            chart_widgets = [
                {"id": "rev_trend", "title": "Commercial Revenue Velocity", "type": "line"},
                {"id": "geo_share", "title": "Regional Market Distribution", "type": "horizontal_bar"},
            ]

        else:
            kpi_cards = [
                {"id": "rows", "title": "Audited Records", "value": f"{len(frame):,}", "subtext": "Canonical rows"},
                {"id": "columns", "title": "Attributes", "value": str(len(frame.columns)), "subtext": "Schema parameters"},
            ]
            chart_widgets = [
                {"id": "quality_score", "title": "Data Hygiene Matrix", "type": "bar"},
            ]

        return {
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
            "domain": domain,
            "kpi_cards": kpi_cards[:4],
            "chart_widgets": chart_widgets,
            "insights": [ins.model_dump() for ins in insights[:4]],
        }
