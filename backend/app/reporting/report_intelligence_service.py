"""Dynamic Report Intelligence Service.

Implements the two-layer intelligence architecture:
Layer 1: Deterministic Capability Engine evaluates feasibility and candidate analyses.
Layer 2: LLM Report Planner prioritizes modules and provides grounded business context.
Includes strict validation against hallucinations and seamless offline fallback.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
import pandas as pd

from app.reporting.dataset_intelligence import DatasetIntelligenceService
from app.reporting.models import DynamicModuleCandidate, DynamicReportPlan, ReportTypeStatus
from app.reporting.report_registry import GLOBAL_REPORT_CATALOG, ReportRegistry

logger = logging.getLogger(__name__)

REPORT_PLANNER_SYSTEM_PROMPT = """You are the AI Report Intelligence Planner inside AI Back-Office Copilot.
Your task is to organize verified analytical capabilities into a useful business report.
The application has already determined which fields, capabilities, and analytical operations are available.
You MUST only select from the supplied capabilities.
You MUST NOT invent fields.
You MUST NOT invent metrics.
You MUST NOT invent report capabilities.
You MUST NOT calculate numerical values.
You MUST NOT claim that an analysis is available unless the application marked it available.
Prioritize analyses that are relevant to the actual dataset.
Avoid redundant report modules.
Use clear professional business language.
The goal is to help a business user understand what matters in their uploaded data.
Return structured JSON only adhering to this schema:
{
    "report_title": "string",
    "report_description": "string",
    "recommended_modules": [
        {
            "module_id": "string",
            "title": "string",
            "description": "string",
            "priority": "high" | "medium" | "low",
            "reason": "string"
        }
    ],
    "excluded_modules": [
        {
            "module_id": "string",
            "reason": "string"
        }
    ]
}"""


class ReportIntelligenceService:
    """Evaluates datasets dynamically to generate tailored, grounded report modules."""

    @classmethod
    def evaluate_candidates(
        cls,
        frame: pd.DataFrame,
        dataset_id: str,
        dataset_version: int = 1,
    ) -> list[DynamicModuleCandidate]:
        """Layer 1: Deterministic generation of valid candidate modules with real preview metrics."""
        intel = DatasetIntelligenceService.generate_profile(
            frame=frame,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
        )

        domain = intel["profile"]
        capabilities = {c: True for c in intel["capabilities"]}
        cols_lower = {c.lower() for c in frame.columns}

        # Evaluate catalog with frame
        raw_statuses = ReportRegistry.evaluate(
            domain=domain,
            capabilities=capabilities,
            available_fields=list(frame.columns),
            frame=frame,
        )

        candidates: list[DynamicModuleCandidate] = []
        for status in raw_statuses:
            rep_def = ReportRegistry.get_report_definition(status.key) or {}
            req_caps = rep_def.get("required_capabilities", [])
            req_fields = rep_def.get("required_fields", [])
            ops = rep_def.get("analytics_operations", ["COUNT", "GROUP_BY", "RANK"])

            # Map status
            module_status = "available" if status.available else "unavailable"
            if not status.available and any(c in capabilities for c in req_caps):
                module_status = "limited"

            # Assign deterministic priority
            priority = "high" if status.key in ("workforce_overview", "sales_overview", "inventory_overview", "attrition_analysis", "regional_sales") else "medium"
            if not status.available:
                priority = "low"

            reason = status.dynamic_insight or f"Feasible based on verified {', '.join(req_caps)} capabilities."

            candidates.append(
                DynamicModuleCandidate(
                    module_id=status.key,
                    title=status.title,
                    description=status.description,
                    domain=status.domain,
                    priority=priority,
                    reason=reason,
                    status=module_status,
                    required_capabilities=req_caps,
                    required_fields=req_fields,
                    analytics_operations=ops,
                    preview_metrics=status.preview_metrics,
                    dynamic_insight=status.dynamic_insight,
                )
            )

        # Sort: available first, domain matched first, high priority first
        candidates.sort(key=lambda c: (c.status != "available", c.domain != domain, c.priority != "high"))
        return candidates

    @classmethod
    async def plan_report_intelligence(
        cls,
        frame: pd.DataFrame,
        dataset_id: str,
        dataset_version: int = 1,
    ) -> DynamicReportPlan:
        """Two-Layer Orchestration: Deterministic candidates refined by LLM planner."""
        # 1. Deterministic Layer 1
        candidates = cls.evaluate_candidates(
            frame=frame,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
        )

        available_candidates = [c for c in candidates if c.status == "available"]
        domain = available_candidates[0].domain if available_candidates else "generic"

        # Default title map
        title_map = {
            "hr": "Workforce & Talent Analytics Intelligence",
            "sales": "Commercial Revenue & Market Performance Intelligence",
            "inventory": "Inventory Health & Supply Chain Intelligence",
            "generic": "Comprehensive Business Intelligence Suite",
        }
        default_title = title_map.get(domain, "Universal Business Intelligence Intelligence")
        default_desc = f"AI analyzed this dataset ({len(frame):,} records across {len(frame.columns)} attributes) and identified {len(available_candidates)} relevant business analyses."

        deterministic_plan = DynamicReportPlan(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            report_title=default_title,
            report_description=default_desc,
            recommended_modules=available_candidates[:8],
            excluded_modules=[
                {"module_id": c.module_id, "reason": "Missing required schema fields or lower business relevance."}
                for c in candidates if c.status != "available"
            ],
        )

        # 2. Layer 2: LLM Prioritization (if enabled)
        try:
            from app.ai.provider import AICompletionRequest, get_llm_provider
            provider = get_llm_provider()

            if provider.provider_name() == "deterministic-fallback":
                return deterministic_plan

            # Prepare structured context for LLM
            candidate_payload = [
                {
                    "module_id": c.module_id,
                    "title": c.title,
                    "preview_metrics": c.preview_metrics,
                    "insight": c.dynamic_insight,
                }
                for c in available_candidates[:12]
            ]

            user_prompt = (
                f"Analyze this uploaded company dataset to organize the report modules:\n\n"
                f"DATASET CONTEXT:\n"
                f"Domain: {domain.upper()}\n"
                f"Total Records: {len(frame):,}\n"
                f"Total Attributes: {len(frame.columns)}\n\n"
                f"AVAILABLE DETERMINISTIC CANDIDATES:\n"
                f"{json.dumps(candidate_payload, indent=2)}\n\n"
                f"Select and prioritize between 5 to 8 of the most relevant modules for executive leadership.\n"
                f"Provide concise, non-repetitive descriptions and grounded 'reason' ('Why this matters')."
            )

            req = AICompletionRequest(
                system_prompt=REPORT_PLANNER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.15,
                max_tokens=1024,
            )

            resp = await asyncio.wait_for(provider.generate(req), timeout=6.0)
            raw_content = resp.content.strip() if resp and resp.content else ""
            if not raw_content:
                return deterministic_plan

            # Strip markdown block if present
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_content)

            # Strict Validation of LLM Output
            valid_candidate_map = {c.module_id: c for c in available_candidates}
            recommended: list[DynamicModuleCandidate] = []

            for rec in parsed.get("recommended_modules", []):
                mid = rec.get("module_id")
                if mid in valid_candidate_map:
                    base = valid_candidate_map[mid].model_copy()
                    if rec.get("title"):
                        base.title = str(rec["title"])
                    if rec.get("description"):
                        base.description = str(rec["description"])
                    if rec.get("reason"):
                        base.reason = str(rec["reason"])
                    if rec.get("priority") in ("high", "medium", "low"):
                        base.priority = rec["priority"]
                    recommended.append(base)

            if len(recommended) >= 3:
                return DynamicReportPlan(
                    dataset_id=dataset_id,
                    dataset_version=dataset_version,
                    report_title=parsed.get("report_title") or default_title,
                    report_description=parsed.get("report_description") or default_desc,
                    recommended_modules=recommended,
                    excluded_modules=parsed.get("excluded_modules") or deterministic_plan.excluded_modules,
                )

        except Exception as exc:
            logger.warning("LLM report planner encountered an issue (%s). Using deterministic plan.", exc)

        return deterministic_plan
