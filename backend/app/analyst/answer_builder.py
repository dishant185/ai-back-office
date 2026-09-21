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
            is_top = "TOP" in intent
            rank_label = "highest" if is_top else "lowest"
            if meas == "record_count":
                answer_text = f"{entity} has the {rank_label} number of records with {_format_num(val)} entries."
            else:
                clean_meas = meas.replace("_", " ").title()
                answer_text = f"{entity} has the {rank_label} {clean_meas.lower()} at {_format_num(val)}."

        # Case 6: Numerical Aggregations (SUM, AVERAGE, MINIMUM, MAXIMUM, MEDIAN)
        elif intent in ("SUM", "AVERAGE", "AVG", "MINIMUM", "MIN", "MAXIMUM", "MAX", "MEDIAN"):
            meas = res.get("measure", "metric").replace("_", " ").title()
            val = res.get("value")
            plan = verified.query_plan or {}
            filter_val = plan.get("filter_val")
            if filter_val:
                unit_str = " units in total" if "quant" in meas.lower() or "unit" in meas.lower() else " in total"
                answer_text = f"{filter_val} recorded {_format_num(val)}{unit_str} {meas.lower()}."
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
                answer_text = f"{intent_label} {meas.lower()} is {_format_num(val)}."

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

        # Case 9: Comparison
        elif intent == "COMPARISON":
            ent_a = res.get("entity_a")
            val_a = res.get("value_a")
            ent_b = res.get("entity_b")
            val_b = res.get("value_b")
            diff = res.get("difference", 0.0)
            meas = (res.get("measure") or "sales").replace("_", " ")
            if ent_a and ent_b and val_a is not None and val_b is not None:
                diff_val = abs(diff) if diff is not None else 0.0
                answer_text = (
                    f"{ent_a} generated {_format_num(val_a)} in {meas} compared with {_format_num(val_b)} in {ent_b}, "
                    f"a difference of {_format_num(diff_val)}."
                )
            else:
                answer_text = "Comparison analysis completed based on verified dataset data."

        # Case 10: Distribution
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
