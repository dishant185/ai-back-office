import glob, os, sys
sys.path.insert(0, "backend")
from app.ai.context_builder import build_context_from_dataset_id
from app.ai.query_router import classify_query
from app.ai.verified_answer import get_verified_answer

sales_files = glob.glob("data/uploads/Sales*") or glob.glob("data/uploads/sales*")
print("Found sales files:", len(sales_files))
if sales_files:
    fname = os.path.basename(sales_files[0])
    ctx = build_context_from_dataset_id(fname)
    print("Profile:", ctx["profile"])
    print("Metrics:", ctx["metrics"])
    print("Dimensions:", list(ctx["dimensions"].keys()))
    for d, v in ctx["dimensions"].items():
        print(f"  {d}: {list(v.items())[:3]}")

import asyncio
from app.ai.analyst import analyze_question

async def run_test():
    # 1. Test sales
    print("--- SALES DATASET TEST ---")
    ans_sales = await analyze_question("What are the strongest products?", fname)
    print("Sales Products Answer:\n", ans_sales.answer)

    ans_rev = await analyze_question("What is the total revenue?", fname)
    print("Sales Revenue Answer:\n", ans_rev.answer)

    # 2. Test HR
    hr_files = [x for x in glob.glob("data/uploads/*") if "Cleaned" in x or "Employee" in x]
    if hr_files:
        hr_name = os.path.basename(hr_files[0])
        print("\n--- HR DATASET TEST (" + hr_name + ") ---")
        ans_hr1 = await analyze_question("How many employees are there?", hr_name)
        print("Headcount Answer:\n", ans_hr1.answer)
        ans_hr2 = await analyze_question("Which city has the most employees?", hr_name)
        print("City Answer:\n", ans_hr2.answer)

asyncio.run(run_test())


