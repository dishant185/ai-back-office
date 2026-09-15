from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any
import uuid
import pandas as pd

from app.core.config import settings
from app.reporting.analytics.customer import CustomerAnalytics
from app.reporting.analytics.finance import FinanceAnalytics
from app.reporting.analytics.generic import GenericAnalytics
from app.reporting.analytics.hr import HRAnalytics
from app.reporting.analytics.inventory import InventoryAnalytics
from app.reporting.analytics.sales import SalesAnalytics
from app.reporting.formatter import format_value
from app.reporting.models import (
    DataQuality,
    DatasetProfile,
    ExecutiveSummary,
    ReportAnomaly,
    ReportMetric,
    ReportRecommendation,
    ReportResponse,
    ReportSection,
)
from app.reporting.profiler import DatasetProfiler
from app.reporting.report_registry import ReportRegistry


class ReportComposer:
    """Master orchestrator generating comprehensive, deterministic reports from any dataset."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or Path(settings.upload_dir) / "reports_store"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def compose_report(
        self,
        frame: pd.DataFrame,
        dataset_id: str = "dataset",
        filename: str = "dataset.csv",
        mappings: list[dict[str, Any]] | None = None,
    ) -> ReportResponse:
        # 1. Apply user mappings if provided
        working_frame = frame.copy()
        if mappings:
            rename_map = {
                str(m.get("source")): str(m.get("target"))
                for m in mappings
                if m.get("target") and not bool(m.get("ignored", False)) and m.get("source") in working_frame.columns
            }
            if rename_map:
                working_frame = working_frame.rename(columns=rename_map)
                working_frame = working_frame.loc[:, ~working_frame.columns.duplicated()].copy()

        # 2. Profile dataset & audit data quality
        profile, data_quality, standardized_frame = DatasetProfiler.profile(working_frame)

        # 3. Dispatch to domain analytics engine
        domain = profile.primary_domain
        kpis: list[ReportMetric] = []
        sections: list[ReportSection] = []
        anomalies: list[ReportAnomaly] = []
        recommendations: list[ReportRecommendation] = []

        try:
            if domain == "hr":
                kpis, sections, anomalies, recommendations = HRAnalytics.analyze(standardized_frame)
            elif domain == "sales":
                kpis, sections, anomalies, recommendations = SalesAnalytics.analyze(standardized_frame)
            elif domain == "finance":
                kpis, sections, anomalies, recommendations = FinanceAnalytics.analyze(standardized_frame)
            elif domain == "inventory":
                kpis, sections, anomalies, recommendations = InventoryAnalytics.analyze(standardized_frame)
            elif domain == "customer":
                kpis, sections, anomalies, recommendations = CustomerAnalytics.analyze(standardized_frame)
            else:
                kpis, sections, anomalies, recommendations = GenericAnalytics.analyze(standardized_frame)
        except Exception:
            kpis, sections, anomalies, recommendations = GenericAnalytics.analyze(standardized_frame)

        # Fallback if domain returned empty
        if not kpis or not sections:
            gen_kpis, gen_sections, gen_anomalies, gen_recs = GenericAnalytics.analyze(standardized_frame)
            if not kpis:
                kpis = gen_kpis
            if not sections:
                sections = gen_sections
            anomalies.extend(gen_anomalies)
            recommendations.extend(gen_recs)

        # 4. Generate Executive Summary
        exec_summary = self._synthesize_executive_summary(
            domain=domain,
            row_count=profile.row_count,
            col_count=profile.column_count,
            kpis=kpis,
            anomalies=anomalies,
            quality=data_quality,
        )

        # 5. Evaluate Report Catalog
        available_reports = ReportRegistry.evaluate(domain, profile.detected_capabilities)

        # 6. Report Titles & Subtitles
        title_map = {
            "hr": "Workforce & Talent Analytics Report",
            "sales": "Commercial Revenue & Sales Performance Report",
            "finance": "Financial Governance & Spend Analysis",
            "inventory": "Supply Chain & Inventory Management Report",
            "customer": "Customer Segmentation & Growth Report",
            "generic": "Comprehensive Business Intelligence Report",
        }
        title = title_map.get(domain, "Universal Business Intelligence Report")
        subtitle = f"Automated analytical audit of {filename} ({profile.row_count:,} rows × {profile.column_count} columns)"

        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        response = ReportResponse(
            report_id=report_id,
            dataset_id=dataset_id,
            title=title,
            subtitle=subtitle,
            domain=domain,
            generated_at=now_iso,
            row_count=profile.row_count,
            column_count=profile.column_count,
            executive_summary=exec_summary,
            kpi_metrics=kpis,
            sections=sections,
            anomalies=anomalies,
            data_quality=data_quality,
            recommendations=recommendations,
            available_report_types=available_reports,
            metadata={
                "filename": filename,
                "domain_confidence": profile.domain_confidence,
                "secondary_domains": profile.secondary_domains,
                "has_mappings": bool(mappings),
            },
        )

        # 7. Persist report to store
        self._save_report(response)

        return response

    def _synthesize_executive_summary(
        self,
        domain: str,
        row_count: int,
        col_count: int,
        kpis: list[ReportMetric],
        anomalies: list[ReportAnomaly],
        quality: DataQuality,
    ) -> ExecutiveSummary:
        domain_display = domain.upper() if domain in ("hr", "crm", "sku") else domain.capitalize()
        overview = (
            f"This executive intelligence report evaluates {row_count:,} verified operational records across "
            f"{col_count} parameters in the {domain_display} domain. The dataset demonstrates a data completeness "
            f"rating of {quality.completeness_pct:.1f}% with an overall data health score of {quality.score:.1f}/100."
        )

        highlights: list[str] = []
        for metric in kpis[:4]:
            if metric.value is not None and metric.formatted_value:
                highlights.append(f"{metric.name}: {metric.formatted_value} ({metric.description})")

        critical_findings: list[str] = []
        for anomaly in anomalies:
            critical_findings.append(f"{anomaly.label}: {anomaly.reason} (Measured: {anomaly.value})")

        if quality.missing_cells > 0:
            critical_findings.append(
                f"Data Hygiene: {quality.missing_cells:,} missing values detected across {len(quality.issues)} impacted fields."
            )

        sentiment = "cautionary" if (anomalies or quality.score < 80) else "positive"

        return ExecutiveSummary(
            overview=overview,
            key_highlights=highlights,
            critical_findings=critical_findings,
            sentiment=sentiment,
        )

    def _save_report(self, report: ReportResponse) -> None:
        try:
            target_path = self.reports_dir / f"{report.report_id}.json"
            target_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_report(self, report_id: str) -> ReportResponse | None:
        target_path = self.reports_dir / f"{report_id}.json"
        if not target_path.exists():
            return None
        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            return ReportResponse(**data)
        except Exception:
            return None

    def list_reports(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for f in self.reports_dir.glob("rep_*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({
                    "report_id": data.get("report_id"),
                    "dataset_id": data.get("dataset_id"),
                    "title": data.get("title"),
                    "domain": data.get("domain"),
                    "generated_at": data.get("generated_at"),
                    "row_count": data.get("row_count"),
                })
            except Exception:
                continue
        results.sort(key=lambda r: str(r.get("generated_at", "")), reverse=True)
        return results
