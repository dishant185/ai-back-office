"""Advanced mapping engine tests for edge cases and fuzzy matching.

These tests verify that the upgraded ColumnMatcher handles:
- CamelCase, snake_case, kebab-case, mixed formats
- Abbreviations (emp, qty, amt, dept, etc.)
- Semantic synonyms (Annual Salary → revenue, Compensation → payment_tier)
- Reordered tokens (Name Employee → employee_name)
- Partial/substring matches (Employee Joining Year → joining_year)
- Multi-word fuzzy matches
- Batch deduplication (no two columns map to the same target)
"""

from __future__ import annotations

from app.data.mapping.matcher import ColumnMatcher


class TestFuzzyMatching:
    """Test that fuzzy matching handles common column name variations."""

    def setup_method(self) -> None:
        self.matcher = ColumnMatcher()

    # ── Exact & Alias Matches ─────────────────────────────────────────────

    def test_exact_key_match(self) -> None:
        result = self.matcher.match_column("employee_name")
        assert result["suggested_target"] == "employee_name"
        assert result["confidence"] == 100

    def test_label_match(self) -> None:
        result = self.matcher.match_column("Employee Name")
        assert result["suggested_target"] == "employee_name"
        assert result["confidence"] >= 95

    def test_alias_match_net_sales(self) -> None:
        result = self.matcher.match_column("Net Sales")
        assert result["suggested_target"] == "revenue"
        assert result["confidence"] >= 90

    # ── CamelCase Handling ────────────────────────────────────────────────

    def test_camelcase_joining_year(self) -> None:
        result = self.matcher.match_column("JoiningYear")
        assert result["suggested_target"] == "joining_year"
        assert result["confidence"] >= 80

    def test_camelcase_payment_tier(self) -> None:
        result = self.matcher.match_column("PaymentTier")
        assert result["suggested_target"] == "payment_tier"
        assert result["confidence"] >= 80

    def test_camelcase_customer_name(self) -> None:
        result = self.matcher.match_column("CustomerName")
        assert result["suggested_target"] == "customer_name"
        assert result["confidence"] >= 80

    # ── Abbreviation Handling ─────────────────────────────────────────────

    def test_abbreviation_emp_name(self) -> None:
        result = self.matcher.match_column("Emp Name")
        assert result["suggested_target"] == "employee_name"
        assert result["confidence"] >= 70

    def test_abbreviation_qty(self) -> None:
        result = self.matcher.match_column("Qty")
        assert result["suggested_target"] == "quantity"
        assert result["confidence"] >= 60

    def test_abbreviation_dept(self) -> None:
        result = self.matcher.match_column("Dept")
        assert result["suggested_target"] == "department"
        assert result["confidence"] >= 60

    def test_abbreviation_txn_id(self) -> None:
        result = self.matcher.match_column("Txn ID")
        assert result["suggested_target"] == "transaction_id"
        assert result["confidence"] >= 70

    # ── Synonym / Semantic Matches ────────────────────────────────────────

    def test_synonym_turnover(self) -> None:
        result = self.matcher.match_column("Turnover")
        assert result["suggested_target"] == "revenue"
        assert result["confidence"] >= 90

    def test_synonym_qualification(self) -> None:
        result = self.matcher.match_column("Qualification")
        assert result["suggested_target"] == "education"
        assert result["confidence"] >= 90

    def test_synonym_staff_name(self) -> None:
        result = self.matcher.match_column("Staff Name")
        assert result["suggested_target"] == "employee_name"
        assert result["confidence"] >= 90

    def test_synonym_invoice_date(self) -> None:
        result = self.matcher.match_column("Invoice Date")
        assert result["suggested_target"] == "transaction_date"
        assert result["confidence"] >= 90

    def test_synonym_order_number(self) -> None:
        result = self.matcher.match_column("Order Number")
        assert result["suggested_target"] == "transaction_id"
        assert result["confidence"] >= 60

    # ── Reordered Tokens ──────────────────────────────────────────────────

    def test_reordered_tokens_name_employee(self) -> None:
        """'Name Employee' should still match 'employee_name'."""
        result = self.matcher.match_column("Name Employee")
        assert result["suggested_target"] == "employee_name"
        assert result["confidence"] >= 70

    # ── HR Dataset Column Patterns ────────────────────────────────────────

    def test_hr_column_education(self) -> None:
        result = self.matcher.match_column("Education")
        assert result["suggested_target"] == "education"

    def test_hr_column_age(self) -> None:
        result = self.matcher.match_column("Age")
        assert result["suggested_target"] == "age"

    def test_hr_column_gender(self) -> None:
        result = self.matcher.match_column("Gender")
        assert result["suggested_target"] == "gender"

    def test_hr_column_experience_years(self) -> None:
        result = self.matcher.match_column("Experience Years")
        assert result["suggested_target"] == "experience"
        assert result["confidence"] >= 80

    def test_hr_column_domain_experience(self) -> None:
        result = self.matcher.match_column("Domain Experience")
        assert result["suggested_target"] == "experience_in_current_domain"
        assert result["confidence"] >= 80

    # ── Sales Dataset Column Patterns ─────────────────────────────────────

    def test_sales_column_sales_amount(self) -> None:
        result = self.matcher.match_column("Sales Amount")
        # Could map to sales_amount or revenue — both acceptable
        assert result["suggested_target"] in ("sales_amount", "revenue")
        assert result["confidence"] >= 80

    def test_sales_column_sales_executive(self) -> None:
        """'Sales Executive' must map to employee_name, NOT revenue."""
        result = self.matcher.match_column("Sales Executive")
        assert result["suggested_target"] in ("employee_name", "sales_person")
        assert result["confidence"] >= 90

    # ── Customer Dataset Column Patterns ──────────────────────────────────

    def test_customer_column_client_name(self) -> None:
        result = self.matcher.match_column("Client Name")
        assert result["suggested_target"] == "customer_name"
        assert result["confidence"] >= 80

    def test_customer_column_account_id(self) -> None:
        result = self.matcher.match_column("Account ID")
        assert result["suggested_target"] == "customer_id"
        assert result["confidence"] >= 80

    def test_customer_column_buyer_city(self) -> None:
        result = self.matcher.match_column("Buyer City")
        assert result["suggested_target"] == "customer_city"
        assert result["confidence"] >= 60

    # ── Inventory Column Patterns ─────────────────────────────────────────

    def test_inventory_column_item_code(self) -> None:
        result = self.matcher.match_column("Item Code")
        assert result["suggested_target"] == "sku"
        assert result["confidence"] >= 80

    def test_inventory_column_units_sold(self) -> None:
        result = self.matcher.match_column("Units Sold")
        assert result["suggested_target"] == "sold_quantity"
        assert result["confidence"] >= 80

    def test_inventory_column_beginning_stock(self) -> None:
        result = self.matcher.match_column("Beginning Stock")
        assert result["suggested_target"] == "opening_stock"
        assert result["confidence"] >= 70

    # ── Finance Column Patterns ───────────────────────────────────────────

    def test_finance_column_gross_profit(self) -> None:
        result = self.matcher.match_column("Gross Profit")
        assert result["suggested_target"] == "profit"
        assert result["confidence"] >= 80

    def test_finance_column_cogs(self) -> None:
        result = self.matcher.match_column("COGS")
        assert result["suggested_target"] == "cost"
        assert result["confidence"] >= 70


class TestBatchDeduplication:
    """Test that batch match_columns prevents duplicate target assignments."""

    def setup_method(self) -> None:
        self.matcher = ColumnMatcher()

    def test_no_duplicate_targets_in_batch(self) -> None:
        """When multiple columns could map to the same target, only the best one wins."""
        columns = ["Employee Name", "Staff Name", "City", "Age"]
        results = self.matcher.match_columns(columns)

        targets = [r["suggested_target"] for r in results if r["suggested_target"] is not None]
        # No duplicates
        assert len(targets) == len(set(targets)), f"Duplicate targets: {targets}"

    def test_batch_hr_dataset(self) -> None:
        """Simulates a real HR dataset header."""
        columns = ["Education", "JoiningYear", "City", "PaymentTier", "Age", "Gender", "EverBenched"]
        results = self.matcher.match_columns(columns)

        mapped = {r["source"]: r["suggested_target"] for r in results if r["suggested_target"]}
        assert mapped.get("Education") == "education"
        assert mapped.get("JoiningYear") == "joining_year"
        assert mapped.get("City") == "city"
        assert mapped.get("PaymentTier") == "payment_tier"
        assert mapped.get("Age") == "age"
        assert mapped.get("Gender") == "gender"

    def test_batch_sales_dataset(self) -> None:
        """Simulates a real Sales dataset header."""
        columns = ["Date", "Product", "Quantity", "Revenue", "Cost", "Profit", "Region"]
        results = self.matcher.match_columns(columns)

        mapped = {r["source"]: r["suggested_target"] for r in results if r["suggested_target"]}
        assert mapped.get("Product") == "product"
        assert mapped.get("Quantity") == "quantity"
        assert mapped.get("Revenue") == "revenue"
        assert mapped.get("Cost") == "cost"
        assert mapped.get("Profit") == "profit"
        assert mapped.get("Region") == "region"

    def test_batch_customer_dataset(self) -> None:
        """Simulates a Customer data header."""
        columns = ["Customer Name", "Customer ID", "Customer City", "Customer Region", "Customer Type"]
        results = self.matcher.match_columns(columns)

        mapped = {r["source"]: r["suggested_target"] for r in results if r["suggested_target"]}
        assert mapped.get("Customer Name") == "customer_name"
        assert mapped.get("Customer ID") == "customer_id"
        assert mapped.get("Customer City") == "customer_city"
        assert mapped.get("Customer Region") == "customer_region"
        assert mapped.get("Customer Type") == "customer_type"

        # No duplicate targets
        targets = list(mapped.values())
        assert len(targets) == len(set(targets))


class TestEdgeCases:
    """Test edge cases like empty strings, special characters, etc."""

    def setup_method(self) -> None:
        self.matcher = ColumnMatcher()

    def test_empty_column_name(self) -> None:
        result = self.matcher.match_column("")
        assert result["suggested_target"] is None
        assert result["status"] == "needs_review"

    def test_whitespace_only(self) -> None:
        result = self.matcher.match_column("   ")
        assert result["suggested_target"] is None

    def test_special_characters(self) -> None:
        result = self.matcher.match_column("$$$Employee@@@Name!!!")
        # Should still match after normalization strips special chars
        assert result["suggested_target"] == "employee_name"

    def test_mixed_case_with_underscores(self) -> None:
        result = self.matcher.match_column("EMPLOYEE_NAME")
        assert result["suggested_target"] == "employee_name"
        assert result["confidence"] == 100

    def test_kebab_case(self) -> None:
        result = self.matcher.match_column("employee-name")
        assert result["suggested_target"] == "employee_name"
        assert result["confidence"] >= 90
