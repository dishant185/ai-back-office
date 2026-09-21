from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any
import uuid
import pandas as pd

from app.core.config import settings
from app.db.repositories.report_repository import ReportRepository
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
from app.reporting.report_query_builder import ReportQueryBuilder
from app.reporting.report_registry import ReportRegistry
from app.reporting.report_snapshot import ReportDatasetContextMismatchError, ReportSnapshot


class ReportComposer:
    """Master orchestrator generating comprehensive, deterministic reports from any dataset."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = reports_dir or Path(settings.upload_dir) / "reports_store"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.repository = ReportRepository()

    def compose_report(
        self,
        frame: pd.DataFrame,
        dataset_id: str = "dataset",
        filename: str = "dataset.csv",
        mappings: list[dict[str, Any]] | None = None,
        account_id: str = "account_default",
        dataset_version: int = 1,
        report_type: str = "standard",
        filters: dict[str, Any] | None = None,
        user_id: str = "guest",
    ) -> ReportResponse:
        # Invariant check
        if not dataset_id:
            raise ReportDatasetContextMismatchError("Dataset ID cannot be empty.")

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

        # 3. Validate requested report_type against capabilities
        available_reports = ReportRegistry.evaluate(
            profile.primary_domain,
            profile.detected_capabilities,
            list(standardized_frame.columns),
            frame=standardized_frame,
        )

        if report_type and report_type not in ("standard", "overview", "default"):
            rep_def = ReportRegistry.get_report_definition(report_type)
            if rep_def:
                matching_status = next((r for r in available_reports if r.key == report_type), None)
                if matching_status and not matching_status.available:
                    missing_str = ", ".join(matching_status.missing_capabilities)
                    raise ValueError(
                        f"Report '{matching_status.title}' cannot be generated because this dataset lacks required capabilities ({missing_str})."
                    )

        # 4. Apply filters if provided
        filtered_frame = standardized_frame
        if filters:
            query_builder = ReportQueryBuilder(standardized_frame, dataset_id)
            filtered_frame = query_builder.apply_filters(filters)

        # 5. Dispatch to domain analytics engine
        domain = profile.primary_domain
        kpis: list[ReportMetric] = []
        sections: list[ReportSection] = []
        anomalies: list[ReportAnomaly] = []
        recommendations: list[ReportRecommendation] = []

        try:
            if domain == "hr":
                kpis, sections, anomalies, recommendations = HRAnalytics.analyze(filtered_frame, report_type=report_type)
            elif domain == "sales":
                kpis, sections, anomalies, recommendations = SalesAnalytics.analyze(filtered_frame, report_type=report_type)
            elif domain == "finance":
                kpis, sections, anomalies, recommendations = FinanceAnalytics.analyze(filtered_frame)
            elif domain == "inventory":
                kpis, sections, anomalies, recommendations = InventoryAnalytics.analyze(filtered_frame)
            elif domain == "customer":
                kpis, sections, anomalies, recommendations = CustomerAnalytics.analyze(filtered_frame)
            else:
                kpis, sections, anomalies, recommendations = GenericAnalytics.analyze(filtered_frame, report_type=report_type)
        except Exception:
            kpis, sections, anomalies, recommendations = GenericAnalytics.analyze(filtered_frame, report_type=report_type)

        # Fallback if domain returned empty
        if not kpis or not sections:
            gen_kpis, gen_sections, gen_anomalies, gen_recs = GenericAnalytics.analyze(filtered_frame, report_type=report_type)
            if not kpis:
                kpis = gen_kpis
            if not sections:
                sections = gen_sections
            anomalies.extend(gen_anomalies)
            recommendations.extend(gen_recs)

        # 6. Generate Executive Summary (Report-Aware)
        exec_summary = self._synthesize_executive_summary(
            domain=domain,
            row_count=profile.row_count,
            col_count=profile.column_count,
            kpis=kpis,
            anomalies=anomalies,
            quality=data_quality,
            report_type=report_type or "standard",
            filename=filename,
        )

        # 7. Dynamic Titles
        rep_def = ReportRegistry.get_report_definition(report_type) if report_type else None
        if rep_def:
            title = rep_def["title"]
            subtitle = f"{rep_def['description']} — Audited from {filename} ({profile.row_count:,} records)"
        else:
            title_map = {
                "hr": "Workforce & Talent Analytics Report",
                "sales": "Commercial Revenue & Sales Performance Report",
                "finance": "Financial Governance & Spend Analysis",
                "inventory": "Supply Chain & Inventory Management Report",
                "customer": "Customer Segmentation & Growth Report",
                "generic": "Comprehensive Business Intelligence Report",
            }
            title = title_map.get(domain, "Universal Business Intelligence Report")
            subtitle = f"Analytical report for {filename} ({profile.row_count:,} records across {profile.column_count} fields)"

        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 8. Construct Reproducible Snapshot
        snapshot = ReportSnapshot(
            report_id=report_id,
            account_id=account_id,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_type=report_type or "standard",
            title=title,
            subtitle=subtitle,
            domain=domain,
            status="completed",
            filters=filters or {},
            generated_at=now_iso,
            row_count=profile.row_count,
            column_count=profile.column_count,
            executive_summary=exec_summary.model_dump(),
            kpi_metrics=[k.model_dump() for k in kpis],
            sections=[s.model_dump() for s in sections],
            anomalies=[a.model_dump() for a in anomalies],
            recommendations=[r.model_dump() for r in recommendations],
            data_quality=data_quality.model_dump(),
            metadata={
                "filename": filename,
                "domain_confidence": profile.domain_confidence,
                "secondary_domains": profile.secondary_domains,
                "has_mappings": bool(mappings),
            },
        )

        response = ReportResponse(
            report_id=report_id,
            account_id=account_id,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_type=report_type or "standard",
            status="completed",
            title=title,
            subtitle=subtitle,
            domain=domain,
            generated_at=now_iso,
            row_count=profile.row_count,
            column_count=profile.column_count,
            filters=filters or {},
            snapshot_id=snapshot.snapshot_id,
            is_stale=False,
            executive_summary=exec_summary,
            kpi_metrics=kpis,
            sections=sections,
            anomalies=anomalies,
            data_quality=data_quality,
            recommendations=recommendations,
            available_report_types=available_reports,
            metadata=snapshot.metadata,
        )

        # 9. Persist to MongoDB repository & file cache
        try:
            self.repository.create_report(
                account_id=account_id,
                user_id=user_id,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
                title=title,
                report_type=report_type or "standard",
                status="completed",
                filters=filters or {},
                content=response.model_dump(),
                snapshot=snapshot,
            )
        except Exception:
            pass

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
        report_type: str = "standard",
        filename: str = "dataset.csv",
    ) -> ExecutiveSummary:
        rep_title = (report_type or "report").replace("_", " ").title()
        rpt = (report_type or "").lower()

        # Build report-specific overview
        overview_parts = [
            f"This {rep_title.lower()} evaluates {row_count:,} operational records from {filename}."
        ]

        valid_kpis = [k for k in kpis if k.value is not None and str(k.value).lower() != "unavailable"]
        # DYNAMIC: Surface top available KPIs regardless of report type
        if valid_kpis:
            kpi_summary = ", ".join(f"{k.name}: {k.formatted_value}" for k in valid_kpis[:3])
            overview_parts.append(f"Primary verified metrics include: {kpi_summary}.")

        overview = " ".join(overview_parts)

        highlights: list[str] = []
        for metric in valid_kpis[:5]:
            desc = f" ({metric.description})" if metric.description else ""
            highlights.append(f"{metric.name}: {metric.formatted_value}{desc}")

        critical_findings: list[str] = []
        for anomaly in anomalies:
            critical_findings.append(f"{anomaly.label}: {anomaly.reason} (Measured: {anomaly.value})")

        if quality.missing_cells > 0:
            critical_findings.append(
                f"Data Completeness: {quality.missing_cells:,} missing values detected across {len(quality.issues)} fields."
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

    def _sanitize_legacy_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        es = payload.get("executive_summary")
        if not es or not isinstance(es, dict):
            return payload
        overview = es.get("overview", "")
        banned = [
            "operational governance standpoint",
            "organizational resilience",
            "zero synthetic extrapolations",
            "capability density",
            "prevent further talent drain and margin compression",
            "proactive retention stay-interviews",
            "operational roster represents a comprehensive census",
            "stable operational performance across",
            "data hygiene completeness rating of",
        ]
        if any(b in overview.lower() for b in banned):
            domain = payload.get("domain", "generic")
            row_count = payload.get("row_count", 0)
            kpis = payload.get("kpi_metrics", [])
            valid_kpis = [k for k in kpis if isinstance(k, dict) and k.get("value") is not None and str(k.get("value")).lower() != "unavailable"]
            metric_strs = [f"{k.get('name')}: {k.get('formatted_value')}" for k in valid_kpis[:3]]
            new_overview = f"Audited {payload.get('title', 'report')} evaluating {row_count:,} verified operational records in the {domain.capitalize()} domain."
            if metric_strs:
                new_overview += f" Primary verified metrics include: {', '.join(metric_strs)}."
            es["overview"] = new_overview
            payload["executive_summary"] = es
        return payload

    def get_report(self, report_id: str, account_id: str | None = None) -> ReportResponse | None:
        # First check MongoDB repository
        try:
            doc = self.repository.get_report(report_id, account_id=account_id)
            if doc and doc.get("content"):
                return ReportResponse(**self._sanitize_legacy_summary(doc["content"]))
            if doc and doc.get("snapshot"):
                return ReportResponse(**self._sanitize_legacy_summary(doc["snapshot"]))
        except Exception:
            pass

        # Fallback to file cache
        target_path = self.reports_dir / f"{report_id}.json"
        if not target_path.exists():
            return None
        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            if account_id and data.get("account_id") and data.get("account_id") != account_id:
                return None
            return ReportResponse(**self._sanitize_legacy_summary(data))
        except Exception:
            return None
