"""Natural Answer Builder for verified analytical results.

Converts authoritative VerifiedResult objects into human, professional,
natural language answers strictly grounded in verified facts.
"""
from __future__ import annotations

from typing import Any
from app.analytics.models import VerifiedResult


def _format_num(val: Any) -> str:
    if val is None:
        return "N/A"
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val.is_integer():
            return f"{int(val):,}"
        if isinstance(val, float):
            return f"{val:,.2f}"
        return f"{val:,}"
    return str(val)


class AnswerBuilder:
    """Builds grounded, natural conversational responses from VerifiedResult."""

    @classmethod
    def build_answer(cls, verified: VerifiedResult) -> dict[str, Any]:
        # Case 1: Clarification
        if verified.verification_status == "clarification":
            clarification_q = verified.result.get("clarification_question") or "Could you please clarify your question?"
            return {
                "status": "clarification",
                "question": clarification_q,
                "answer": clarification_q,
                "dataset_id": verified.dataset_id,
                "sources": [],
            }

        # Case 2: Unavailable
        if verified.verification_status == "unavailable" or verified.is_unavailable:
            reason = verified.error_message or "Requested information isn't available in this dataset."
            return {
                "status": "unavailable",
                "answer": reason,
                "dataset_id": verified.dataset_id,
                "sources": [],
            }

        # Case 2b: Rejected / Validation Failure
        if verified.verification_status == "rejected":
            reason = verified.error_message or "The requested analysis could not be verified against the dataset."
            return {
                "status": "rejected",
                "answer": reason,
                "dataset_id": verified.dataset_id,
                "sources": [],
            }

        intent = verified.intent
        res = verified.result
        fields = verified.source_fields or ([res.get("dimension")] if res.get("dimension") else ([res.get("measure")] if res.get("measure") else []))
        sources = [
            {
                "field": f,
                "operation": verified.intent,
                "dataset": verified.dataset_id,
                "status": "Verified",
            }
            for f in fields
        ]
        answer_text = ""

        # Case 3: LIST_UNIQUE
        if intent == "LIST_UNIQUE":
            dim = res.get("dimension") or "options"
            u_vals = res.get("unique_values", [])
            val = len(u_vals)
            clean_dim = dim.replace("_", " ").lower()
            if u_vals and len(u_vals) <= 8:
                vals_str = ", ".join(u_vals[:-1]) + f", and {u_vals[-1]}" if len(u_vals) > 1 else u_vals[0]
                answer_text = f"There are {val} {clean_dim}s available: {vals_str}."
            elif u_vals:
                vals_str = ", ".join(u_vals[:5]) + "..."
                answer_text = f"There are {val} {clean_dim}s available, including: {vals_str}."
            else:
                answer_text = f"No {clean_dim} options found in the dataset."

        # Case 3b: DUPLICATE_CHECK
        elif intent == "DUPLICATE_CHECK":
            cnt = res.get("value", 0)
            if cnt == 0:
                answer_text = "No duplicate records were found in the dataset."
            else:
                answer_text = f"Yes. I found {_format_num(cnt)} duplicate records in the dataset."

        # Case 3c: MISSING_VALUE_CHECK
        elif intent == "MISSING_VALUE_CHECK":
            cnt = res.get("value", 0)
            if cnt == 0:
                answer_text = "No missing values were found across the dataset."
            else:
                answer_text = f"There are {_format_num(cnt)} missing values across the dataset."

        # Case 3d: COUNT_UNIQUE
        elif intent == "COUNT_UNIQUE":
            dim = res.get("dimension") or "items"
            val = res.get("value", 0)
            u_vals = res.get("unique_values", [])
            clean_dim = dim.replace("_", " ").lower()
            if u_vals and len(u_vals) <= 6:
                vals_str = ", ".join(u_vals[:-1]) + f", and {u_vals[-1]}" if len(u_vals) > 1 else u_vals[0]
                answer_text = f"There are {val} {clean_dim}s covered in the dataset: {vals_str}."
            else:
                answer_text = f"There are {val} unique {clean_dim}s covered in the dataset."

        # Case 4: Total record COUNT
        elif intent == "COUNT":
            val = res.get("value", 0)
            answer_text = f"There are {_format_num(val)} records in the dataset."

        # Case 5: TOP_ENTITY / BOTTOM_ENTITY
        elif intent in ("TOP_ENTITY", "BOTTOM_ENTITY"):
            entity = res.get("entity")
            val = res.get("value")
            meas = res.get("measure", "records")
            dim = res.get("dimension", "Category")
            rank = res.get("rank", 1)
            records = res.get("records", [])
            is_top = "TOP" in intent
            rank_label = "highest" if is_top else "lowest"
            is_rev = any(t in meas.lower() for t in ["revenue", "sales", "amount"])

            # Entity label cleaning
            ent_label = f"Item {entity}" if any(t in dim.lower() for t in ["product", "item"]) and str(entity).isdigit() else str(entity)

            # Multiple records requested (e.g. top 5 products by revenue)
            if len(records) > 1 and rank == 1:
                clean_dim = dim.replace('_', ' ').title()
                clean_meas = "revenue" if is_rev else meas.replace('_', ' ').lower()
                lines = [f"Top {len(records)} {clean_dim} by {clean_meas}:"]
                for idx, r in enumerate(records, 1):
                    r_val = r["metric_value"]
                    val_str = f"${r_val:,.2f}" if is_rev else _format_num(r_val)
                    r_ent = f"Item {r['entity']}" if any(t in dim.lower() for t in ["product", "item"]) and str(r['entity']).isdigit() else str(r['entity'])
                    lines.append(f"{idx}. {r_ent}: {val_str}")
                answer_text = "\n".join(lines)
            elif rank == 2:
                val_str = f"${val:,.2f}" if is_rev else _format_num(val)
                clean_meas = "revenue" if is_rev else meas.replace('_', ' ').lower()
                answer_text = f"{ent_label} is the second-highest {dim.replace('_', ' ').lower()} by {clean_meas} at {val_str}."
            elif meas == "record_count":
                answer_text = f"{ent_label} has the {rank_label} number of records with {_format_num(val)} entries."
            elif is_rev:
                val_str = f"${val:,.2f}"
                answer_text = f"{ent_label} ranked first by revenue at {val_str}."
            elif any(t in meas.lower() for t in ["quantity", "units"]):
                answer_text = f"{ent_label} ranked first by quantity at {_format_num(val)}."
            else:
                clean_meas = meas.replace("_", " ").title()
                answer_text = f"{ent_label} ranked first by {clean_meas.lower()} at {_format_num(val)}."

        # Case 6: Numerical Aggregations (SUM, AVERAGE, MINIMUM, MAXIMUM, MEDIAN)
        elif intent in ("SUM", "AVERAGE", "AVG", "MINIMUM", "MIN", "MAXIMUM", "MAX", "MEDIAN"):
            meas = res.get("measure", "metric")
            val = res.get("value")
            plan = verified.query_plan or {}
            filter_val = plan.get("filter_val")
            filter_col = plan.get("filter_col")
            is_revenue = any(t in meas.lower() for t in ["sales", "revenue", "amount"])
            is_quantity = any(t in meas.lower() for t in ["quantity", "units"])

            if filter_val:
                if is_revenue:
                    val_str = f"${val:,.2f}"
                    ent_prefix = f"Item {filter_val}" if any(t in str(filter_col).lower() for t in ["product", "item"]) and str(filter_val).isdigit() else str(filter_val)
                    answer_text = f"{ent_prefix} generated {val_str} in revenue."
                elif is_quantity:
                    answer_text = f"{filter_val} recorded {_format_num(val)} units sold."
                else:
                    answer_text = f"{filter_val} recorded {_format_num(val)} {meas.replace('_', ' ').lower()}."
            else:
                if intent in ("AVERAGE", "AVG") and is_revenue:
                    # Bug 6: AOV vs Average Transaction Value
                    schema_cols = verified.source_fields or []
                    has_order_id = any("order" in str(c).lower() and "id" in str(c).lower() for c in schema_cols)
                    if has_order_id:
                        answer_text = f"Average Order Value is ${val:,.2f}."
                    else:
                        answer_text = f"Average Transaction Value is ${val:,.2f} (order-level grain is not verified as no order ID is present; calculated as mean revenue per transaction record)."
                elif intent == "SUM" and is_quantity:
                    # Bug 7 & Bug 10: Units Sold
                    if "quantity_sold" in meas.lower() or "units_sold" in meas.lower() or meas.lower() == "quantity":
                        answer_text = f"Total units sold is {_format_num(val)}."
                    elif "stock" in meas.lower():
                        answer_text = f"Stock On Hand is {_format_num(val)}."
                    elif "ordered" in meas.lower():
                        answer_text = f"Units Ordered is {_format_num(val)}."
                    elif "shipped" in meas.lower():
                        answer_text = f"Units Shipped is {_format_num(val)}."
                    else:
                        answer_text = f"Total quantity is {_format_num(val)}."
                elif intent == "SUM" and is_revenue:
                    answer_text = f"Total revenue is ${val:,.2f}."
                else:
                    intent_label = {
                        "SUM": "Total",
                        "AVERAGE": "Average",
                        "AVG": "Average",
                        "MINIMUM": "Minimum",
                        "MIN": "Minimum",
                        "MAXIMUM": "Maximum",
                        "MAX": "Maximum",
                        "MEDIAN": "Median",
                    }.get(intent, intent.capitalize())
                    val_str = f"${val:,.2f}" if is_revenue else _format_num(val)
                    answer_text = f"{intent_label} {meas.replace('_', ' ').lower()} is {val_str}."

        # Case 7: Derived Metrics (Profit, Attrition)
        elif intent == "DERIVED_METRIC":
            label = res.get("label", "Metric")
            val = res.get("value")
            if "profit" in label.lower():
                answer_text = f"The {label} is {_format_num(val)}."
            elif "attrition" in label.lower():
                pct = res.get("percentage", val)
                left = res.get("count_left")
                q_low = verified.question.lower()
                is_causal_inquiry = any(k in q_low for k in ["why", "reason", "cause", "driving"])
                if is_causal_inquiry:
                    answer_text = (
                        f"The dataset records an attrition rate of {pct}% ({_format_num(left)} departures). "
                        "While the dataset can show associations and patterns across dimensions (such as city, education, and experience), "
                        "it does not capture or establish the underlying causes or exit reasons for employees leaving."
                    )
                elif left is not None:
                    answer_text = f"The attrition rate is {pct}% ({_format_num(left)} employees left)."
                else:
                    answer_text = f"The attrition rate is {pct}%."
            else:
                answer_text = f"{label} is {_format_num(val)}."

        # Case 8: Quality
        elif intent == "QUALITY":
            label = res.get("label", "Issue Count")
            val = res.get("value", 0)
            answer_text = f"There are {_format_num(val)} {label.lower()} in the dataset."

        # Case 8b: MISSING_DATA_AUDIT
        elif intent == "MISSING_DATA_AUDIT":
            missing_cells = res.get("missing_cells", 0)
            comp = res.get("completeness", 100.0)
            absent = res.get("absent_analytical_fields", [])
            absent_str = f" In terms of analytical availability, fields for {', '.join(absent)} are not present in this dataset." if absent else ""
            answer_text = f"0 missing cells were found across the dataset ({comp}% data completeness).{absent_str}" if missing_cells == 0 else f"{missing_cells} missing cells were found across the dataset ({comp}% data completeness).{absent_str}"

        # Case 9: Comparison
        elif intent == "COMPARISON":
            ent_a = res.get("entity_a")
            val_a = res.get("value_a")
            ent_b = res.get("entity_b")
            val_b = res.get("value_b")
            diff = res.get("difference", 0.0)
            meas = (res.get("measure") or "revenue").replace("_", " ")
            is_rev = any(t in meas.lower() for t in ["revenue", "sales", "amount"])
            if ent_a and ent_b and val_a is not None and val_b is not None:
                val_a_str = f"${val_a:,.2f}" if is_rev else _format_num(val_a)
                val_b_str = f"${val_b:,.2f}" if is_rev else _format_num(val_b)
                diff_str = f"${abs(diff):,.2f}" if is_rev else _format_num(abs(diff))
                answer_text = (
                    f"{ent_a} generated {val_a_str} in revenue versus {val_b_str} for {ent_b}, "
                    f"a difference of {diff_str}."
                )
            else:
                answer_text = "Comparison analysis completed based on verified dataset data."

        # Case 9b: CAUSAL_EXPLANATION
        elif intent == "CAUSAL_EXPLANATION":
            higher_ent = res.get("higher_entity", "North")
            lower_ent = res.get("lower_entity", "South")
            higher_val = res.get("higher_value")
            lower_val = res.get("lower_value")
            meas = (res.get("measure") or "revenue").replace("_", " ").lower()
            is_rev = any(t in meas.lower() for t in ["revenue", "sales", "amount"])
            h_str = f"${higher_val:,.2f}" if is_rev and higher_val is not None else _format_num(higher_val)
            l_str = f"${lower_val:,.2f}" if is_rev and lower_val is not None else _format_num(lower_val)
            answer_text = (
                f"{higher_ent} generated more revenue than {lower_ent} ({h_str} vs {l_str}). "
                "However, the available dataset does not establish why the difference occurred, "
                "as underlying causal drivers are not captured in the data."
            )

        # Case 10: Share / Percentage
        elif intent == "SHARE":
            entity = res.get("entity")
            pct = res.get("percentage")
            if entity and pct is not None:
                answer_text = f"{entity} generated approximately {pct}% of total revenue."
            else:
                dist = res.get("distribution", [])
                dim = res.get("dimension", "Category")
                if dist:
                    lines = [f"Revenue share across **{dim}**:"]
                    lines.append("| " + dim + " | Value | Share (%) |")
                    lines.append("| :--- | :--- | :--- |")
                    for item in dist[:10]:
                        lines.append(f"| {item.get('label', item.get('item'))} | {_format_num(item.get('value'))} | {item.get('share', item.get('percentage'))}% |")
                    answer_text = "\n".join(lines)
                else:
                    answer_text = "Analysis completed based on verified dataset data."

        # Case 10b: Time Trend / Growth
        elif intent in ("TREND", "GROWTH"):
            periods = res.get("periods", [])
            meas = (res.get("measure") or "revenue").replace("_", " ").lower()
            is_rev = any(t in meas.lower() for t in ["revenue", "sales", "amount"])
            if periods:
                first_p = periods[0]
                last_p = periods[-1]
                first_val = first_p.get("total_val", first_p.get("txn_count", 0))
                last_val = last_p.get("total_val", last_p.get("txn_count", 0))
                f_str = f"${first_val:,.2f}" if is_rev else _format_num(first_val)
                l_str = f"${last_val:,.2f}" if is_rev else _format_num(last_val)
                answer_text = (
                    f"The {meas} trend spans {len(periods)} monthly periods (from {first_p.get('period')} to {last_p.get('period')}). "
                    f"Initial period {meas} was {f_str} and final period was {l_str}."
                )
            else:
                answer_text = "A revenue trend cannot be calculated because the dataset does not contain a valid date/time field for temporal analysis."

        # Case 10c: Anomaly
        elif intent == "ANOMALY":
            outlier_cnt = res.get("outlier_count", 0)
            if outlier_cnt == 0:
                answer_text = "No statistically detected anomalies were found under the configured anomaly analysis."
            else:
                answer_text = f"I detected {outlier_cnt} statistically significant anomalies in {res.get('measure', 'the metric')}."

        # Case 10d: Recommendation
        elif intent == "RECOMMENDATION":
            recs = res.get("recommendations", [])
            if recs:
                lines = ["Verified analytical recommendations:"]
                for r in recs:
                    lines.append(f"- **{r.get('title')}**: {r.get('description')}")
                answer_text = "\n".join(lines)
            else:
                answer_text = "Based on the available dataset, there is not enough evidence to make a specific operational recommendation."

        # Case 10e: Distribution
        elif intent == "DISTRIBUTION":
            dist = res.get("distribution", [])
            dim = res.get("dimension", "Category")
            if dist:
                lines = [f"Distribution across **{dim}**:"]
                lines.append("| " + dim + " | Count | Share (%) |")
                lines.append("| :--- | :--- | :--- |")
                for item in dist[:10]:
                    lines.append(f"| {item.get('item')} | {_format_num(item.get('count'))} | {item.get('percentage')}% |")
                answer_text = "\n".join(lines)
            else:
                answer_text = f"No distribution data found for {dim}."

        # Case 11: Summary
        else:
            rows = res.get("total_rows")
            cols = res.get("total_columns")
            if rows and cols:
                answer_text = f"The dataset contains {_format_num(rows)} rows across {cols} attributes."
            else:
                answer_text = "Analysis completed based on verified dataset data."

        return {
            "status": "verified",
            "answer": answer_text,
            "dataset_id": verified.dataset_id,
            "sources": sources,
            "entity": res.get("entity"),
            "value": res.get("value"),
            "dimension": res.get("dimension"),
            "measure": res.get("measure"),
            "raw_result": res,
        }
