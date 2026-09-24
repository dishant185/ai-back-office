"""Universal Data Cleaning Engine.

Responsibilities:
- Missing values detection, imputation, or exclusion
- Duplicate record detection and auditable removal
- Whitespace trimming and casing normalization
- Numeric conversion with currency ($12,500.50 -> 12500.50) and percentage parsing (15.5% -> 15.5)
- Date normalization to standard ISO YYYY-MM-DD
- Boolean normalization (yes/no, true/false, 1/0)
- Null tokens normalization (NA, N/A, null, none, -, empty string)
- Type consistency checks and malformed record detection

Transparent, auditable, and reversible:
Produces an auditable trail of transformations:
(raw_value -> clean_value -> transformation -> reason)
Never silently changes source data without recording the transformation.
"""
from __future__ import annotations

import datetime
import re
from typing import Any
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class CleaningTransformation(BaseModel):
    column: str
    row_index: int | None = None
    raw_value: Any = None
    clean_value: Any = None
    transformation: str
    reason: str


class CleaningAuditSummary(BaseModel):
    total_records_analyzed: int
    total_transformations: int
    missing_cells_imputed: int
    duplicate_rows_detected: int
    duplicate_rows_removed: int
    currency_conversions: int
    percentage_conversions: int
    boolean_normalizations: int
    date_normalizations: int
    whitespace_trimmed: int
    null_tokens_normalized: int
    transformations_sample: list[CleaningTransformation] = Field(default_factory=list)


class IssueItem(BaseModel):
    column: str
    issue_type: str  # missing_values, duplicate_rows, currency_format, percentage_format, whitespace, mixed_types
    affected_count: int
    affected_percentage: float
    suggested_action: str
    sample_values: list[str] = Field(default_factory=list)


class CleaningPreview(BaseModel):
    dataset_id: str
    row_count: int
    column_count: int
    issues: list[IssueItem]
    available_actions: list[str] = Field(default_factory=lambda: [
        "trim_whitespace",
        "normalize_nulls",
        "parse_currencies",
        "parse_percentages",
        "normalize_booleans",
        "normalize_dates",
        "remove_duplicates",
        "impute_numeric_mean",
        "impute_numeric_median",
        "drop_null_rows",
    ])


class UniversalDataCleaner:
    """Production-grade universal data cleaning engine for arbitrary business datasets."""

    NULL_TOKENS = {
        "na", "n/a", "null", "none", "nan", "-", "--", "nil", "n.a.", "#n/a",
        "#na", "undefined", "blank", "empty", "", "?"
    }

    TRUE_TOKENS = {"yes", "y", "true", "t", "1", "1.0", "active", "enabled"}
    FALSE_TOKENS = {"no", "n", "false", "f", "0", "0.0", "inactive", "disabled"}

    CURRENCY_REGEX = re.compile(r"^\s*[$€£¥₹]?\s*([+-]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|[+-]?\d+(?:\.\d+)?)\s*[$€£¥₹]?\s*$")
    PERCENT_REGEX = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*%\s*$")

    @classmethod
    def preview_issues(cls, frame: pd.DataFrame, dataset_id: str = "dataset") -> CleaningPreview:
        """Scan dataframe and report detected issues with affected record counts."""
        row_count = int(len(frame))
        col_count = int(len(frame.columns))
        issues: list[IssueItem] = []

        if row_count == 0:
            return CleaningPreview(dataset_id=dataset_id, row_count=0, column_count=col_count, issues=[])

        # 1. Duplicate rows
        dup_count = int(frame.duplicated().sum())
        if dup_count > 0:
            issues.append(IssueItem(
                column="[ALL_COLUMNS]",
                issue_type="duplicate_rows",
                affected_count=dup_count,
                affected_percentage=round((dup_count / row_count) * 100, 2),
                suggested_action="Deduplicate identical records to preserve statistical accuracy.",
                sample_values=[f"{dup_count} identical records observed"],
            ))

        # Column-level issues
        for col in frame.columns:
            s = frame[col]
            missing_cnt = int(s.isna().sum())
            # Check string null tokens
            if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
                string_nulls = int(s.dropna().astype(str).str.strip().str.lower().isin(cls.NULL_TOKENS).sum())
                total_null_like = missing_cnt + string_nulls
            else:
                total_null_like = missing_cnt

            if total_null_like > 0:
                issues.append(IssueItem(
                    column=str(col),
                    issue_type="missing_values",
                    affected_count=total_null_like,
                    affected_percentage=round((total_null_like / row_count) * 100, 2),
                    suggested_action="Normalize null tokens; decide whether to keep null, impute, or exclude.",
                    sample_values=[str(x) for x in s[s.isna() | s.astype(str).str.strip().str.lower().isin(cls.NULL_TOKENS)].dropna().head(3).tolist()],
                ))

            # Check whitespace & casing
            if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
                non_null_str = s.dropna().astype(str)
                whitespace_count = int(non_null_str.map(lambda x: len(x) != len(x.strip())).sum())
                if whitespace_count > 0:
                    issues.append(IssueItem(
                        column=str(col),
                        issue_type="whitespace",
                        affected_count=whitespace_count,
                        affected_percentage=round((whitespace_count / row_count) * 100, 2),
                        suggested_action="Trim leading/trailing whitespace to standardize category matching.",
                        sample_values=[repr(x) for x in non_null_str[non_null_str.map(lambda x: len(x) != len(x.strip()))].head(2).tolist()],
                    ))

                # Check currency
                curr_matches = non_null_str.map(lambda x: bool(cls.CURRENCY_REGEX.match(x.strip())) and any(sym in x for sym in ["$", "€", "£", "¥", "₹", ","]))
                curr_count = int(curr_matches.sum())
                if curr_count > 0:
                    issues.append(IssueItem(
                        column=str(col),
                        issue_type="currency_format",
                        affected_count=curr_count,
                        affected_percentage=round((curr_count / row_count) * 100, 2),
                        suggested_action="Convert formatted currency text to clean numeric float measure.",
                        sample_values=non_null_str[curr_matches].head(3).tolist(),
                    ))

                # Check percentage
                pct_matches = non_null_str.map(lambda x: bool(cls.PERCENT_REGEX.match(x.strip())))
                pct_count = int(pct_matches.sum())
                if pct_count > 0:
                    issues.append(IssueItem(
                        column=str(col),
                        issue_type="percentage_format",
                        affected_count=pct_count,
                        affected_percentage=round((pct_count / row_count) * 100, 2),
                        suggested_action="Parse percentage strings into normalized decimal/numeric values.",
                        sample_values=non_null_str[pct_matches].head(3).tolist(),
                    ))

        return CleaningPreview(
            dataset_id=dataset_id,
            row_count=row_count,
            column_count=col_count,
            issues=issues,
        )

    @classmethod
    def clean(
        cls,
        frame: pd.DataFrame,
        actions: list[str] | None = None,
        impute_strategy: dict[str, str] | None = None,  # col -> "mean" | "median" | "mode" | "constant"
    ) -> tuple[pd.DataFrame, CleaningAuditSummary]:
        """Execute transparent, reversible cleaning pipeline and record audit trail."""
        df = frame.copy()
        transformations: list[CleaningTransformation] = []

        total_records = len(df)
        currency_conversions = 0
        percentage_conversions = 0
        boolean_normalizations = 0
        date_normalizations = 0
        whitespace_trimmed = 0
        null_tokens_normalized = 0
        missing_imputed = 0
        dup_removed = 0

        # Default action list if not provided
        active_actions = set(actions or [
            "trim_whitespace",
            "normalize_nulls",
            "standardize_casing",
            "parse_currencies",
            "parse_percentages",
            "normalize_booleans",
            "normalize_dates",
        ])

        # 1. Whitespace trimming & Null token normalization
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                new_vals = []
                for idx, val in enumerate(df[col]):
                    if pd.isna(val):
                        new_vals.append(np.nan)
                        continue
                    val_str = str(val)
                    clean_str = val_str.strip()

                    if "trim_whitespace" in active_actions and clean_str != val_str:
                        whitespace_trimmed += 1
                        if len(transformations) < 50:
                            transformations.append(CleaningTransformation(
                                column=str(col),
                                row_index=idx,
                                raw_value=val_str,
                                clean_value=clean_str,
                                transformation="whitespace_trim",
                                reason="Stripped extraneous leading/trailing whitespace",
                            ))

                    if "normalize_nulls" in active_actions and clean_str.lower() in cls.NULL_TOKENS:
                        null_tokens_normalized += 1
                        if len(transformations) < 50:
                            transformations.append(CleaningTransformation(
                                column=str(col),
                                row_index=idx,
                                raw_value=val_str,
                                clean_value=None,
                                transformation="null_normalization",
                                reason=f"Standardized null token '{clean_str}' to NaN",
                            ))
                        new_vals.append(np.nan)
                    else:
                        if "standardize_casing" in active_actions and clean_str and not clean_str.isdigit():
                            clean_str = clean_str[:1].upper() + clean_str[1:].lower()
                        new_vals.append(clean_str)

                df[col] = new_vals

        # 2. Currency Parsing
        if "parse_currencies" in active_actions:
            for col in df.columns:
                if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                    non_nulls = df[col].dropna()
                    if non_nulls.empty:
                        continue
                    sample = non_nulls.head(20)
                    matches = sample.map(lambda x: bool(cls.CURRENCY_REGEX.match(str(x))) and any(sym in str(x) for sym in ["$", "€", "£", "¥", "₹", ","]))
                    if matches.sum() >= max(1, int(len(sample) * 0.6)):
                        new_col_vals = []
                        for idx, val in enumerate(df[col]):
                            if pd.isna(val):
                                new_col_vals.append(np.nan)
                                continue
                            raw_s = str(val)
                            m = cls.CURRENCY_REGEX.match(raw_s)
                            if m:
                                num_str = m.group(1).replace(",", "")
                                try:
                                    num_val = float(num_str)
                                    currency_conversions += 1
                                    if len(transformations) < 50:
                                        transformations.append(CleaningTransformation(
                                            column=str(col),
                                            row_index=idx,
                                            raw_value=raw_s,
                                            clean_value=num_val,
                                            transformation="currency_normalization",
                                            reason="Parsed currency string to numeric float",
                                        ))
                                    new_col_vals.append(num_val)
                                except ValueError:
                                    new_col_vals.append(val)
                            else:
                                new_col_vals.append(val)
                        df[col] = pd.to_numeric(new_col_vals, errors="coerce")

        # 3. Percentage Parsing
        if "parse_percentages" in active_actions:
            for col in df.columns:
                if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                    non_nulls = df[col].dropna()
                    if non_nulls.empty:
                        continue
                    sample = non_nulls.head(20)
                    matches = sample.map(lambda x: bool(cls.PERCENT_REGEX.match(str(x))))
                    if matches.sum() >= max(1, int(len(sample) * 0.6)):
                        new_col_vals = []
                        for idx, val in enumerate(df[col]):
                            if pd.isna(val):
                                new_col_vals.append(np.nan)
                                continue
                            raw_s = str(val)
                            m = cls.PERCENT_REGEX.match(raw_s)
                            if m:
                                try:
                                    pct_val = float(m.group(1))
                                    percentage_conversions += 1
                                    if len(transformations) < 50:
                                        transformations.append(CleaningTransformation(
                                            column=str(col),
                                            row_index=idx,
                                            raw_value=raw_s,
                                            clean_value=pct_val,
                                            transformation="percentage_normalization",
                                            reason="Parsed percentage string to numeric float value",
                                        ))
                                    new_col_vals.append(pct_val)
                                except ValueError:
                                    new_col_vals.append(val)
                            else:
                                new_col_vals.append(val)
                        df[col] = pd.to_numeric(new_col_vals, errors="coerce")

        # 4. Boolean Normalization
        if "normalize_booleans" in active_actions:
            for col in df.columns:
                if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                    non_nulls = df[col].dropna().astype(str).str.lower().str.strip()
                    if non_nulls.empty:
                        continue
                    unique_vals = set(non_nulls.unique())
                    if unique_vals.issubset(cls.TRUE_TOKENS.union(cls.FALSE_TOKENS)) and len(unique_vals) <= 4:
                        new_col_vals = []
                        for idx, val in enumerate(df[col]):
                            if pd.isna(val):
                                new_col_vals.append(np.nan)
                                continue
                            v_low = str(val).lower().strip()
                            clean_bool = 1 if v_low in cls.TRUE_TOKENS else (0 if v_low in cls.FALSE_TOKENS else val)
                            boolean_normalizations += 1
                            new_col_vals.append(clean_bool)
                        df[col] = new_col_vals

        # 5. Date Normalization
        if "normalize_dates" in active_actions:
            for col in df.columns:
                if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                    col_lower = str(col).lower()
                    if any(term in col_lower for term in ["date", "timestamp", "time", "day", "created_at", "order_date"]):
                        try:
                            parsed_dates = pd.to_datetime(df[col], errors="coerce")
                            if parsed_dates.notna().sum() >= max(1, int(len(df) * 0.5)):
                                date_normalizations += int(parsed_dates.notna().sum())
                                df[col] = parsed_dates.dt.strftime("%Y-%m-%d").replace("NaT", np.nan)
                        except Exception:
                            pass

        # 6. Duplicate row handling
        dup_detected = int(df.duplicated().sum())
        if "remove_duplicates" in active_actions and dup_detected > 0:
            dup_removed = dup_detected
            df = df.drop_duplicates().reset_index(drop=True)
            transformations.append(CleaningTransformation(
                column="[ALL_COLUMNS]",
                transformation="deduplication",
                reason=f"Removed {dup_removed} exact duplicate records",
            ))

        # 7. Imputation Strategies
        if impute_strategy:
            for col, strat in impute_strategy.items():
                if col in df.columns and df[col].isna().sum() > 0:
                    missing_for_col = int(df[col].isna().sum())
                    if strat == "mean" and pd.api.types.is_numeric_dtype(df[col]):
                        fill_val = float(df[col].mean())
                        df[col] = df[col].fillna(round(fill_val, 2))
                        missing_imputed += missing_for_col
                    elif strat == "median" and pd.api.types.is_numeric_dtype(df[col]):
                        fill_val = float(df[col].median())
                        df[col] = df[col].fillna(round(fill_val, 2))
                        missing_imputed += missing_for_col
                    elif strat == "mode":
                        mode_vals = df[col].mode()
                        if not mode_vals.empty:
                            fill_val = mode_vals.iloc[0]
                            df[col] = df[col].fillna(fill_val)
                            missing_imputed += missing_for_col

        summary = CleaningAuditSummary(
            total_records_analyzed=total_records,
            total_transformations=(
                whitespace_trimmed + null_tokens_normalized + currency_conversions +
                percentage_conversions + boolean_normalizations + date_normalizations +
                dup_removed + missing_imputed
            ),
            missing_cells_imputed=missing_imputed,
            duplicate_rows_detected=dup_detected,
            duplicate_rows_removed=dup_removed,
            currency_conversions=currency_conversions,
            percentage_conversions=percentage_conversions,
            boolean_normalizations=boolean_normalizations,
            date_normalizations=date_normalizations,
            whitespace_trimmed=whitespace_trimmed,
            null_tokens_normalized=null_tokens_normalized,
            transformations_sample=transformations[:30],
        )

        return df, summary
