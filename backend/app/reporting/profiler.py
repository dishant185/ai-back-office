from __future__ import annotations

import pandas as pd
from app.reporting.capability_detector import CapabilityDetector
from app.reporting.domain_detector import DomainDetector
from app.reporting.models import DataQuality, DataQualityIssue, DatasetProfile
from app.reporting.semantic_detector import SemanticDetector, normalize_col_name


class DatasetProfiler:
    """Profiles tabular data, assesses data quality, and extracts semantic structures."""

    @classmethod
    def profile(cls, frame: pd.DataFrame) -> tuple[DatasetProfile, DataQuality, pd.DataFrame]:
        row_count = int(len(frame.index))
        col_count = int(len(frame.columns))

        if row_count == 0:
            return (
                DatasetProfile(),
                DataQuality(score=0.0, total_rows=0, total_columns=col_count, issues=[
                    DataQualityIssue(severity="critical", description="The dataset contains zero rows.")
                ]),
                frame.copy(),
            )

        # 1. Semantic Field Detection
        fields = SemanticDetector.detect_all(frame)

        # Create standardized dataframe where columns are mapped to their normalized_name
        # Keep original mapping tracking
        rename_map = {f.source_column: f.normalized_name for f in fields}
        standardized_frame = frame.rename(columns=rename_map).copy()
        standardized_frame = standardized_frame.loc[:, ~standardized_frame.columns.duplicated()].copy()

        # 2. Domain & Capabilities
        domain, domain_conf, secondaries = DomainDetector.detect(fields)
        capabilities = CapabilityDetector.detect(fields)

        # 3. Categorize fields
        numeric_fields = [f.normalized_name for f in fields if f.data_type == "numeric"]
        categorical_fields = [f.normalized_name for f in fields if f.data_type in ("category", "string", "boolean")]
        date_fields = [f.normalized_name for f in fields if f.data_type == "date"]
        identifier_fields = [f.normalized_name for f in fields if f.semantic_role == "id"]

        profile = DatasetProfile(
            row_count=row_count,
            column_count=col_count,
            primary_domain=domain,
            domain_confidence=domain_conf,
            secondary_domains=secondaries,
            fields=fields,
            numeric_fields=numeric_fields,
            categorical_fields=categorical_fields,
            date_fields=date_fields,
            identifier_fields=identifier_fields,
            detected_capabilities=capabilities,
        )

        # 4. Data Quality Audit
        total_cells = row_count * col_count
        missing_cells = int(frame.isna().sum().sum())
        missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0.0

        duplicate_rows = int(frame.duplicated().sum())
        duplicate_pct = (duplicate_rows / row_count * 100) if row_count > 0 else 0.0

        completeness_pct = max(0.0, 100.0 - missing_pct)

        issues: list[DataQualityIssue] = []

        # Missing values check per column
        for col in frame.columns:
            col_missing = int(frame[col].isna().sum())
            if col_missing > 0:
                col_pct = (col_missing / row_count) * 100
                severity = "critical" if col_pct > 30 else ("warning" if col_pct > 5 else "info")
                issues.append(
                    DataQualityIssue(
                        severity=severity,
                        column=str(col),
                        description=f"{col_missing:,} missing values ({col_pct:.1f}% of column)",
                    )
                )

        # Duplicate check
        if duplicate_rows > 0:
            severity = "warning" if duplicate_pct > 5 else "info"
            issues.append(
                DataQualityIssue(
                    severity=severity,
                    description=f"{duplicate_rows:,} duplicate records detected ({duplicate_pct:.1f}% of dataset)",
                )
            )

        # Calculate overall quality score (0 to 100)
        # Deductions: up to 40 for missing cells, up to 30 for duplicates, up to 30 for extreme cardinality / anomalies
        deduction_missing = min(40.0, missing_pct * 1.5)
        deduction_dups = min(30.0, duplicate_pct * 1.0)
        quality_score = max(0.0, round(100.0 - deduction_missing - deduction_dups, 1))

        quality = DataQuality(
            score=quality_score,
            total_rows=row_count,
            total_columns=col_count,
            missing_cells=missing_cells,
            missing_pct=round(missing_pct, 2),
            duplicate_rows=duplicate_rows,
            duplicate_pct=round(duplicate_pct, 2),
            completeness_pct=round(completeness_pct, 2),
            issues=issues,
        )

        return profile, quality, standardized_frame
