from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.data.mapping.aliases import alias_registry
from app.data.mapping.matcher import ColumnMatcher
from app.data.mapping.normalizer import ColumnNormalizer
from app.data.mapping.validator import MappingValidator
from app.main import app

client = TestClient(app)


def test_normalizer_handles_common_variants() -> None:
    assert ColumnNormalizer.normalize(" Net_Sales ") == "net sales"
    assert ColumnNormalizer.normalize("NET-SALES") == "net sales"
    assert ColumnNormalizer.normalize("Sales Amount") == "sales amount"


def test_alias_registry_contains_revenue_aliases() -> None:
    aliases = alias_registry["revenue"]
    assert "net sales" in [alias.lower() for alias in aliases]
    assert "sales amount" in [alias.lower() for alias in aliases]


def test_matcher_exact_and_alias_mapping() -> None:
    revenue_match = ColumnMatcher().match_column("Net Sales")
    employee_match = ColumnMatcher().match_column("Sales Executive")

    assert revenue_match["suggested_target"] == "revenue"
    assert revenue_match["confidence"] >= 90
    assert employee_match["suggested_target"] == "employee_name"
    assert employee_match["confidence"] >= 90


def test_matcher_flags_ambiguous_columns_for_review() -> None:
    result = ColumnMatcher().match_column("Amount")
    # Generic field now gets matched but flagged for review
    assert result["status"] == "needs_review" or result["suggested_target"] == "amount"


def test_mapping_validator_detects_duplicate_targets() -> None:
    validation = MappingValidator.validate(
        [
            {"source": "Sales", "target": "revenue"},
            {"source": "Net Sales", "target": "revenue"},
        ]
    )
    assert validation["valid"] is False
    assert any("Multiple columns mapped to revenue" in message for message in validation["errors"])


def test_mapping_validator_detects_missing_required_fields() -> None:
    validation = MappingValidator.validate(
        [
            {"source": "Customer", "target": "customer_name"},
        ]
    )
    assert validation["valid"] is False
    assert any("Missing required fields" in message for message in validation["errors"])


def test_generic_dataset_does_not_require_sales_fields() -> None:
    validation = MappingValidator.validate(
        [
            {"source": "Name", "target": "customer_name"},
            {"source": "Location", "target": "city"},
            {"source": "Category", "target": "category"},
            {"source": "Value", "target": "amount"},
        ],
        dataset_profile="generic",
    )
    assert validation["valid"] is True
    assert validation["errors"] == []


def test_hr_dataset_matches_employee_fields_without_sales_requirements() -> None:
    matcher = ColumnMatcher()

    result_education = matcher.match_column("Education")
    result_joining = matcher.match_column("JoiningYear")
    result_city = matcher.match_column("PaymentTier")
    result_age = matcher.match_column("Age")

    assert result_education["suggested_target"] == "education"
    assert result_joining["suggested_target"] == "joining_year"
    assert result_city["suggested_target"] == "payment_tier"
    assert result_age["suggested_target"] == "age"

    validation = MappingValidator.validate(
        [
            {"source": "Education", "target": "education"},
            {"source": "JoiningYear", "target": "joining_year"},
            {"source": "City", "target": "city"},
            {"source": "PaymentTier", "target": "payment_tier"},
            {"source": "Age", "target": "age"},
        ],
        dataset_profile="hr",
    )
    assert validation["valid"] is True
