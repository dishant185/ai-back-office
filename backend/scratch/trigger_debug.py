import asyncio
import json
import os
import sys

# Step 1: Force DEBUG_AI_VALIDATION=true
os.environ["DEBUG_AI_VALIDATION"] = "true"

from app.core.config import settings
from app.api.v1.endpoints.reports import _resolve_report_context
from app.reporting.executive_summary import ExecutiveSummaryGenerator
from app.ai.analyst import analyze_question

async def run_debug():
    print(f"=== CONFIG CHECK ===")
    print(f"settings.llm_provider: {settings.llm_provider}")
    print(f"settings.llm_model: {settings.llm_model}")
    print(f"settings.llm_base_url: {settings.llm_base_url}")
    print(f"settings.llm_api_key present: {bool(settings.llm_api_key)} (len: {len(settings.llm_api_key) if settings.llm_api_key else 0})")
    print(f"DEBUG_AI_VALIDATION: {os.getenv('DEBUG_AI_VALIDATION')}")
    print("=" * 40)

    report_id = "rep_d66709ed5b2e"
    account_id = "account_default"

    print(f"\n>>> 1. TRIGGERING REAL EXECUTIVE SUMMARY GENERATION FOR {report_id} <<<")
    try:
        payload, dataset_id, dataset_ver, report_type, report_ver, filters = _resolve_report_context(report_id, account_id)
        summary_result = await ExecutiveSummaryGenerator.generate_executive_summary(
            tenant_context={"account_id": account_id},
            dataset_context={"dataset_id": dataset_id, "version": dataset_ver},
            report_context=payload,
            regenerate=True,
        )
        print(f"\n[SUMMARY RESULT STATUS]: {summary_result.get('status')}")
        print(f"[SUMMARY RESULT OVERVIEW]: {summary_result.get('overview')}")
    except Exception as e:
        print(f"[SUMMARY ERROR]: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    print(f"\n>>> 2. TRIGGERING REAL AI ANALYST CHAT QUESTION <<<")
    try:
        chat_dataset_id = "sales_data-ec9c1d8486f04cfbb83965cceaf7ad3e.csv"
        question = "What is the total gross revenue?"
        chat_response = await analyze_question(
            question=question,
            dataset_id=chat_dataset_id,
        )
        print(f"\n[CHAT RESULT AI STATUS]: {chat_response.ai_status}")
        print(f"[CHAT RESULT ANSWER]: {chat_response.answer}")
    except Exception as e:
        print(f"[CHAT ERROR]: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
