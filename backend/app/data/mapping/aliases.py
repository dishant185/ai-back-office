from __future__ import annotations

from app.data.mapping.schema import STANDARD_SCHEMA


# ── Auto-generated base aliases from schema ───────────────────────────────────

alias_registry: dict[str, list[str]] = {
    field.key: list(dict.fromkeys([*field.aliases, field.key, field.label.lower()]))
    for field in STANDARD_SCHEMA.values()
}


# ── Comprehensive extra aliases ───────────────────────────────────────────────
# Each list covers: camelCase, PascalCase, abbreviations, domain synonyms,
# international/industry variants, and common CSV header formats.

extra_aliases: dict[str, list[str]] = {
    # ── Identity ──────────────────────────────────────────────────────────
    "employee_name": [
        "sales executive", "salesperson", "staff name", "worker name",
        "full name", "name", "emp name", "employee full name",
        "associate name", "personnel name", "rep name", "representative",
        "resource name", "team member", "member name",
    ],
    "employee_id": [
        "emp id", "staff id", "salesperson id", "worker id",
        "employee number", "emp no", "emp num", "personnel id",
        "employee code", "badge number", "emp code",
    ],
    "customer_name": [
        "client name", "account name", "buyer name", "consumer name",
        "customer", "cust name", "patron name", "contact name",
        "company name", "business name", "shopper name",
    ],
    "customer_id": [
        "client id", "account id", "buyer id", "consumer id",
        "cust id", "customer number", "customer code", "account number",
        "client code", "patron id",
    ],
    "customer_type": [
        "client type", "segment", "customer segment", "customer category",
        "account type", "buyer type", "client segment", "customer class",
        "customer classification", "cust type",
    ],

    # ── HR / People ───────────────────────────────────────────────────────
    "education": [
        "education level", "qualification", "qualification level", "degree",
        "highest qualification", "academic level", "academic qualification",
        "educational background", "degree level", "education qualification",
        "schooling", "edu level", "education attainment",
    ],
    "joining_year": [
        "joining year", "joiningyear", "year joined", "start year",
        "joining date year", "hire year", "date of joining", "doj year",
        "year of joining", "joined year", "employment year", "onboarding year",
    ],
    "age": [
        "employee age", "customer age", "person age", "years old",
        "current age", "age years",
    ],
    "gender": [
        "sex", "gender identity", "male female", "m f",
    ],
    "experience": [
        "years experience", "total experience", "experience years",
        "work experience", "professional experience", "yrs exp",
        "years of experience", "exp years", "career experience",
        "industry experience", "tenure",
    ],
    "experience_in_current_domain": [
        "domain experience", "current domain experience",
        "experience current domain", "domain exp",
        "current domain exp", "specialization experience",
    ],
    "employment_status": [
        "active status", "employment active", "is active",
        "leave status", "work status", "employee status",
        "job status", "current status", "working status",
    ],
    "payment_tier": [
        "payment tier", "paymenttier", "pay tier", "salary tier",
        "compensation tier", "wage tier", "pay band", "pay grade",
        "salary band", "salary grade", "comp tier", "pay level",
    ],

    # ── Location ──────────────────────────────────────────────────────────
    "city": [
        "employee city", "location city", "town", "municipality",
        "work city", "office city", "base city", "home city",
    ],
    "customer_city": [
        "customer location", "client city", "buyer city",
        "shipping city", "billing city", "cust city",
    ],
    "customer_region": [
        "customer geography", "region", "client region",
        "customer area", "market region", "sales region",
        "cust region", "geographic region",
    ],

    # ── Organization ──────────────────────────────────────────────────────
    "department": [
        "division", "dept", "business unit", "function",
        "organizational unit", "org unit", "section",
    ],
    "team": [
        "group", "squad", "work group", "team name",
        "project team", "unit",
    ],
    "region": [
        "territory", "area", "geographic region", "sales territory",
        "market", "zone", "district",
    ],
    "branch": [
        "office", "location", "branch name", "office name",
        "site", "outlet", "store",
    ],
    "dealer_name": [
        "dealer", "partner name", "vendor name", "distributor",
        "reseller", "channel partner", "agent name",
    ],

    # ── Transaction ───────────────────────────────────────────────────────
    "transaction_id": [
        "txn id", "invoice id", "order id", "receipt id",
        "transaction number", "order number", "invoice number",
        "txn number", "txn no", "order no", "bill number",
        "reference number", "ref id", "ref no",
    ],
    "transaction_date": [
        "sale date", "sales date", "invoice date", "date",
        "order date", "purchase date", "txn date", "billing date",
        "receipt date", "transaction dt", "date of transaction",
        "date of sale", "sold date",
    ],
    "date": [
        "event date", "record date", "entry date", "log date",
        "created date", "creation date", "effective date",
    ],
    "year": [
        "calendar year", "fiscal year", "fy", "yr",
    ],
    "month": [
        "month name", "calendar month", "period", "month of year",
    ],

    # ── Product / Inventory ───────────────────────────────────────────────
    "product": [
        "item", "sku name", "product name", "merchandise",
        "goods", "commodity", "article", "product description",
        "product title",
    ],
    "category": [
        "product category", "item category", "main category",
        "primary category", "group", "classification",
    ],
    "subcategory": [
        "sub category", "sub-category", "secondary category",
        "product subcategory", "item subcategory",
    ],
    "item": [
        "product item", "line item", "inventory item",
        "item name", "item description",
    ],
    "sku": [
        "item code", "product code", "barcode", "upc",
        "sku code", "article number", "part number",
    ],
    "opening_stock": [
        "opening inventory", "stock opening", "beginning stock",
        "beginning inventory", "initial stock", "start stock",
    ],
    "received_quantity": [
        "received", "inbound qty", "received stock",
        "quantity received", "stock received", "inbound quantity",
    ],
    "sold_quantity": [
        "units sold", "qty sold", "quantity sold",
        "sales quantity", "sold units", "outbound quantity",
    ],
    "closing_stock": [
        "ending inventory", "stock closing", "end stock",
        "ending stock", "final stock", "remaining stock",
    ],

    # ── Financial / Sales ─────────────────────────────────────────────────
    "revenue": [
        "sales amount", "net sales", "gross revenue", "turnover",
        "total sales", "sales revenue", "income", "gross sales",
        "sales value", "billing amount", "billed amount",
        "net revenue", "top line",
    ],
    "sales_amount": [
        "sales_amt", "sale amount", "total sale", "sale value",
        "sales val", "transaction amount", "order amount",
    ],
    "cost": [
        "total cost", "expense", "cogs", "cost of goods",
        "unit cost", "purchase cost", "buying price",
        "cost price", "expenditure",
    ],
    "profit": [
        "gross profit", "margin", "net profit", "earnings",
        "net margin", "gross margin", "profit amount",
        "operating profit", "bottom line",
    ],
    "amount": [
        "value", "total amount", "sum", "monetary value",
        "dollar amount", "charge amount", "fee amount",
    ],
    "quantity": [
        "qty", "units", "count", "pieces", "pcs",
        "number of units", "num units", "volume",
    ],

    # ── Payment ───────────────────────────────────────────────────────────
    "payment_method": [
        "payment mode", "paymentmethod", "mode of payment",
        "pay method", "payment type", "payment option",
        "transaction method", "pmt method", "pay mode",
    ],

    # ── Sales Performance ─────────────────────────────────────────────────
    "sales_person": [
        "sales executive", "salesperson", "sales rep",
        "sales representative", "account executive", "sales agent",
        "sales associate", "rep name", "ae name",
    ],
    "target": [
        "monthly target", "sales target", "target amount",
        "quota", "sales quota", "plan", "budget",
        "goal", "objective", "benchmark",
    ],
    "achievement": [
        "actual", "attainment", "actual amount", "achieved",
        "actual sales", "performance", "result",
    ],
    "achievement_percentage": [
        "achievement %", "attainment %", "quota attainment",
        "target achievement", "completion rate", "hit rate",
        "performance percentage", "achievement rate",
    ],

    # ── General ───────────────────────────────────────────────────────────
    "description": [
        "notes", "details", "comments", "remarks",
        "memo", "narrative", "observation", "summary",
    ],
    "status": [
        "state", "condition", "stage", "phase",
        "current state", "workflow status",
    ],
}


# ── Merge extra aliases into the registry ─────────────────────────────────────

for key, values in extra_aliases.items():
    alias_registry.setdefault(key, [])
    alias_registry[key].extend(values)
    # Deduplicate while preserving order
    alias_registry[key] = list(dict.fromkeys(alias_registry[key]))
