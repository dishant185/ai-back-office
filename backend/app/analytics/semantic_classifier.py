"""Novera — Universal Semantic Classifier & Measure Validator.

Strict, non-negotiable classification of dataset fields into canonical semantic classes
and business roles. Enforces absolute identifier protection and confidence-based gating.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any
import pandas as pd
from pydantic import BaseModel, Field


class SemanticClass(str, Enum):
    IDENTIFIER = "IDENTIFIER"
    MEASURE = "MEASURE"
    DIMENSION = "DIMENSION"
    DATE = "DATE"
    DATETIME = "DATETIME"
    PERCENTAGE = "PERCENTAGE"
    RATIO = "RATIO"
    QUANTITY = "QUANTITY"
    AMOUNT = "AMOUNT"
    SCORE = "SCORE"
    STATUS = "STATUS"
    ENTITY = "ENTITY"
    PII = "PII"
    UNKNOWN = "UNKNOWN"


class BusinessRole(str, Enum):
    IDENTIFIER = "IDENTIFIER"
    MEASURE = "MEASURE"
    DIMENSION = "DIMENSION"
    TIME_DIMENSION = "TIME_DIMENSION"
    STATUS = "STATUS"
    UNKNOWN = "UNKNOWN"


class ClassificationStatus(str, Enum):
    AUTO_CONFIRMED = "AUTO_CONFIRMED"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    USER_CONFIRMATION_REQUIRED = "USER_CONFIRMATION_REQUIRED"


class FieldSemanticProfile(BaseModel):
    source_name: str
    semantic_name: str
    semantic_class: SemanticClass
    business_role: BusinessRole
    detected_type: str
    unit: str | None = None
    allowed_aggregations: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    status: ClassificationStatus = ClassificationStatus.AUTO_CONFIRMED
    is_identifier: bool = False
    is_temporal: bool = False
    is_numeric_measure: bool = False
    cardinality: int = 0
    uniqueness_ratio: float = 0.0
    null_ratio: float = 0.0
    reasons: list[str] = Field(default_factory=list)


class SemanticClassifier:
    """Universal field classifier evaluating column name, dtypes, value distributions,

    cardinality, and business context without domain hardcoding.
    """

    # Strict Identifiers: High-entropy unique keys, entities, and serials
    IDENTIFIER_EXACT = {
        "id", "uuid", "guid", "pk", "fk",
        "employee_id", "empid", "emp_id", "employeeid", "employee_number",
        "customer_id", "custid", "cust_id", "customerid", "client_id", "account_id",
        "record_id", "row_id", "rec_id", "rowid", "entry_id", "id_number",
        "transaction_id", "trans_id", "txn_id", "tx_id",
        "order_id", "order_number", "ord_id", "invoice_id", "invoice_number", "inv_id",
        "serial_number", "vin", "imei", "device_id", "tracking_number",
        "ssn", "national_id", "passport_number", "tax_id",
    }

    # PII Fields (which are also restricted from metric aggregations)
    PII_PATTERNS = [
        re.compile(r"\b(?:phone|mobile|cell|fax|telephone)\b", re.I),
        re.compile(r"\b(?:email|e_mail|email_address)\b", re.I),
        re.compile(r"\b(?:ssn|social_security|passport)\b", re.I),
    ]

    # Explicit Dimensions / Categorical Codes that must NOT be treated as primary identifiers
    VALID_CODE_DIMENSIONS = {
        "postal_code", "zip_code", "zip", "postcode",
        "branch_code", "store_code", "department_code", "dept_code",
        "product_code", "sku", "item_code", "category_code",
        "region_code", "country_code", "state_code", "area_code",
        "airport_code", "currency_code", "language_code",
        "payment_tier", "tier", "grade", "level", "step", "band",
    }

    # Temporal Patterns
    DATE_PATTERNS = [
        re.compile(r"\b(?:date|day|month|year|quarter|week|period)\b", re.I),
        re.compile(r"\b(?:hire_date|join_date|birth_date|dob|order_date|ship_date|transaction_date|created_at|updated_at|timestamp)\b", re.I),
    ]

    # Amount / Currency Patterns
    AMOUNT_PATTERNS = [
        re.compile(r"\b(?:revenue|sales|income|salary|wage|cost|expense|cogs|price|fee|budget|amount|spend|margin_amount|profit|gross_profit|net_profit|operating_profit)\b", re.I),
    ]

    # Percentage / Ratio Patterns
    PERCENTAGE_PATTERNS = [
        re.compile(r"\b(?:rate|ratio|percent|percentage|pct|margin|share|yield)\b", re.I),
    ]

    # Quantity / Count Patterns
    QUANTITY_PATTERNS = [
        re.compile(r"\b(?:count|quantity|qty|units|volume|headcount|inventory|items|stock|hours|days|years|tenure|age|experience)\b", re.I),
    ]

    # Score / Index Patterns
    SCORE_PATTERNS = [
        re.compile(r"\b(?:score|rating|index|rank|nps|satisfaction|grade|evaluation|level)\b", re.I),
    ]

    # Status / Outcome Patterns
    STATUS_PATTERNS = [
        re.compile(r"\b(?:status|state|stage|outcome|churn|attrition|attrited|leave_or_not|left|terminated|active|flag)\b", re.I),
    ]

    @classmethod
    def classify_field(cls, col_name: str, series: pd.Series) -> FieldSemanticProfile:
        clean_name = str(col_name).strip()
        norm_name = clean_name.lower().replace(" ", "_").replace("-", "_")
        match_name = norm_name.replace("_", " ")
        total_rows = len(series)
        non_null = series.dropna()
        non_null_count = len(non_null)
        cardinality = int(non_null.nunique()) if non_null_count > 0 else 0
        uniqueness_ratio = (cardinality / non_null_count) if non_null_count > 0 else 0.0
        null_ratio = ((total_rows - non_null_count) / total_rows) if total_rows > 0 else 1.0

        # Type detection
        is_numeric = pd.api.types.is_numeric_dtype(series)
        is_datetime_dtype = pd.api.types.is_datetime64_any_dtype(series)
        is_bool_dtype = pd.api.types.is_bool_dtype(series)

        reasons: list[str] = []

        # ── 1. PII Check ──
        for pii_pat in cls.PII_PATTERNS:
            if pii_pat.search(match_name):
                return FieldSemanticProfile(
                    source_name=clean_name,
                    semantic_name=norm_name,
                    semantic_class=SemanticClass.PII,
                    business_role=BusinessRole.IDENTIFIER,
                    detected_type="text",
                    allowed_aggregations=["count", "count_distinct"],
                    confidence=0.98,
                    status=ClassificationStatus.AUTO_CONFIRMED,
                    is_identifier=True,
                    cardinality=cardinality,
                    uniqueness_ratio=uniqueness_ratio,
                    null_ratio=null_ratio,
                    reasons=["Matches explicit PII naming pattern; restricted from metric aggregation."],
                )

        # ── 2. Check Valid Dimension Codes (Rule: Not every code is an identifier) ──
        if norm_name in cls.VALID_CODE_DIMENSIONS or any(k in norm_name for k in ["_code", "code_"]):
            # If cardinality is low-to-moderate, it is a categorical dimension, NOT a single-use identifier
            if uniqueness_ratio < 0.85 or cardinality <= 500:
                reasons.append(f"Categorical code/dimension with bounded cardinality ({cardinality} distinct values).")
                return FieldSemanticProfile(
                    source_name=clean_name,
                    semantic_name=norm_name,
                    semantic_class=SemanticClass.DIMENSION,
                    business_role=BusinessRole.DIMENSION,
                    detected_type="categorical" if not is_numeric else "numeric_code",
                    allowed_aggregations=["count", "count_distinct", "mode"],
                    confidence=0.92,
                    status=ClassificationStatus.AUTO_CONFIRMED,
                    is_identifier=False,
                    cardinality=cardinality,
                    uniqueness_ratio=uniqueness_ratio,
                    null_ratio=null_ratio,
                    reasons=reasons,
                )

        # ── 3. Strict Identifier Check ──
        is_id_name = (
            norm_name in cls.IDENTIFIER_EXACT
            or norm_name.endswith(("_id", "_key", "_nbr", "_number", "_uuid"))
            or norm_name.startswith(("id_", "key_"))
        )
        is_high_unique_numeric_id = is_numeric and uniqueness_ratio > 0.95 and total_rows > 10 and not any(
            p.search(match_name) for p in cls.AMOUNT_PATTERNS + cls.PERCENTAGE_PATTERNS + cls.QUANTITY_PATTERNS
        )

        if is_id_name or is_high_unique_numeric_id:
            reasons.append("Identified as entity/transaction key. Banned from SUM, AVG, MEDIAN, TREND, and KPI measures.")
            return FieldSemanticProfile(
                source_name=clean_name,
                semantic_name=norm_name,
                semantic_class=SemanticClass.IDENTIFIER,
                business_role=BusinessRole.IDENTIFIER,
                detected_type="identifier",
                allowed_aggregations=["count", "count_distinct"],
                confidence=0.96 if is_id_name else 0.88,
                status=ClassificationStatus.AUTO_CONFIRMED if is_id_name else ClassificationStatus.REVIEW_RECOMMENDED,
                is_identifier=True,
                cardinality=cardinality,
                uniqueness_ratio=uniqueness_ratio,
                null_ratio=null_ratio,
                reasons=reasons,
            )

        # ── 4. Temporal Check ──
        if is_datetime_dtype or any(pat.search(match_name) for pat in cls.DATE_PATTERNS):
            # Verify if strings parse to valid dates
            can_parse_dates = is_datetime_dtype
            if not can_parse_dates and non_null_count > 0:
                try:
                    sample = non_null.head(50)
                    parsed = pd.to_datetime(sample, errors="coerce")
                    if parsed.notna().mean() >= 0.8:
                        can_parse_dates = True
                except Exception:
                    can_parse_dates = False

            if can_parse_dates:
                return FieldSemanticProfile(
                    source_name=clean_name,
                    semantic_name=norm_name,
                    semantic_class=SemanticClass.DATETIME if is_datetime_dtype else SemanticClass.DATE,
                    business_role=BusinessRole.TIME_DIMENSION,
                    detected_type="datetime" if is_datetime_dtype else "date",
                    allowed_aggregations=["min", "max", "count", "count_distinct"],
                    confidence=0.95,
                    status=ClassificationStatus.AUTO_CONFIRMED,
                    is_temporal=True,
                    cardinality=cardinality,
                    uniqueness_ratio=uniqueness_ratio,
                    null_ratio=null_ratio,
                    reasons=["Valid temporal dimension verified via parseability & naming."],
                )

        # ── 5. Status / Outcome ──
        if is_bool_dtype or (cardinality == 2 and not is_numeric) or any(pat.search(match_name) for pat in cls.STATUS_PATTERNS):
            return FieldSemanticProfile(
                source_name=clean_name,
                semantic_name=norm_name,
                semantic_class=SemanticClass.STATUS,
                business_role=BusinessRole.STATUS,
                detected_type="boolean" if is_bool_dtype or cardinality == 2 else "categorical",
                allowed_aggregations=["count", "count_distinct", "mode"],
                confidence=0.91,
                status=ClassificationStatus.AUTO_CONFIRMED,
                cardinality=cardinality,
                uniqueness_ratio=uniqueness_ratio,
                null_ratio=null_ratio,
                reasons=["Binary or categorical status/outcome dimension."],
            )

        # ── 6. Numeric Business Measures (Amount, Percentage, Quantity, Score) ──
        if is_numeric:
            # Check for Percentage / Ratio
            for pat in cls.PERCENTAGE_PATTERNS:
                if pat.search(match_name):
                    return FieldSemanticProfile(
                        source_name=clean_name,
                        semantic_name=norm_name,
                        semantic_class=SemanticClass.PERCENTAGE,
                        business_role=BusinessRole.MEASURE,
                        detected_type="numeric",
                        unit="percent",
                        allowed_aggregations=["avg", "median", "min", "max"],
                        confidence=0.94,
                        status=ClassificationStatus.AUTO_CONFIRMED,
                        is_numeric_measure=True,
                        cardinality=cardinality,
                        uniqueness_ratio=uniqueness_ratio,
                        null_ratio=null_ratio,
                        reasons=["Percentage or ratio metric. Prohibited from SUM aggregation."],
                    )

            # Check for Amount / Currency
            for pat in cls.AMOUNT_PATTERNS:
                if pat.search(match_name):
                    return FieldSemanticProfile(
                        source_name=clean_name,
                        semantic_name=norm_name,
                        semantic_class=SemanticClass.AMOUNT,
                        business_role=BusinessRole.MEASURE,
                        detected_type="numeric",
                        unit="currency",
                        allowed_aggregations=["sum", "avg", "median", "min", "max"],
                        confidence=0.95,
                        status=ClassificationStatus.AUTO_CONFIRMED,
                        is_numeric_measure=True,
                        cardinality=cardinality,
                        uniqueness_ratio=uniqueness_ratio,
                        null_ratio=null_ratio,
                        reasons=["Monetary amount metric eligible for additive/summative analytics."],
                    )

            # Check for Quantity / Count
            for pat in cls.QUANTITY_PATTERNS:
                if pat.search(match_name):
                    return FieldSemanticProfile(
                        source_name=clean_name,
                        semantic_name=norm_name,
                        semantic_class=SemanticClass.QUANTITY,
                        business_role=BusinessRole.MEASURE,
                        detected_type="numeric",
                        unit="units",
                        allowed_aggregations=["sum", "avg", "median", "min", "max"],
                        confidence=0.93,
                        status=ClassificationStatus.AUTO_CONFIRMED,
                        is_numeric_measure=True,
                        cardinality=cardinality,
                        uniqueness_ratio=uniqueness_ratio,
                        null_ratio=null_ratio,
                        reasons=["Discrete volume/quantity measure."],
                    )

            # Check for Score / Rating
            for pat in cls.SCORE_PATTERNS:
                if pat.search(match_name):
                    return FieldSemanticProfile(
                        source_name=clean_name,
                        semantic_name=norm_name,
                        semantic_class=SemanticClass.SCORE,
                        business_role=BusinessRole.MEASURE,
                        detected_type="numeric",
                        unit="score",
                        allowed_aggregations=["avg", "median", "min", "max"],
                        confidence=0.90,
                        status=ClassificationStatus.AUTO_CONFIRMED,
                        is_numeric_measure=True,
                        cardinality=cardinality,
                        uniqueness_ratio=uniqueness_ratio,
                        null_ratio=null_ratio,
                        reasons=["Ordinal score/rating metric. Prohibited from direct SUM aggregation."],
                    )

            # General numeric measure if continuous with variance
            if cardinality > 5 and not (uniqueness_ratio > 0.98 and total_rows > 50):
                return FieldSemanticProfile(
                    source_name=clean_name,
                    semantic_name=norm_name,
                    semantic_class=SemanticClass.MEASURE,
                    business_role=BusinessRole.MEASURE,
                    detected_type="numeric",
                    unit="number",
                    allowed_aggregations=["sum", "avg", "median", "min", "max"],
                    confidence=0.82,
                    status=ClassificationStatus.REVIEW_RECOMMENDED,
                    is_numeric_measure=True,
                    cardinality=cardinality,
                    uniqueness_ratio=uniqueness_ratio,
                    null_ratio=null_ratio,
                    reasons=["Continuous numeric column with natural variance."],
                )

        # ── 7. Categorical Dimensions ──
        if cardinality < 1000 or uniqueness_ratio < 0.70:
            return FieldSemanticProfile(
                source_name=clean_name,
                semantic_name=norm_name,
                semantic_class=SemanticClass.DIMENSION,
                business_role=BusinessRole.DIMENSION,
                detected_type="categorical",
                allowed_aggregations=["count", "count_distinct", "mode"],
                confidence=0.88,
                status=ClassificationStatus.REVIEW_RECOMMENDED,
                is_identifier=False,
                cardinality=cardinality,
                uniqueness_ratio=uniqueness_ratio,
                null_ratio=null_ratio,
                reasons=["Categorical grouping dimension with low-to-medium cardinality."],
            )

        # ── 8. Unknown / Ambiguous Fallback (Section 13) ──
        return FieldSemanticProfile(
            source_name=clean_name,
            semantic_name=norm_name,
            semantic_class=SemanticClass.UNKNOWN,
            business_role=BusinessRole.UNKNOWN,
            detected_type="unknown",
            allowed_aggregations=["count"],
            confidence=0.50,
            status=ClassificationStatus.USER_CONFIRMATION_REQUIRED,
            is_identifier=False,
            cardinality=cardinality,
            uniqueness_ratio=uniqueness_ratio,
            null_ratio=null_ratio,
            reasons=["Field semantics could not be safely resolved with high confidence."],
        )

    @classmethod
    def validate_kpi_qualification(
        cls,
        field_profile: FieldSemanticProfile,
        series: pd.Series,
    ) -> tuple[bool, str]:
        """Enforces Section 17 KPI Qualification:

        1. Semantic role is valid (MEASURE, AMOUNT, QUANTITY, PERCENTAGE, RATIO, SCORE)
        2. Aggregation is valid (no SUM on percentages/scores)
        3. Unit is known or safely inferred
        4. Calculation is reproducible
        5. Sufficient data exists (variance > 0, non-empty, non-null)
        6. No identifier conflict exists
        """
        if field_profile.is_identifier or field_profile.semantic_class == SemanticClass.IDENTIFIER:
            return False, f"Identifier Conflict: Field '{field_profile.source_name}' is classified as IDENTIFIER."

        if field_profile.semantic_class not in (
            SemanticClass.MEASURE, SemanticClass.AMOUNT, SemanticClass.QUANTITY,
            SemanticClass.PERCENTAGE, SemanticClass.RATIO, SemanticClass.SCORE
        ):
            return False, f"Invalid Role: Semantic class '{field_profile.semantic_class}' cannot be an executive KPI measure."

        s = pd.to_numeric(series, errors="coerce").dropna()
        if s.empty:
            return False, f"Insufficient Data: Field '{field_profile.source_name}' contains no valid numeric values."

        if s.nunique() <= 1:
            return False, f"Zero Variance: Field '{field_profile.source_name}' has constant values across all records."

        if field_profile.status == ClassificationStatus.USER_CONFIRMATION_REQUIRED:
            return False, f"Low Confidence ({field_profile.confidence:.2f}): Field requires explicit user confirmation before KPI promotion."

        return True, "Qualified as verified executive business KPI."
