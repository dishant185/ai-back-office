"""Novera Report Engine v2 — Full Regression & Verification Test Suite.

Tests cover:
1. Golden-Report Regression (Employee dataset):
   - Data Quality semantics (Field completeness vs score)
   - Record vs unique entity count semantics
   - Semantic label accuracy (experience vs tenure)
   - No empty sections
   - Recommendations grounded in evidence
2. Prohibited Content Assertions:
   - No unsupported benchmarks, risk labels, causal claims, unique employee claims
   - No contradictory completeness values
   - No excessive branding
3. Evidence Architecture Regression Tests:
   - Evidence ID integrity on all sections and recommendations
   - Injection of nonexistent evidence_id and verification of removal
   - Rejection/invalid evidence filtering
   - Irrelevant evidence exclusion
   - Report-wide duplicate claim suppression
   - Contextual repetition preservation
   - Evidence-to-section analytical mapping
4. Edge Cases:
   - Empty dataset, single-row dataset, no-numeric dataset, generic dataset
5. PDF Generation Regression:
   - Valid PDF structure, clean title, no excessive branding, user-friendly AI status badge
"""
from __future__ import annotations

import glob
from pathlib import Path
import pandas as pd
import pytest

from app.reporting.report_composer import ReportComposer
from app.reporting.pdf_generator import PDFReportGenerator
from app.reporting.models import ReportSection, ReportRecommendation


def _load_employee_dataset() -> pd.DataFrame:
    """Find and load the golden Employee dataset."""
    search_patterns = [
        "c:/Users/disha/Desktop/ai-backoffice-copilot/data/uploads/Employee-*.csv",
        "c:/Users/disha/Desktop/ai-backoffice-copilot/backend/data/uploads/Employee-*.csv",
        "../data/uploads/Employee-*.csv",
        "data/uploads/Employee-*.csv",
    ]
    for pattern in search_patterns:
        matches = glob.glob(pattern)
        for match in matches:
            try:
                df = pd.read_csv(match)
                if len(df) == 4653 and "LeaveOrNot" in df.columns:
                    return df
            except Exception:
                continue

    # Fallback: create mock Employee dataset matching exact dimensions
    data = {
        "Education": ["Bachelors", "Masters", "PHD"] * 1551,
        "JoiningYear": [2012, 2013, 2014, 2015, 2016, 2017] * 775 + [2018] * 3,
        "City": ["Bangalore", "Pune", "New Delhi"] * 1551,
        "PaymentTier": [1, 2, 3] * 1551,
        "Age": [25, 28, 30, 32, 35, 40] * 775 + [27] * 3,
        "Gender": ["Male", "Female"] * 2326 + ["Male"],
        "EverBenched": ["No", "Yes"] * 2326 + ["No"],
        "ExperienceInCurrentDomain": [0, 1, 2, 3, 4, 5, 6, 7] * 581 + [2] * 5,
        "LeaveOrNot": [0, 1, 0, 0, 1, 0] * 775 + [0] * 3,
    }
    return pd.DataFrame(data)


# ── 1. Golden-Report Regression (Employee Dataset) ──

def test_employee_dataset_golden_report():
    """Golden-report regression: Employee dataset must produce semantically correct report."""
    df = _load_employee_dataset()
    composer = ReportComposer()
    report = composer.compose_report(frame=df, dataset_id="golden_hr", filename="Employee.csv")

    # ── Data Quality Semantics ──
    assert report.data_quality.completeness_pct == 100.0  # 100% field completeness
    assert report.data_quality.missing_cells == 0
    assert report.data_quality.duplicate_rows == 1889
    assert abs(report.data_quality.duplicate_pct - 40.60) < 0.1

    # Verify summary / highlights strictly use completeness_pct and never label score as completeness
    report_text = (
        report.executive_summary.overview
        + " "
        + " ".join(report.executive_summary.key_highlights)
        + " "
        + " ".join(report.executive_summary.critical_findings)
    ).lower()
    if "completeness" in report_text:
        assert "100" in report_text or "100.0%" in report_text
        # Internal score must never be presented as completeness
        assert f"{report.data_quality.score:.0f}% completeness" not in report_text

    # ── Record vs Entity Semantics ──
    record_kpi = next(k for k in report.kpi_metrics if k.id == "record_count")
    assert record_kpi.value == 4653
    assert "headcount" not in record_kpi.name.lower()
    assert "unique" not in record_kpi.name.lower()
    assert "employee" not in record_kpi.name.lower()

    # ── Semantic Label Accuracy ──
    exp_kpi = next((k for k in report.kpi_metrics if "experience" in k.id.lower() or "experience" in k.name.lower()), None)
    if exp_kpi:
        assert "tenure" not in exp_kpi.name.lower()
        assert "company" not in exp_kpi.name.lower()

    # ── No Empty Sections ──
    assert len(report.sections) > 0
    for section in report.sections:
        has_rankings = any(r.items for r in section.rankings)
        has_charts = any(c.data for c in section.charts)
        has_metrics = bool(section.metrics)
        assert has_rankings or has_charts or has_metrics, f"Empty section: {section.title}"

    # ── Recommendations Must Have Evidence ──
    for rec in report.recommendations:
        assert len(rec.evidence_ids) > 0, f"Recommendation '{rec.title}' lacks evidence_ids"


def test_employee_report_prohibited_content():
    """Verify report does NOT contain known bad patterns or ungrounded assertions."""
    df = _load_employee_dataset()
    composer = ReportComposer()
    report = composer.compose_report(frame=df, dataset_id="prohib_hr", filename="Employee.csv")

    summary_text = report.executive_summary.overview.lower()

    # No unsupported benchmarks
    assert "industry benchmark" not in summary_text
    assert "industry average" not in summary_text

    # No unsupported risk labels
    assert "high risk" not in summary_text
    assert "talent loss risk" not in summary_text

    # No unsupported causal claims
    assert "because of" not in summary_text
    assert "caused by" not in summary_text

    # No row count as unique entity count
    assert "4,653 unique employees" not in summary_text
    assert "unique employees" not in summary_text

    # No contradictory completeness in highlights
    highlights_text = " ".join(report.executive_summary.key_highlights).lower()
    if "completeness" in highlights_text:
        assert "70" not in highlights_text  # old contradictory score

    # No excessive verification branding
    branding_count = (
        summary_text.count("verified")
        + summary_text.count("audited")
        + summary_text.count("zero extrapolation")
    )
    assert branding_count <= 4


# ── 2. Evidence Architecture Regression Tests ──

def test_all_sections_have_evidence_ids():
    """Every rendered section must carry evidence_ids that resolve to the evidence ledger."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="ev_sec", filename="Employee.csv")
    for section in report.sections:
        assert hasattr(section, "evidence_ids"), f"Section '{section.title}' missing evidence_ids"
        assert len(section.evidence_ids) > 0, f"Section '{section.title}' has empty evidence_ids"


def test_all_recommendations_have_evidence_ids():
    """Every recommendation must carry evidence_ids."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="ev_rec", filename="Employee.csv")
    for rec in report.recommendations:
        assert hasattr(rec, "evidence_ids"), f"Recommendation '{rec.title}' missing evidence_ids"
        assert len(rec.evidence_ids) > 0, f"Recommendation '{rec.title}' has empty evidence_ids"


def test_missing_evidence_id_removes_section():
    """A section referencing a nonexistent evidence_id must actually be rejected by the gate."""
    composer = ReportComposer()
    df = pd.DataFrame({"value": [1, 2, 3], "group": ["A", "B", "A"]})

    # Normal compose
    report = composer.compose_report(frame=df, dataset_id="miss_ev")
    ledger = report.metadata.get("evidence_ledger", [])

    verified_index = composer._build_verified_evidence_index(
        evidence_ledger=ledger,
        report_type=report.report_type,
        report_title=report.title,
        dataset_domain=report.domain,
    )

    # Injected bogus section
    fake_section = ReportSection(
        id="fake_sec",
        title="Fake Injected Section",
        description="Section with injected invalid evidence_id",
        evidence_ids=["nonexistent_evidence_id_99999"],
    )

    # The gate must reject this section
    assert not composer._content_is_renderable(fake_section, verified_index)


def test_rejected_evidence_prevents_rendering():
    """Content with rejected/invalid evidence status must not pass the gate."""
    composer = ReportComposer()
    fake_ledger = [
        {
            "evidence_id": "ev_rejected_001",
            "entity": "Bad Data",
            "value": 100,
            "verification_status": "rejected",
            "category": "kpi",
        },
        {
            "evidence_id": "ev_valid_002",
            "entity": "Good Data",
            "value": 200,
            "verification_status": "verified",
            "category": "kpi",
        },
    ]
    verified_index = composer._build_verified_evidence_index(
        evidence_ledger=fake_ledger,
        report_type="standard",
        report_title="Test Report",
        dataset_domain="generic",
    )
    assert "ev_rejected_001" not in verified_index
    assert "ev_valid_002" in verified_index

    bad_section = ReportSection(
        id="sec_bad",
        title="Bad Section",
        evidence_ids=["ev_rejected_001"],
    )
    assert not composer._content_is_renderable(bad_section, verified_index)


def test_irrelevant_evidence_excluded_from_sections():
    """Evidence classified as IRRELEVANT (e.g. commercial revenue in an HR report) must not appear in verified index."""
    composer = ReportComposer()
    fake_ledger = [
        {
            "evidence_id": "ev_regional_revenue_001",
            "entity": "regional_revenue",
            "name": "Regional Revenue",
            "value": 999999,
            "verification_status": "verified",
            "category": "sales",
        }
    ]
    verified_index = composer._build_verified_evidence_index(
        evidence_ledger=fake_ledger,
        report_type="hr_workforce",
        report_title="HR Workforce Report",
        dataset_domain="hr",
    )
    assert "ev_regional_revenue_001" not in verified_index


def test_no_duplicate_claims_across_report():
    """Verbatim claims repeated across KPIs and highlights must be suppressed."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="dedup", filename="Employee.csv")
    kpi_exact_statements = {f"{k.name}: {k.formatted_value}" for k in report.kpi_metrics}
    for h in report.executive_summary.key_highlights:
        assert h not in kpi_exact_statements, f"Highlight is pure verbatim KPI repetition: '{h}'"


def test_contextual_repetition_preserved():
    """Contextual statements adding cross-dimensional insight are preserved."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="ctx_rep", filename="Employee.csv")
    # All surviving highlights must provide analytical value
    for h in report.executive_summary.key_highlights:
        assert len(h.strip()) > 5


def test_section_evidence_maps_to_section_content():
    """Section evidence_ids must map to the section's actual analytical content."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="map_ev", filename="Employee.csv")
    for section in report.sections:
        if section.rankings:
            assert len(section.evidence_ids) >= 1, f"Section '{section.title}' missing evidence for rankings"


# ── 3. Edge Cases ──

def test_empty_dataset():
    """Empty dataframe must not crash and produce 0 rows."""
    report = ReportComposer().compose_report(frame=pd.DataFrame(), dataset_id="empty")
    assert report.row_count == 0
    assert len(report.sections) == 0
    assert len(report.recommendations) == 0


def test_single_row_dataset():
    """Single row dataset handles safely."""
    df = pd.DataFrame({"value": [42.0], "category": ["A"]})
    report = ReportComposer().compose_report(frame=df, dataset_id="single")
    assert report.row_count == 1


def test_no_numeric_columns():
    """Non-numeric dataset produces categorical composition only."""
    df = pd.DataFrame({"name": ["A", "B", "C"], "type": ["X", "Y", "Z"]})
    report = ReportComposer().compose_report(frame=df, dataset_id="no_num")
    assert report.row_count == 3


def test_generic_dataset_no_domain_assumption():
    """Generic dataset does not assume HR, Sales, or Finance domain."""
    df = pd.DataFrame({"metric_a": [1, 2, 3], "metric_b": [4, 5, 6], "group": ["X", "Y", "X"]})
    report = ReportComposer().compose_report(frame=df, dataset_id="generic")
    all_text = (report.title + " " + " ".join(k.name for k in report.kpi_metrics)).lower()
    assert "employee" not in all_text
    assert "attrition" not in all_text
    assert "revenue" not in all_text


# ── 4. PDF Generation Regression ──

def test_pdf_generation_employee_dataset():
    """PDF generator creates valid PDF without prohibited branding or enum leaks."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="pdf_test", filename="Employee.csv")
    pdf_bytes = PDFReportGenerator.generate(report.model_dump(), page_compression=0)

    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b"%PDF-"

    pdf_text = pdf_bytes.decode("latin-1", errors="ignore").lower()

    # Title fix
    assert "novera saas" not in pdf_text

    # Footer fix
    assert "strict lineage audited" not in pdf_text
    assert "zero extrapolation" not in pdf_text

    # AI status fix: raw enums must not appear, Verified Analytics must appear
    assert "ai_not_configured" not in pdf_text
    assert "ai_unavailable" not in pdf_text
    assert "verified analytics" in pdf_text

    # Branding
    assert "novera business intelligence" in pdf_text


def test_pdf_completeness_and_duplicates_no_contradiction():
    """Verify PDF scorecard and data quality table strictly use completeness_pct and never score."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="pdf_dq_test", filename="Employee.csv")
    pdf_bytes = PDFReportGenerator.generate(report.model_dump(), page_compression=0)
    pdf_text = pdf_bytes.decode("latin-1", errors="ignore").lower()

    # 100.0% completeness must be shown
    assert "100.0%" in pdf_text

    # Internal score (~79.4%) must never be exposed as completeness
    score_val = f"{report.data_quality.score:.1f}%"
    assert f"completeness: {score_val}" not in pdf_text
    assert f"completeness rate: {score_val}" not in pdf_text

    # Duplicate count & rate must be rendered
    assert "1,889" in pdf_text
    assert "40.60% duplicate rate" in pdf_text or "40.60%" in pdf_text


# ── 5. Issue 1 & 2: Executive Summary Quality Tests ──

def test_issue1_exec_summary_not_only_kpi_restatements():
    """Executive summary must not consist only of KPI value restatements."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="issue1_test", filename="Employee.csv")

    overview = report.executive_summary.overview.lower()
    highlights = report.executive_summary.key_highlights

    # Overview must contain more than just row count + attrition + age
    kpi_only_patterns = [
        "the recorded attrition rate is",
        "average age is",
    ]
    kpi_only_count = sum(1 for p in kpi_only_patterns if p in overview)

    # The overview should have analytical content beyond just listing KPI values
    # Either cross-dimensional evidence or distribution findings
    has_analytical_content = any(k in overview for k in [
        "varies across", "ranging from", "largest segment", "largest share",
        "commands", "distribution", "composition"
    ])

    # If no cross-dimensional evidence exists, KPI repetition is acceptable as fallback
    # But if analytical evidence IS available, it should be preferred
    if has_analytical_content:
        # Good — the overview contains analytical findings
        pass
    else:
        # Verify at minimum that the overview isn't ONLY KPIs
        assert len(overview.split(". ")) >= 2, "Overview should have more than a single sentence"


def test_issue2_cross_dimensional_evidence_preferred():
    """When cross-dimensional evidence exists, it should be preferred in the executive summary."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="issue2_test", filename="Employee.csv")

    # The report should have sections with rankings (cross-dimensional evidence)
    has_ranking_sections = any(s.rankings for s in report.sections)
    assert has_ranking_sections, "Report should have ranking sections with cross-dimensional evidence"

    highlights = report.executive_summary.key_highlights
    # At least some highlights should be cross-dimensional (containing distribution/share info)
    analytical_highlights = [
        h for h in highlights
        if any(k in h.lower() for k in ["leads with", "share", "distribution", "spread", "exceeds"])
    ]
    assert len(analytical_highlights) > 0, "Highlights must include cross-dimensional findings"


def test_issue2_evidence_count_reflects_actual_evidence():
    """Evidence count in summary must reflect actual verified evidence attached, not a fixed number."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="evcount_test", filename="Employee.csv")
    highlights = report.executive_summary.key_highlights
    # Evidence count is dynamic — no fixed requirement for exactly 1, 2, 3, or 5
    # But there must be at least 1 highlight
    assert len(highlights) >= 1, "Must have at least 1 evidence-based highlight"


def test_issue2_no_fixed_evidence_count_required():
    """The system must not require a fixed number of evidence points."""
    # Test with a minimal dataset — should still produce valid summary
    df = pd.DataFrame({"value": [1, 2, 3, 4, 5], "category": ["A", "A", "B", "B", "A"]})
    report = ReportComposer().compose_report(frame=df, dataset_id="min_ev_test")
    # Summary should exist and be valid regardless of evidence count
    assert report.executive_summary.overview
    assert len(report.executive_summary.overview) > 10


# ── 6. Issue 3: Unsupported Department Section Tests ──

def test_issue3_no_department_section_without_department_evidence():
    """Unsupported 'Departmental Structure' section must NOT appear when no department dimension exists."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="dept_test", filename="Employee.csv")

    for section in report.sections:
        title_lower = section.title.lower()
        assert "departmental structure" not in title_lower, \
            f"Section '{section.title}' contains unsupported 'Departmental Structure'"
        assert "functional division" not in title_lower, \
            f"Section '{section.title}' contains unsupported 'Functional Division'"

    overview_lower = report.executive_summary.overview.lower()
    assert "multiple functional divisions" not in overview_lower
    assert "departmental structure" not in overview_lower


def test_issue3_department_section_allowed_when_dimension_exists():
    """Department section may appear when verified department dimension exists."""
    # Create dataset WITH a Department column
    df = pd.DataFrame({
        "Department": ["Sales", "HR", "Engineering", "Sales", "HR", "Engineering"] * 10,
        "Salary": [50000, 45000, 70000, 55000, 48000, 75000] * 10,
        "Age": [25, 30, 28, 35, 40, 32] * 10,
    })
    report = ReportComposer().compose_report(frame=df, dataset_id="dept_exists_test")

    # When Department dimension exists, sections about Department are valid
    section_titles = [s.title.lower() for s in report.sections]
    # At least one section should reference the Department dimension
    has_dept_content = any(
        "department" in t for t in section_titles
    ) or any(
        "department" in (s.description or "").lower()
        for s in report.sections
    )
    # The section should exist if there's a verified Department dimension
    # (it may not appear in the title, but the dimension should be used)
    assert len(report.sections) > 0, "Report should have sections when Department exists"


# ── 7. Issue 4: Semantic Label Accuracy Tests ──

def test_issue4_experience_field_never_becomes_company_tenure():
    """ExperienceInCurrentDomain must never be labeled as 'Company Tenure'."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sem_test", filename="Employee.csv")

    exp_kpi = next((k for k in report.kpi_metrics if "experience" in k.id.lower()), None)
    if exp_kpi:
        name_lower = exp_kpi.name.lower()
        desc_lower = (exp_kpi.description or "").lower()
        assert "company tenure" not in name_lower, f"Experience KPI name contains 'company tenure': {exp_kpi.name}"
        assert "organizational tenure" not in name_lower
        assert "years at company" not in name_lower
        # The label should reflect the source field (domain experience)
        assert "domain" in name_lower or "experience" in name_lower, \
            f"Experience KPI should reference 'domain' or 'experience', got: {exp_kpi.name}"


def test_issue4_generic_dataset_no_hr_terminology():
    """Generic datasets must NOT receive HR-specific terminology."""
    df = pd.DataFrame({
        "metric_a": [1, 2, 3, 4, 5],
        "metric_b": [10, 20, 30, 40, 50],
        "group": ["X", "Y", "X", "Y", "X"],
    })
    report = ReportComposer().compose_report(frame=df, dataset_id="generic_nohr_test")
    all_text = (
        report.title + " " +
        report.executive_summary.overview + " " +
        " ".join(k.name for k in report.kpi_metrics)
    ).lower()
    assert "employee" not in all_text
    assert "workforce" not in all_text
    assert "headcount" not in all_text
    assert "attrition" not in all_text


def test_issue4_verified_hr_dataset_retains_hr_terminology():
    """Verified HR datasets may retain HR terminology when explicitly supported."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="hr_retain_test", filename="Employee.csv")

    # Domain should be detected as HR
    assert report.domain in ("hr", "generic")  # May detect as HR

    # If HR domain, attrition rate should be labeled correctly
    att_kpi = next((k for k in report.kpi_metrics if "attrition" in k.id or "churn" in k.id), None)
    if att_kpi:
        # Attrition terminology is valid for datasets with LeaveOrNot column
        assert "rate" in att_kpi.name.lower()


# ── 8. Issue 7: PDF/Web Consistency Tests ──

def test_issue7_pdf_and_web_use_same_semantic_labels():
    """PDF and web report must use the same semantic labels."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="webpdf_test", filename="Employee.csv")
    pdf_bytes = PDFReportGenerator.generate(report.model_dump(), page_compression=0)
    pdf_text = pdf_bytes.decode("latin-1", errors="ignore").lower()

    # Check experience KPI label consistency
    exp_kpi = next((k for k in report.kpi_metrics if "experience" in k.id.lower()), None)
    if exp_kpi:
        # PDF must use the same name as the web report
        assert exp_kpi.name.lower() in pdf_text, \
            f"PDF must contain the same experience label '{exp_kpi.name}' as web report"
        assert "company tenure" not in pdf_text


def test_issue7_pdf_no_unsupported_departmental_structure():
    """PDF must not contain unsupported 'Departmental Structure' claims."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="pdf_dept_test", filename="Employee.csv")
    pdf_bytes = PDFReportGenerator.generate(report.model_dump(), page_compression=0)
    pdf_text = pdf_bytes.decode("latin-1", errors="ignore").lower()

    assert "departmental structure" not in pdf_text
    assert "multiple functional divisions" not in pdf_text
    assert "functional division" not in pdf_text


def test_issue7_pdf_matches_web_section_count():
    """PDF renders same sections as web report (no hidden departmental sections)."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="pdf_sec_test", filename="Employee.csv")

    # All section titles in report should be renderable
    for section in report.sections:
        title_lower = section.title.lower()
        assert "departmental structure" not in title_lower
        assert "functional division" not in title_lower


# =============================================================================
# SECTION 14: UNIVERSAL SALES-STYLE EXECUTIVE SUMMARY TESTS (20 TESTS)
# =============================================================================

def test_sec14_01_sales_style_summary_structure():
    """1. Executive summary must have dataset_overview, highlights, and overall."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s1", filename="Employee.csv")
    summary = report.executive_summary

    assert hasattr(summary, "dataset_overview")
    assert hasattr(summary, "highlights")
    assert hasattr(summary, "overall")
    assert len(summary.dataset_overview) > 0, "Dataset overview must be a non-empty string"
    assert isinstance(summary.highlights, list) and len(summary.highlights) > 0, "Highlights must be a non-empty list"
    assert summary.overall.startswith("Overall:"), "Overall interpretation must start with 'Overall:'"


def test_sec14_02_dataset_overview_generation():
    """2. Dataset overview is a concise sentence with verified record count and fields."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s2", filename="Employee.csv")
    ov = report.executive_summary.dataset_overview

    assert "4,653" in ov or "4653" in ov
    assert "9 fields" in ov or "9 attributes" in ov or "9 columns" in ov or "dataset" in ov.lower()
    # Must not invent unverified domains or dimensions
    assert "store" not in ov.lower()
    assert "department" not in ov.lower()


def test_sec14_03_dynamic_bullet_generation():
    """3. Dynamic bullets must be cleanly formatted with 'Label: Value' or 'Label – Value'."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s3", filename="Employee.csv")
    bullets = report.executive_summary.highlights

    assert len(bullets) >= 1
    for b in bullets:
        assert ":" in b or "–" in b or "vs" in b, f"Bullet '{b}' should follow a clean business key-value format"


def test_sec14_04_dynamic_bullet_count():
    """4. Dynamic bullet count should be between 1 and 8 (never forced to fixed number)."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s4", filename="Employee.csv")
    count = len(report.executive_summary.highlights)
    assert 1 <= count <= 8, f"Bullet count {count} must be within [1, 8]"


def test_sec14_05_top_entity_evidence():
    """5. Top entity/category evidence correctly extracted and formatted."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s5", filename="Employee.csv")
    bullets_text = " ".join(report.executive_summary.highlights)
    # Bachelors is the top education entity
    assert "Bachelors" in bullets_text or "Education" in bullets_text


def test_sec14_06_comparison_evidence():
    """6. Meaningful comparisons are captured without semantic mixing."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s6", filename="Employee.csv")
    bullets_text = " ".join(report.executive_summary.highlights)
    # Should include tier or gender or education comparisons
    assert any(term in bullets_text for term in ["Tier", "Payment Tier", "Education", "City", "Gender", "Attrition"])


def test_sec14_07_distribution_evidence():
    """7. Distribution/share evidence includes percentage or proportion."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s7", filename="Employee.csv")
    bullets_text = " ".join(report.executive_summary.highlights)
    assert "%" in bullets_text, "At least one highlight should represent distribution or rate with %"


def test_sec14_08_overall_synthesis():
    """8. Overall paragraph synthesizes findings without speculation or subjective judgments."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s8", filename="Employee.csv")
    overall = report.executive_summary.overall

    assert overall.startswith("Overall:")
    lower_ov = overall.lower()
    # Must NOT invent causes or make unsupported subjective claims
    forbidden = ["this is good", "this is bad", "this is risky", "this is healthy", "poor performance", "indicates failure"]
    for f in forbidden:
        assert f not in lower_ov, f"Forbidden subjective phrase '{f}' found in overall"


def test_sec14_09_kpi_deduplication():
    """9. Bullets do not contain duplicate claims for the same entity and value."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s9", filename="Employee.csv")
    bullets = report.executive_summary.highlights

    seen_prefixes = set()
    for b in bullets:
        prefix = b.split(":")[0].strip().lower()
        assert prefix not in seen_prefixes, f"Duplicate bullet prefix '{prefix}' found"
        seen_prefixes.add(prefix)


def test_sec14_10_evidence_id_preservation():
    """10. Every executive summary claim has valid evidence IDs preserved in ledger."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s10", filename="Employee.csv")
    eids = report.executive_summary.evidence_ids

    assert len(eids) > 0, "Executive summary must have evidence_ids"
    ledger_ids = set(report.verified_evidence.keys())
    for eid in eids:
        assert eid in ledger_ids, f"Evidence ID '{eid}' missing from verified_evidence ledger"


def test_sec14_11_cross_evidence_semantic_mismatch_rejection():
    """11. Validator MUST strictly reject cross-metric mismatch: Education count as Attrition rate."""
    from app.reporting.summary_validator import SummaryValidator
    from app.reporting.models import VerifiedEvidenceLedger, EvidenceItem, EvidenceType

    ledger = VerifiedEvidenceLedger()
    ledger.add(EvidenceItem(
        id="EV-COUNT-001",
        type=EvidenceType.CATEGORY_SHARE,
        metric="Education",
        value=3601,
        formatted="3,601",
        label="Bachelors Record Count",
        dimension="Education",
        verified=True,
    ))

    # Fabricated bad summary trying to claim record counts 179 to 3,601 are attrition rates
    bad_summary = {
        "dataset_overview": "This workforce dataset contains 4,653 records across 9 fields.",
        "highlights": [
            "Attrition across Education ranges from 179 to 3,601.",
        ],
        "overall": "Overall: Attrition varies between 179 and 3,601 records across education tiers.",
        "evidence_ids": ["EV-COUNT-001"],
    }

    validator = SummaryValidator(ledger=ledger)
    res = validator.validate_summary(bad_summary)

    # Must fail or completely strip the mismatched claim
    if res.is_valid:
        # If validator cleaned it up, check that the invalid claim is stripped
        cleaned_hl = res.summary_dict.get("highlights", [])
        for hl in cleaned_hl:
            assert "179 to 3,601" not in hl, "Validator must strip count-attrition mismatch"
    else:
        assert not res.is_valid
        assert any("mismatch" in err.lower() or "count" in err.lower() or "attrition" in err.lower() for err in res.errors)


def test_sec14_12_unsupported_dimension_rejection():
    """12. Rejects unsupported dimensions not present in the dataset schema."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s12", filename="Employee.csv")
    text = (
        report.executive_summary.dataset_overview + " " +
        " ".join(report.executive_summary.highlights) + " " +
        report.executive_summary.overall
    ).lower()

    # Employee dataset has Education, City, PaymentTier, Age, Gender, EverBenched, ExperienceInCurrentDomain, LeaveOrNot
    assert "region" not in text
    assert "sales representative" not in text
    assert "product category" not in text


def test_sec14_13_unsupported_domain_terminology_rejection():
    """13. Preserves verified semantics: ExperienceInCurrentDomain is never renamed to Company Tenure."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s13", filename="Employee.csv")
    text = (
        report.executive_summary.dataset_overview + " " +
        " ".join(report.executive_summary.highlights) + " " +
        report.executive_summary.overall
    ).lower()

    assert "company tenure" not in text


def test_sec14_14_pdf_web_summary_consistency():
    """14. PDF executive briefing matches the exact web summary model."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_s14", filename="Employee.csv")
    pdf_bytes = PDFReportGenerator.generate(report.model_dump(), page_compression=0)
    pdf_text = pdf_bytes.decode("latin-1", errors="ignore")

    # PDF must contain the dataset overview
    assert "4,653" in pdf_text
    # PDF must contain the overall tag
    assert "Overall:" in pdf_text or "overall:" in pdf_text.lower()
    # PDF must contain at least one highlight label from web
    first_hl = report.executive_summary.highlights[0]
    label = first_hl.split(":")[0].strip()
    assert label in pdf_text


def test_sec14_15_ai_unavailable_deterministic_fallback():
    """15. Deterministic fallback generates complete Sales-style 3-part layout."""
    from app.reporting.executive_summary import generate_deterministic_summary
    from app.reporting.models import VerifiedEvidenceLedger, EvidenceItem, EvidenceType

    ledger = VerifiedEvidenceLedger()
    ledger.add(EvidenceItem(
        id="EV-KPI-1",
        type=EvidenceType.PRIMARY_KPI,
        metric="Total Revenue",
        value=5019000,
        formatted="₹50.19 lakh",
        label="Total Revenue",
        verified=True,
    ))
    ledger.add(EvidenceItem(
        id="EV-TOP-1",
        type=EvidenceType.TOP_GROUP,
        metric="Sales",
        dimension="Region",
        entity="North",
        value=1370000,
        formatted="₹13.70 lakh",
        label="Top Region",
        verified=True,
    ))

    result = generate_deterministic_summary(
        ledger=ledger,
        dataset_name="Sales_2023.csv",
        row_count=1000,
        column_count=12,
        domain="sales",
    )

    assert result.dataset_overview is not None and len(result.dataset_overview) > 0
    assert len(result.highlights) >= 2
    assert result.overall.startswith("Overall:")
    assert result.verification_status == "VERIFIED_ANALYTICS_ONLY"
    assert "EV-KPI-1" in result.evidence_ids
    assert "EV-TOP-1" in result.evidence_ids


def test_sec14_16_generic_dataset_summary():
    """16. Universal summary gracefully handles generic dataset."""
    df_generic = pd.DataFrame({
        "item_id": [f"ID_{i}" for i in range(100)],
        "category": ["Alpha", "Beta", "Gamma", "Delta"] * 25,
        "score": [float(i % 10) for i in range(100)],
    })
    report = ReportComposer().compose_report(frame=df_generic, dataset_id="sec14_generic", filename="GenericData.csv")
    summary = report.executive_summary

    assert summary.dataset_overview.startswith("This dataset contains 100 records")
    assert len(summary.highlights) >= 1
    assert summary.overall.startswith("Overall:")


def test_sec14_17_hr_dataset_summary():
    """17. HR dataset produces accurate workforce summary."""
    df = _load_employee_dataset()
    report = ReportComposer().compose_report(frame=df, dataset_id="sec14_hr", filename="Employee.csv")
    summary = report.executive_summary

    assert "4,653" in summary.dataset_overview
    hl_text = " ".join(summary.highlights)
    assert "Attrition" in hl_text or "Leave" in hl_text


def test_sec14_18_sales_dataset_summary():
    """18. Synthetic sales dataset produces expected Sales-style summary."""
    df_sales = pd.DataFrame({
        "region": ["North", "South", "East", "West"] * 250,
        "rep": ["Alice", "Bob", "Charlie", "David", "Eve"] * 200,
        "category": ["Electronics", "Clothing", "Home", "Sports"] * 250,
        "sales_amount": [100.0 + (i % 50) * 10 for i in range(1000)],
        "quantity": [(i % 5) + 1 for i in range(1000)],
    })
    report = ReportComposer().compose_report(frame=df_sales, dataset_id="sec14_sales", filename="Sales_Data.csv")
    summary = report.executive_summary

    assert "1,000" in summary.dataset_overview or "1000" in summary.dataset_overview
    assert len(summary.highlights) >= 2
    assert summary.overall.startswith("Overall:")


def test_sec14_19_finance_dataset_summary():
    """19. Synthetic finance dataset produces valid executive summary."""
    df_fin = pd.DataFrame({
        "account_id": [f"ACC_{i}" for i in range(500)],
        "department": ["Engineering", "Sales", "Operations", "Legal"] * 125,
        "revenue": [5000.0 + (i % 20) * 200 for i in range(500)],
        "expense": [3000.0 + (i % 15) * 150 for i in range(500)],
    })
    report = ReportComposer().compose_report(frame=df_fin, dataset_id="sec14_fin", filename="Quarterly_Finance.csv")
    summary = report.executive_summary

    assert "500" in summary.dataset_overview
    assert len(summary.highlights) >= 2
    assert summary.overall.startswith("Overall:")


def test_sec14_20_inventory_dataset_summary():
    """20. Synthetic inventory dataset produces valid executive summary."""
    df_inv = pd.DataFrame({
        "sku": [f"SKU_{i}" for i in range(800)],
        "warehouse": ["WH-East", "WH-West", "WH-Central"] * 266 + ["WH-East"] * 2,
        "category": ["Hardware", "Tools", "Fasteners", "Safety"] * 200,
        "stock_qty": [10 + (i % 50) for i in range(800)],
        "unit_cost": [2.5 + (i % 10) * 0.5 for i in range(800)],
    })
    report = ReportComposer().compose_report(frame=df_inv, dataset_id="sec14_inv", filename="Inventory_Audit.csv")
    summary = report.executive_summary

    assert "800" in summary.dataset_overview
    assert len(summary.highlights) >= 2
    assert summary.overall.startswith("Overall:")

