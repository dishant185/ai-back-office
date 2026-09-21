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

            user_asked_for_id = bool(re.search(r"\b(id|identifier|code|sku)\b", q_lower))

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
            # Check common business measure terms
            for term, semantic_target in [
                ("sales", "sales_amount"),
                ("revenue", "revenue"),
                ("quantity", "quantity"),
                ("qty", "quantity"),
                ("price", "unit_price"),
                ("cost", "unit_cost"),
                ("discount", "discount"),
                ("age", "age"),
                ("experience", "experience"),
                ("joining year", "joining_year"),
                ("salary", "salary"),
                ("amount", "amount"),
            ]:
                if term in q_lower:
                    if semantic_target in col_by_semantic:
                        return col_by_semantic[semantic_target].original_name
                    # Check if original col matches term
                    for c in schema.columns:
                        if term in c.original_name.lower():
                            return c.original_name

            # If question is asking for average / sum / min / max, pick the primary numeric measure
            if intent in ("SUM", "AVERAGE", "MINIMUM", "MAXIMUM", "MEDIAN"):
                for m_cand in ["sales_amount", "amount", "revenue", "quantity", "age", "unit_price"]:
                    if m_cand in col_by_semantic:
                        return col_by_semantic[m_cand].original_name
                return numeric_cols[0].original_name if numeric_cols else None

            return None

        # 1. Check for requested unavailable metrics
        profile_name = getattr(schema, "profile", "") or getattr(schema, "domain_profile", "")
        if ("revenue" in q_lower or "sales" in q_lower) and profile_name == "hr":
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="Revenue / sales metrics are unavailable in this HR dataset.",
            )

        if any(t in q_lower for t in ["ebitda", "net income", "after tax", "post tax", "roe", "return on equity", "accounting profit"]):
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="Tax / EBITDA / Net accounting profit metrics are not present in this dataset.",
            )

        if ("attrition" in q_lower or "resigned" in q_lower or "employee" in q_lower) and profile_name != "hr":
            return QueryPlan(
                status="UNAVAILABLE",
                intent="UNAVAILABLE",
                unavailable_reason="Employee / attrition metrics are not present in this sales dataset.",
            )

        # 2. Quality queries
        if intent in ("QUALITY", "DUPLICATE_CHECK", "MISSING_VALUE_CHECK"):
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

        # 6. Top / Bottom Entity
        if intent in ("TOP_ENTITY", "BOTTOM_ENTITY"):
            dim = find_dimension()
            meas = find_measure()
            agg = "AVG" if "average" in q_lower else "SUM"
            sort_order = "DESC" if intent == "TOP_ENTITY" else "ASC"
            return QueryPlan(
                status="READY" if dim else "UNAVAILABLE",
                intent=intent,
                dimension=dim,
                measure=meas,
                aggregation=agg,
                sort=sort_order,
                limit=1,
                unavailable_reason=f"Could not identify dimension for entity ranking." if not dim else None,
            )

        # 7. Comparison (e.g. Compare North and South)
        if intent == "COMPARISON":
            dim = find_dimension()
            meas = find_measure()
            # Extract possible named entities from question
            entities: list[str] = []
            # Look for capitalised or known words
            words = [w.strip("?,.!") for w in question.split() if len(w) > 2]
            skip_words = {"compare", "versus", "difference", "between", "what", "which", "sales", "revenue", "regions", "categories", "and", "the"}
            candidates = [w for w in words if w.lower() not in skip_words]
            if len(candidates) >= 2:
                entities = candidates[:2]
            return QueryPlan(
                status="READY",
                intent="COMPARISON",
                dimension=dim,
                measure=meas,
                entities=entities,
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
            filter_col = None
            filter_val = None
            last_ent = conversation_context.get("last_entity") if conversation_context else None
            last_dim = conversation_context.get("last_dimension") if conversation_context else None
            if last_ent and (last_ent.lower() in q_lower or any(w in q_lower.split() for w in ["its", "it", "that", "this", "there", "them"])):
                filter_val = last_ent
                filter_col = last_dim or find_dimension()
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
        if intent == "TREND":
            meas = find_measure()
            return QueryPlan(
                status="READY",
                intent="TREND",
                measure=meas,
            )

        # 11. Recommendations / Summary
        return QueryPlan(
            status="READY",
            intent=intent,
        )
