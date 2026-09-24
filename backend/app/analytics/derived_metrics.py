"""Deterministic calculation of derived business metrics and financial lineage.

Strictly checks for required columns and returns UNAVAILABLE (None) if missing.
Enforces Section 19-22 Financial Semantic Validation:
- Never interchange Revenue, Gross Profit, Operating Profit, Net Profit, Gross Margin, Operating Margin, Net Margin.
- Every derived metric stores: numerator, denominator, formula, semantic_definition, source_fields.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
import pandas as pd

from app.data.semantic.schema_builder import SemanticSchema


class FinancialLineage(BaseModel):
    metric: str
    label: str
    value: float | None
    formatted_value: str
    numerator: str | None = None
    denominator: str | None = None
    formula: str | None = None
    semantic_definition: str
    source_fields: list[str] = Field(default_factory=list)
    verified: bool = False


def calculate_financial_lineage(frame: pd.DataFrame) -> dict[str, FinancialLineage]:
    """Deterministically audit and derive financial metrics with strict semantic separation."""
    cols_lower = {str(c).strip().lower(): str(c) for c in frame.columns}
    results: dict[str, FinancialLineage] = {}

    # 1. Identify Revenue
    rev_col = next((cols_lower[k] for k in ["revenue", "sales_amount", "gross_revenue", "sales", "total_sales"] if k in cols_lower), None)
    rev_val: float | None = None
    if rev_col:
        s_rev = pd.to_numeric(frame[rev_col], errors="coerce").dropna()
        if not s_rev.empty:
            rev_val = float(s_rev.sum())
            results["revenue"] = FinancialLineage(
                metric="revenue",
                label="Revenue",
                value=rev_val,
                formatted_value=f"${rev_val:,.2f}" if rev_val >= 0 else f"-${abs(rev_val):,.2f}",
                formula=f"SUM({rev_col})",
                semantic_definition="Total recognized top-line commercial turnover",
                source_fields=[rev_col],
                verified=True,
            )

    # 2. Identify COGS / Cost
    cogs_col = next((cols_lower[k] for k in ["cogs", "cost_of_goods_sold", "unit_cost", "direct_costs"] if k in cols_lower), None)
    cogs_val: float | None = None
    if cogs_col:
        s_cogs = pd.to_numeric(frame[cogs_col], errors="coerce").dropna()
        if not s_cogs.empty:
            cogs_val = float(s_cogs.sum())
            results["cogs"] = FinancialLineage(
                metric="cogs",
                label="Cost of Goods Sold",
                value=cogs_val,
                formatted_value=f"${cogs_val:,.2f}",
                formula=f"SUM({cogs_col})",
                semantic_definition="Direct costs attributable to the production of goods sold",
                source_fields=[cogs_col],
                verified=True,
            )

    # 3. Identify Operating Expenses (OPEX)
    opex_col = next((cols_lower[k] for k in ["opex", "operating_expenses", "operating_costs"] if k in cols_lower), None)
    opex_val: float | None = None
    if opex_col:
        s_opex = pd.to_numeric(frame[opex_col], errors="coerce").dropna()
        if not s_opex.empty:
            opex_val = float(s_opex.sum())
            results["opex"] = FinancialLineage(
                metric="opex",
                label="Operating Expenses",
                value=opex_val,
                formatted_value=f"${opex_val:,.2f}",
                formula=f"SUM({opex_col})",
                semantic_definition="Expenditures required to run day-to-day operations",
                source_fields=[opex_col],
                verified=True,
            )

    # 4. Gross Profit: Revenue - COGS
    gross_prof_col = next((cols_lower[k] for k in ["gross_profit", "gross_margin_amount"] if k in cols_lower), None)
    gross_prof_val: float | None = None
    if gross_prof_col:
        s_gp = pd.to_numeric(frame[gross_prof_col], errors="coerce").dropna()
        if not s_gp.empty:
            gross_prof_val = float(s_gp.sum())
            results["gross_profit"] = FinancialLineage(
                metric="gross_profit",
                label="Gross Profit",
                value=gross_prof_val,
                formatted_value=f"${gross_prof_val:,.2f}",
                formula=f"SUM({gross_prof_col})",
                semantic_definition="Profit earned after deducting production costs",
                source_fields=[gross_prof_col],
                verified=True,
            )
    elif rev_val is not None and cogs_val is not None:
        gross_prof_val = rev_val - cogs_val
        results["gross_profit"] = FinancialLineage(
            metric="gross_profit",
            label="Gross Profit",
            value=gross_prof_val,
            formatted_value=f"${gross_prof_val:,.2f}",
            numerator="revenue",
            denominator="cogs",
            formula=f"{rev_col} - {cogs_col}",
            semantic_definition="Derived: Total Revenue minus Cost of Goods Sold",
            source_fields=[rev_col, cogs_col],
            verified=True,
        )

    # 5. Gross Margin: Gross Profit / Revenue * 100
    if gross_prof_val is not None and rev_val and rev_val > 0:
        gm_pct = round((gross_prof_val / rev_val) * 100.0, 2)
        results["gross_margin"] = FinancialLineage(
            metric="gross_margin",
            label="Gross Margin",
            value=gm_pct,
            formatted_value=f"{gm_pct:.2f}%",
            numerator="gross_profit",
            denominator="revenue",
            formula="gross_profit / revenue * 100",
            semantic_definition="Percentage of revenue retained after deducting cost of goods sold",
            source_fields=[results["gross_profit"].source_fields[0], rev_col] if "gross_profit" in results else [],
            verified=True,
        )

    # 6. Operating Profit
    op_prof_col = next((cols_lower[k] for k in ["operating_profit", "ebit", "operating_income"] if k in cols_lower), None)
    op_prof_val: float | None = None
    if op_prof_col:
        s_op = pd.to_numeric(frame[op_prof_col], errors="coerce").dropna()
        if not s_op.empty:
            op_prof_val = float(s_op.sum())
            results["operating_profit"] = FinancialLineage(
                metric="operating_profit",
                label="Operating Profit",
                value=op_prof_val,
                formatted_value=f"${op_prof_val:,.2f}",
                formula=f"SUM({op_prof_col})",
                semantic_definition="Earnings from core operational activities prior to interest and taxes",
                source_fields=[op_prof_col],
                verified=True,
            )
    elif gross_prof_val is not None and opex_val is not None:
        op_prof_val = gross_prof_val - opex_val
        results["operating_profit"] = FinancialLineage(
            metric="operating_profit",
            label="Operating Profit",
            value=op_prof_val,
            formatted_value=f"${op_prof_val:,.2f}",
            numerator="gross_profit",
            denominator="opex",
            formula="gross_profit - operating_expenses",
            semantic_definition="Derived: Gross Profit minus Operating Expenses",
            source_fields=results["gross_profit"].source_fields + ([opex_col] if opex_col else []),
            verified=True,
        )

    # 7. Operating Margin: Operating Profit / Revenue * 100
    if op_prof_val is not None and rev_val and rev_val > 0:
        om_pct = round((op_prof_val / rev_val) * 100.0, 2)
        results["operating_margin"] = FinancialLineage(
            metric="operating_margin",
            label="Operating Margin",
            value=om_pct,
            formatted_value=f"{om_pct:.2f}%",
            numerator="operating_profit",
            denominator="revenue",
            formula="operating_profit / revenue * 100",
            semantic_definition="Percentage of revenue remaining after paying for operational costs",
            source_fields=[results["operating_profit"].source_fields[0], rev_col] if "operating_profit" in results else [],
            verified=True,
        )

    # 8. Net Profit
    net_prof_col = next((cols_lower[k] for k in ["net_profit", "net_income", "profit", "earnings"] if k in cols_lower), None)
    net_prof_val: float | None = None
    if net_prof_col:
        s_np = pd.to_numeric(frame[net_prof_col], errors="coerce").dropna()
        if not s_np.empty:
            net_prof_val = float(s_np.sum())
            label = "Net Profit" if ("net" in net_prof_col or net_prof_col == "profit") else "Total Profit"
            results["net_profit"] = FinancialLineage(
                metric="net_profit",
                label=label,
                value=net_prof_val,
                formatted_value=f"${net_prof_val:,.2f}",
                formula=f"SUM({net_prof_col})",
                semantic_definition="Bottom-line residual earnings after all operating and non-operating expenses",
                source_fields=[net_prof_col],
                verified=True,
            )

    # 9. Net Margin: Net Profit / Revenue * 100 (NEVER label as Operating Margin!)
    if net_prof_val is not None and rev_val and rev_val > 0:
        nm_pct = round((net_prof_val / rev_val) * 100.0, 2)
        results["net_margin"] = FinancialLineage(
            metric="net_margin",
            label="Net Profit Margin",
            value=nm_pct,
            formatted_value=f"{nm_pct:.2f}%",
            numerator="net_profit",
            denominator="revenue",
            formula="net_profit / revenue * 100",
            semantic_definition="Bottom-line net margin as a percentage of total revenue",
            source_fields=[results["net_profit"].source_fields[0], rev_col] if "net_profit" in results else [],
            verified=True,
        )

    return results


def calculate_estimated_profit(frame: pd.DataFrame, schema: SemanticSchema) -> tuple[float | None, str, list[str]]:
    """Legacy helper maintained for compatibility; delegates to financial lineage."""
    lineage = calculate_financial_lineage(frame)
    if "net_profit" in lineage and lineage["net_profit"].value is not None:
        return lineage["net_profit"].value, lineage["net_profit"].label, lineage["net_profit"].source_fields
    if "gross_profit" in lineage and lineage["gross_profit"].value is not None:
        return lineage["gross_profit"].value, lineage["gross_profit"].label, lineage["gross_profit"].source_fields
    return None, "Estimated Profit", []


def calculate_attrition_rate(frame: pd.DataFrame, schema: SemanticSchema | None = None) -> tuple[float | None, int, list[str]]:
    """Calculate HR attrition rate from LeaveOrNot or attrition field.

    Returns: (attrition_rate_pct, employees_left_count, source_columns)
    """
    att_col = None
    if schema:
        cols_by_semantic = {c.semantic_name: c.original_name for c in schema.columns}
        att_col = cols_by_semantic.get("attrition")

    if not att_col:
        for col in frame.columns:
            col_low = str(col).lower()
            if any(k in col_low for k in ["attrition", "leave_or_not", "left", "separation", "churn"]):
                att_col = str(col)
                break

    if att_col and att_col in frame.columns:
        series = frame[att_col]
        total = len(series)
        if total == 0:
            return 0.0, 0, [att_col]

        if pd.api.types.is_numeric_dtype(series):
            left_count = int((series == 1).sum())
        else:
            left_count = int(series.astype(str).str.strip().str.lower().isin(["1", "yes", "true", "left", "resigned", "churned", "terminated"]).sum())

        rate = (left_count / total * 100) if total > 0 else 0.0
        return round(rate, 2), left_count, [att_col]

    return None, 0, []
