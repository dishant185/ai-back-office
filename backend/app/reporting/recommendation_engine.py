"""Evidence-Grounded Recommendation Engine.

Produces actionable executive recommendations strictly derived from verified insights.
Enforces the mandatory constraint: NEVER claim unsupported causation without analytical proof.
"""
from __future__ import annotations

import logging
from typing import Any
from app.reporting.models import ReportRecommendation, VerifiedInsight

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Derives structured recommendations strictly from verified insights."""

    @classmethod
    def generate_recommendations(
        cls,
        insights: list[VerifiedInsight],
        domain: str = "generic",
    ) -> list[ReportRecommendation]:
        recommendations: list[ReportRecommendation] = []
        rec_counter = 1

        for ins in insights:
            # 1. Attrition Risk
            if ins.metric == "attrition_rate":
                val = float(ins.value or 0)
                if val > 15.0:
                    recommendations.append(
                        ReportRecommendation(
                            id=f"rec_att_{rec_counter}",
                            title="Targeted Retention Intervention",
                            description=(
                                f"With verified turnover measuring {ins.formatted_value}, leadership should execute "
                                f"targeted stay-interviews and structured compensation parity audits within high-churn corridors. "
                                f"Note: Root cause drivers are not fully determined by attrition rate alone."
                            ),
                            priority="high",
                            category="retention",
                        )
                    )
                    rec_counter += 1

            # 2. Revenue or Demographic Concentration
            elif ins.type in ("LARGEST_SHARE", "TOP_ENTITY"):
                pct = float(ins.percentage or 0)
                if pct > 45.0:
                    entity_name = ins.entity or ins.dimension or "Primary Segment"
                    recommendations.append(
                        ReportRecommendation(
                            id=f"rec_conc_{rec_counter}",
                            title=f"Mitigate Operational Concentration in {entity_name}",
                            description=(
                                f"Verified analytics indicate that {entity_name} represents {pct:.1f}% of volume. "
                                f"Management should evaluate pipeline diversification to prevent single-cohort operational dependency."
                            ),
                            priority="high" if pct > 60.0 else "medium",
                            category="optimization",
                        )
                    )
                    rec_counter += 1

            # 3. Data Quality & Completeness
            elif ins.type == "DATA_QUALITY":
                comp = float(ins.value or 100.0)
                if comp < 98.0:
                    recommendations.append(
                        ReportRecommendation(
                            id=f"rec_dq_{rec_counter}",
                            title="Implement Upstream Ingestion Validation",
                            description=(
                                f"Dataset completeness stands at {ins.formatted_value}. Mandate strict schema constraint checks "
                                f"at upload to eliminate null density across critical reporting columns."
                            ),
                            priority="medium",
                            category="governance",
                        )
                    )
                    rec_counter += 1

            # 4. Outliers
            elif ins.type == "OUTLIER":
                recommendations.append(
                    ReportRecommendation(
                        id=f"rec_out_{rec_counter}",
                        title=f"Audit Upper Dispersion in {ins.dimension}",
                        description=(
                            f"{ins.formatted_value} were flagged beyond 2.5x IQR boundaries in {ins.dimension}. "
                            f"Audit outlier records to ensure billing, compensation, or recording accuracy."
                        ),
                        priority="low",
                        category="governance",
                    )
                )
                rec_counter += 1

        return recommendations[:4]
