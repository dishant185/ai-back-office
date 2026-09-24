"""Universal Query Planner.

Translates natural language questions and schema knowledge into a structured QueryPlan.
Does NOT perform arbitrary calculations; only emits the operational plan.
"""
from __future__ import annotations

import re
from typing import Any

from app.analytics.models import QueryPlan
from app.analyst.intent_classifier import IntentClassifier
from app.data.semantic.schema_builder import SemanticSchema


class QueryPlanner:
    """Constructs structured QueryPlan from question and dataset schema."""

    @classmethod
    def plan(
        cls,
        question: str,
        schema: SemanticSchema,
        conversation_context: dict[str, Any] | None = None,
    ) -> QueryPlan:
        q = question.strip()
        q_lower = q.lower()
        intent = IntentClassifier.classify(q, schema)

        col_by_semantic = {c.semantic_name: c for c in schema.columns}
        col_by_original = {c.original_name.lower(): c for c in schema.columns}
        numeric_cols = [c for c in schema.columns if c.role == "measure" or "int" in c.data_type or "float" in c.data_type]
        dim_cols = [c for c in schema.columns if c.role in ("dimension", "geographic_dimension") or "str" in c.data_type or "object" in c.data_type]

        def find_dimension() -> str | None:
            # Check conversation context inheritance first if query has pronouns
            if conversation_context and any(w in q_lower.split() for w in ["its", "their", "it", "them"]):
                last_dim = conversation_context.get("last_dimension")
                if last_dim:
                    return last_dim

            user_asked_for_id = bool(re.search(r"\b(id|identifier|code|sku|item|product)\b", q_lower))

            def is_allowed_dim(c_name: str) -> bool:
                if user_asked_for_id:
                    return True
                cn = c_name.lower().replace(" ", "_")
                if cn.endswith(("_id", "_code", "_key", "_sku", "_number")) or cn in ("id", "code", "sku", "key"):
                    return False
                col_obj = schema.get_column(c_name)
                if col_obj and col_obj.role == "identifier":
                    return False
                return True

            # If user explicitly asked for item or product, prioritize product/item identifier or name
            if re.search(r"\b(items?|products?)\b", q_lower) and not re.search(r"\b(categories|category)\b", q_lower):
                for p_col in ["Product_ID", "item_id", "product_id", "product_name", "item_name", "Product", "Item"]:
                    for c in schema.columns:
                        if c.original_name.lower() == p_col.lower() or c.semantic_name.lower() == p_col.lower():
                            return c.original_name

            # Check if a known region or category entity is in the question
            for reg in ["north", "south", "east", "west"]:
                if re.search(rf"\b{reg}\b", q_lower):
                    for c in schema.columns:
                        if any(t in c.original_name.lower() for t in ["region", "state", "territory"]):
                            return c.original_name

            # Check dimension aliases against schema (specific/longer categories first)
            dim_candidate_map = [
                ("category", ["product category", "product categories", "product_category", "item category", "category", "categories"]),
                ("product", ["product name", "product description", "item name", "product", "products", "item", "items"]),
                ("region", ["sales region", "region", "regions", "territory", "area"]),
                ("city", ["city", "cities", "location"]),
                ("sales_rep", ["sales rep", "rep", "reps", "representative", "representatives", "sales_rep", "salesperson", "sales person", "agent"]),
                ("channel", ["sales channel", "channel", "channels", "sales_channel"]),
                ("payment_method", ["payment method", "payment methods", "payment", "payments", "methods"]),
                ("customer_type", ["customer type", "customer", "customers", "client", "clients"]),
                ("education", ["education", "degree", "qualification"]),
                ("department", ["department", "departments"]),
                ("payment_tier", ["payment tier", "tier", "tiers"]),
                ("gender", ["gender", "sex"]),
            ]
            for canonical, aliases in dim_candidate_map:
                if any(a in q_lower for a in aliases):
                    if canonical in col_by_semantic and is_allowed_dim(col_by_semantic[canonical].original_name):
                        return col_by_semantic[canonical].original_name
                    for c in schema.columns:
                        if is_allowed_dim(c.original_name) and any(a in c.original_name.lower().replace("_", " ") for a in aliases):
                            return c.original_name
                    for k, v in col_by_semantic.items():
                        if canonical in k and is_allowed_dim(v.original_name):
                            return v.original_name

            # Fuzzy match in original columns (excluding identifiers unless requested)
            for c in schema.columns:
                if is_allowed_dim(c.original_name) and c.original_name.lower() in q_lower:
                    return c.original_name

            # Default to first categorical dimension if available (excluding identifiers)
            allowed_dims = [c.original_name for c in dim_cols if is_allowed_dim(c.original_name)]
            if allowed_dims:
                return allowed_dims[0]
            return dim_cols[0].original_name if dim_cols else None

        def find_measure() -> str | None:
            # 1. Units Sold / Quantity (check BEFORE sales to avoid false match on 'sold')
            if re.search(r"\b(units?\s+sold|sales\s+quantity|quantity\s+sold|units?|quantity|qty|volume)\b", q_lower):
                for q_cand in ["quantity", "quantity_sold", "units_sold"]:
                    if q_cand in col_by_semantic:
                        return col_by_semantic[q_cand].original_name
                for c in schema.columns:
                    if any(t in c.original_name.lower() for t in ["quantity_sold", "units_sold", "quantity", "qty"]):
                        return c.original_name

            # 2. Revenue / Sales Amount
            if re.search(r"\b(revenue|sales\s+amount|gross\s+revenue|total\s+sales|sales|turnover)\b", q_lower):
                for r_cand in ["sales_amount", "revenue", "amount", "gross_revenue", "sales"]:
                    if r_cand in col_by_semantic:
                        return col_by_semantic[r_cand].original_name
                for c in schema.columns:
                    if any(t in c.original_name.lower() for t in ["sales_amount", "revenue", "amount"]):
                        return c.original_name

            # 3. Unit Price / Cost / Discount / Age / Salary
            for term, semantic_targets in [
                ("price", ["unit_price", "price"]),
                ("cost", ["unit_cost", "cost"]),
                ("discount", ["discount"]),
                ("age", ["age"]),
                ("experience", ["experience"]),
                ("joining year", ["joining_year"]),
                ("salary", ["salary"]),
                ("amount", ["amount", "sales_amount"]),
            ]:
                if term in q_lower:
                    for target in semantic_targets:
                        if target in col_by_semantic:
                            return col_by_semantic[target].original_name
                    for c in schema.columns:
                        if term in c.original_name.lower():
                            return c.original_name

            # If question is asking for average / sum / min / max, pick the primary numeric measure
            if intent in ("SUM", "AVERAGE", "MINIMUM", "MAXIMUM", "MEDIAN"):
                for m_cand in ["sales_amount", "revenue", "amount", "quantity", "age", "unit_price"]:
                    if m_cand in col_by_semantic:
                        return col_by_semantic[m_cand].original_name
                return numeric_cols[0].original_name if numeric_cols else None

            return None

        def extract_filter() -> tuple[str | None, Any]:
            # Check item/product filter: e.g. "item 1099", "product 1099"
            m_item = re.search(r"\b(?:item|product|id|sku)\s+([A-Za-z0-9_-]+)\b", q_lower)
            if m_item:
                val_str = m_item.group(1)
                for c in schema.columns:
                    if any(t in c.original_name.lower() for t in ["product_id", "item_id", "product", "item"]) or c.semantic_name in ("item_id", "product_id"):
                        return c.original_name, val_str

            # Check region entity
            for reg in ["north", "south", "east", "west"]:
                if re.search(rf"\b{reg}\b", q_lower):
                    for c in schema.columns:
                        if any(t in c.original_name.lower() for t in ["region", "state", "territory"]):
                            return c.original_name, reg.capitalize()

            # Conversation context fallback
            if conversation_context:
                last_ent = conversation_context.get("last_entity")
                last_dim = conversation_context.get("last_dimension")
                if last_ent and (last_ent.lower() in q_lower or any(w in q_lower.split() for w in ["its", "it", "that", "this", "there", "them"])):
                    return last_dim or find_dimension(), last_ent

            return None, None

        # 1. Check for ambiguous questions (e.g. "What are sales?" when multiple sales fields exist)
        candidate_sales = [c.original_name for c in schema.columns if any(t in c.original_name.lower() for t in ["sales", "revenue"])]
        if len(candidate_sales) > 1 and re.search(r"^(what (are|is)\s+)?sales\??$", q_lower):
            clarification = f"I found several sales-related measures ({', '.join(candidate_sales)}). Do you mean {', '.join(candidate_sales[:-1])} or {candidate_sales[-1]}?"
            return QueryPlan(
                status="CLARIFICATION",
                intent="CLARIFICATION",
                clarification_question=clarification,
                confidence=0.60,
            )

        # 1b. Check temporal capability: if question asks for temporal analysis but no date field exists
        has_date_col = any(c.role in ("date", "datetime", "time_dimension") or any(t in c.data_type.lower() for t in ["date", "time"]) for c in schema.columns)
        if any(w in q_lower for w in ["last month", "last year", "monthly", "trend", "quarter", "over time", "yoy", "growth"]) and not has_date_col:
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="That analysis cannot be calculated because the dataset does not contain a validated date/time field.",
                confidence=0.95,
            )

        # 1c. Check for requested unavailable metrics
        profile_name = getattr(schema, "profile", "") or getattr(schema, "domain_profile", "")
        if ("revenue" in q_lower or "sales" in q_lower) and profile_name == "hr":
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="Revenue / sales metrics are unavailable in this HR dataset.",
            )

        if any(t in q_lower for t in ["ebitda", "after tax", "post tax", "roe", "return on equity", "accounting profit"]):
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="Tax / EBITDA / Net accounting profit metrics are not present in this dataset.",
            )

        if any(t in q_lower for t in ["net profit", "net income", "net margin"]):
            has_net = any("net" in c.original_name.lower() and "profit" in c.original_name.lower() for c in schema.columns)
            if not has_net:
                return QueryPlan(
                    status="UNAVAILABLE",
                    intent="UNAVAILABLE",
                    unavailable_reason="Net profit is unavailable because the dataset does not contain the required fields to calculate it.",
                )

        if any(t in q_lower for t in ["operating margin", "operating profit"]):
            has_op = any("operating" in c.original_name.lower() and ("margin" in c.original_name.lower() or "profit" in c.original_name.lower()) for c in schema.columns)
            if not has_op:
                return QueryPlan(
                    status="UNAVAILABLE",
                    intent="UNAVAILABLE",
                    unavailable_reason="Operating margin is unavailable because the required fields are not present in the dataset.",
                )

        if ("attrition" in q_lower or "resigned" in q_lower or "employee" in q_lower) and profile_name != "hr":
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="Employee / attrition metrics are not present in this sales dataset.",
            )

        # 2. Quality queries
        if intent == "MISSING_VALUE_CHECK":
            return QueryPlan(
                status="READY",
                intent="MISSING_DATA_AUDIT",
            )

        if intent in ("QUALITY", "DUPLICATE_CHECK"):
            return QueryPlan(
                status="READY",
                intent=intent,
            )

        # 3. Derived metrics (Estimated Profit, Attrition Rate)
        if intent == "DERIVED_METRIC":
            if "profit" in q_lower or "margin" in q_lower:
                return QueryPlan(
                    status="READY",
                    intent="DERIVED_METRIC",
                    measure="estimated_profit",
                )
            if any(k in q_lower for k in ("attrition", "left", "leave", "leaving", "churn", "resigned")):
                return QueryPlan(
                    status="READY",
                    intent="DERIVED_METRIC",
                    measure="attrition_rate",
                )

        # 4. LIST_UNIQUE (e.g. "What sales channels are available?", "What categories exist?")
        if intent == "LIST_UNIQUE":
            dim = find_dimension()
            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent="LIST_UNIQUE",
                dimension=dim,
                unavailable_reason=f"Could not find matching dimension in dataset for question: '{question}'" if not dim else None,
            )

        # 5. CRITICAL: COUNT_UNIQUE
        if intent == "COUNT_UNIQUE":
            dim = find_dimension()
            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent="COUNT_UNIQUE",
                dimension=dim,
                unavailable_reason=f"Could not find matching dimension in dataset for question: '{question}'" if not dim else None,
            )

        # 5. Total Row Count
        if intent == "COUNT":
            return QueryPlan(
                status="READY",
                intent="COUNT",
            )

        # 6. Top / Bottom Entity (with rank & limit awareness)
        if intent in ("TOP_ENTITY", "BOTTOM_ENTITY"):
            dim = find_dimension()
            meas = find_measure()
            agg = "AVG" if "average" in q_lower else "SUM"
            sort_order = "DESC" if intent == "TOP_ENTITY" else "ASC"
            rank = 1
            if re.search(r"\b(second|2nd)\b", q_lower):
                rank = 2
            elif re.search(r"\b(third|3rd)\b", q_lower):
                rank = 3

            limit = 1
            m_top = re.search(r"\b(?:top|first|highest)\s+(\d+)\b", q_lower)
            if m_top:
                limit = int(m_top.group(1))
            elif rank > 1:
                limit = rank

            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent=intent,
                dimension=dim,
                measure=meas,
                aggregation=agg,
                sort=sort_order,
                limit=limit,
                rank=rank,
                unavailable_reason=f"Could not identify dimension for entity ranking." if not dim else None,
            )

        # 7. Comparison (e.g. Compare North and South)
        if intent == "COMPARISON":
            meas = find_measure()
            entities: list[str] = []
            for reg in ["North", "South", "East", "West"]:
                if re.search(rf"\b{reg.lower()}\b", q_lower):
                    entities.append(reg)
            dim = None
            if len(entities) >= 2:
                for c in schema.columns:
                    if any(t in c.original_name.lower() for t in ["region", "state"]):
                        dim = c.original_name
                        break
            if not dim:
                dim = find_dimension()
            if len(entities) < 2 and conversation_context and conversation_context.get("entities"):
                entities = conversation_context["entities"]
            if len(entities) < 2:
                words = [w.strip("?,.!") for w in question.split() if len(w) > 2]
                skip_words = {"compare", "versus", "difference", "between", "what", "which", "sales", "revenue", "regions", "categories", "and", "the", "how", "much", "more", "did", "generate", "than"}
                candidates = [w for w in words if w.lower() not in skip_words]
                if len(candidates) >= 2:
                    entities = candidates[:2]
            return QueryPlan(
                status="READY",
                intent="COMPARISON",
                dimension=dim,
                measure=meas,
                entities=entities,
                calculation="difference",
            )

        # 8. Aggregations: SUM, AVERAGE, MINIMUM, MAXIMUM, MEDIAN
        if intent in ("SUM", "AVERAGE", "MINIMUM", "MAXIMUM", "MEDIAN"):
            meas = find_measure()
            if not meas:
                return QueryPlan(
                    status="UNAVAILABLE",
                    intent="UNAVAILABLE",
                    unavailable_reason=f"No matching numeric measure found for '{question}'.",
                )
            filter_col, filter_val = extract_filter()
            return QueryPlan(
                status="READY",
                intent=intent,
                measure=meas,
                aggregation=intent,
                filter_col=filter_col,
                filter_val=filter_val,
                dimension=filter_col,
            )

        # 9. Distribution / Group By
        if intent == "DISTRIBUTION":
            dim = find_dimension()
            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent="DISTRIBUTION",
                dimension=dim,
                limit=10,
                unavailable_reason=f"No matching dimension found in dataset for breakdown." if not dim else None,
            )

        # 10. Time Trend / Growth
        if intent in ("TREND", "GROWTH"):
            meas = find_measure()
            date_cols = [c.original_name for c in schema.columns if c.role == "time_dimension" or "date" in c.data_type]
            if not date_cols:
                return QueryPlan(
                    status="UNAVAILABLE",
                    intent="UNAVAILABLE",
                    unavailable_reason="A revenue trend cannot be calculated because the dataset does not contain a valid date/time field for temporal analysis.",
                )
            return QueryPlan(
                status="READY",
                intent=intent,
                measure=meas,
            )

        # 11. CORRELATION — needs two numeric columns
        if intent == "CORRELATION":
            mentioned_numerics = []
            for c in numeric_cols:
                if c.original_name.lower() in q_lower or c.semantic_name.lower() in q_lower:
                    mentioned_numerics.append(c.original_name)
            if len(mentioned_numerics) < 2:
                all_numerics = [c.original_name for c in numeric_cols]
                mentioned_numerics = all_numerics[:2]
            if len(mentioned_numerics) >= 2:
                return QueryPlan(
                    status="READY",
                    intent="CORRELATION",
                    measure=mentioned_numerics[0],
                    dimension=mentioned_numerics[1],
                )
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="At least two numeric columns are needed for correlation analysis.",
            )

        # 12. ANOMALY — detect outliers in a numeric column
        if intent == "ANOMALY":
            meas = find_measure() or (numeric_cols[0].original_name if numeric_cols else None)
            if meas:
                return QueryPlan(
                    status="READY",
                    intent="ANOMALY",
                    measure=meas,
                )
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="No numeric column available for anomaly detection.",
            )

        # 13. SHARE — share/contribution of a dimension
        if intent == "SHARE":
            dim = find_dimension()
            meas = find_measure()
            f_col, f_val = extract_filter()
            if f_col and f_val:
                dim = f_col
            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent="SHARE",
                dimension=dim,
                measure=meas,
                filter_col=f_col,
                filter_val=f_val,
                limit=10,
                calculation="percentage_share",
                unavailable_reason="No matching dimension found for share analysis." if not dim else None,
            )

        # 17. EXPLANATION / CAUSAL
        if intent == "EXPLANATION":
            if any(k in q_lower for k in ["better than", "higher than", "more than", "worse than", "different from"]):
                comp_entities = []
                for reg in ["North", "South", "East", "West"]:
                    if re.search(rf"\b{reg.lower()}\b", q_lower):
                        comp_entities.append(reg)
                dim = "Region" if len(comp_entities) >= 2 else find_dimension()
                meas = find_measure()
                return QueryPlan(
                    status="READY",
                    intent="CAUSAL_EXPLANATION",
                    dimension=dim,
                    measure=meas,
                    entities=comp_entities,
                )
            meas = find_measure()
            return QueryPlan(
                status="READY",
                intent="EXPLANATION",
                measure=meas,
            )

        # 14. RANK — ranking of entities
        if intent == "RANK":
            dim = find_dimension()
            meas = find_measure()
            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent="RANK",
                dimension=dim,
                measure=meas,
                limit=10,
                unavailable_reason="No matching dimension found for ranking." if not dim else None,
            )

        # 15. FILTER — filtered subset of data
        if intent == "FILTER":
            dim = find_dimension()
            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent="FILTER",
                dimension=dim,
                unavailable_reason="No matching field found for filter." if not dim else None,
            )

        # 16. SCHEMA — dataset structure inspection
        if intent == "SCHEMA":
            return QueryPlan(
                status="READY",
                intent="SCHEMA",
            )

        # 17. EXPLANATION — explain a metric or finding
        if intent == "EXPLANATION":
            meas = find_measure()
            return QueryPlan(
                status="READY",
                intent="EXPLANATION",
                measure=meas,
            )

        # 18. DATA_QUALITY — overall data quality assessment
        if intent == "DATA_QUALITY":
            return QueryPlan(
                status="READY",
                intent="DATA_QUALITY",
            )

        # 19. PERCENTILE — compute percentile of a numeric field
        if intent == "PERCENTILE":
            meas = find_measure()
            if not meas:
                return QueryPlan(
                    status="UNAVAILABLE",
                    intent="UNAVAILABLE",
                    unavailable_reason="No numeric field found for percentile computation.",
                )
            return QueryPlan(
                status="READY",
                intent="PERCENTILE",
                measure=meas,
            )

        # 20. Recommendations / Summary (fallback)
        return QueryPlan(
            status="READY",
            intent=intent,
        )

