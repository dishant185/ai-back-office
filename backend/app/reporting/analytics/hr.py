from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from app.reporting.chart_builder import ChartBuilder
from app.reporting.formatter import format_value
from app.reporting.models import (
    ChartDefinition,
    RankingItem,
    ReportAnomaly,
    ReportMetric,
    ReportRanking,
    ReportRecommendation,
    ReportSection,
)


def _safe_numeric_series(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[col], errors="coerce").dropna()


def _binary_flag_series(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(dtype="float64")
    s = frame[col].dropna()
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce").dropna()
    s_lower = s.astype(str).str.strip().str.lower()
    mapping = {"yes": 1, "y": 1, "true": 1, "1": 1, "1.0": 1, "left": 1, "resigned": 1}
    return s_lower.map(lambda x: mapping.get(x, 0))


def _find_col(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in frame.columns:
            return c
        for col in frame.columns:
            if col.lower() == c.lower():
                return col
    return None


class HRAnalytics:
    """Computes dynamic, report-type-tailored metrics, sections, anomalies, and recommendations."""

    @classmethod
    def analyze(
        cls,
        frame: pd.DataFrame,
        report_type: str = "standard",
    ) -> tuple[list[ReportMetric], list[ReportSection], list[ReportAnomaly], list[ReportRecommendation]]:
        employee_count = int(len(frame.index))
        if employee_count == 0:
            return [], [], [], []

        # Detect relevant column names dynamically
        age_col = _find_col(frame, ["age", "employee_age"])
        age_group_col = _find_col(frame, ["age_group", "agegroup", "age_bracket", "generation"])
        dept_col = _find_col(frame, ["department", "dept", "business_unit", "division"])
        role_col = _find_col(frame, ["job_role", "jobrole", "role", "designation", "title"])
        edu_col = _find_col(frame, ["education", "education_level", "degree", "qualification"])
        edu_field_col = _find_col(frame, ["education_field", "educationfield", "field_of_study", "major"])
        gender_col = _find_col(frame, ["gender", "sex"])
        city_col = _find_col(frame, ["city", "location", "office_location", "branch"])
        leave_col = _find_col(frame, ["leave_or_not", "attrition", "left", "resigned"])
        tier_col = _find_col(frame, ["payment_tier", "salary_tier", "tier", "salary_slab", "salaryslab"])
        salary_col = _find_col(frame, ["monthly_income", "monthlyincome", "salary", "daily_rate", "compensation"])
        exp_col = _find_col(frame, ["experience_in_current_domain", "total_working_years", "totalworkingyears", "years_at_company", "yearsatcompany", "experience"])
        tenure_col = _find_col(frame, ["years_at_company", "yearsatcompany", "tenure"])
        bench_col = _find_col(frame, ["ever_benched", "benched"])
        overtime_col = _find_col(frame, ["over_time", "overtime"])

        age_series = _safe_numeric_series(frame, age_col) if age_col else pd.Series(dtype="float64")
        leave_series = _binary_flag_series(frame, leave_col) if leave_col else pd.Series(dtype="float64")
        exp_series = _safe_numeric_series(frame, exp_col) if exp_col else pd.Series(dtype="float64")
        salary_series = _safe_numeric_series(frame, salary_col) if salary_col else pd.Series(dtype="float64")

        # Global aggregate indicators
        avg_age = float(age_series.mean()) if not age_series.empty else None
        median_age = float(age_series.median()) if not age_series.empty else None
        employees_left = int(leave_series.sum()) if not leave_series.empty else None
        employees_retained = (employee_count - employees_left) if employees_left is not None else None
        attrition_rate = (
            float((employees_left / employee_count) * 100)
            if employees_left is not None and employee_count > 0
            else None
        )
        avg_exp = float(exp_series.mean()) if not exp_series.empty else None
        avg_salary = float(salary_series.mean()) if not salary_series.empty else None

        # Prepare normalized working frame for cross-tabulations
        work_df = frame.copy()
        if leave_col and not leave_series.empty:
            work_df["__leave_flag"] = leave_series

        # If age exists but no age_group, create dynamic cohorts
        if age_col and not age_series.empty and not age_group_col:
            bins = [0, 25, 35, 45, 55, 120]
            labels = ["Under 25", "26-35", "36-45", "46-55", "55+"]
            work_df["__age_cohort"] = pd.cut(pd.to_numeric(work_df[age_col], errors="coerce"), bins=bins, labels=labels)
            age_group_col = "__age_cohort"

        rpt = (report_type or "standard").lower()

        # =========================================================================
        # 1. SPECIALIZED: AGE ANALYSIS & DEMOGRAPHICS
        # =========================================================================
        if rpt in ("age_analysis", "age_demographics", "demographics"):
            min_age = int(age_series.min()) if not age_series.empty else None
            max_age = int(age_series.max()) if not age_series.empty else None
            under_30_count = int((age_series < 30).sum()) if not age_series.empty else None
            under_30_pct = (under_30_count / employee_count * 100) if under_30_count is not None else None
            senior_count = int((age_series >= 45).sum()) if not age_series.empty else None
            senior_pct = (senior_count / employee_count * 100) if senior_count is not None else None

            kpis = [
                ReportMetric(
                    id="avg_age",
                    name="Average Workforce Age",
                    value=round(avg_age, 1) if avg_age else None,
                    formatted_value=format_value(avg_age, "years"),
                    unit="years",
                    description="Mean age across all active personnel",
                    priority=1,
                    category="demographics",
                    status="neutral",
                ),
                ReportMetric(
                    id="median_age",
                    name="Median Age",
                    value=round(median_age, 1) if median_age else None,
                    formatted_value=format_value(median_age, "years"),
                    unit="years",
                    description="50th percentile workforce age midpoint",
                    priority=2,
                    category="demographics",
                ),
                ReportMetric(
                    id="junior_talent_share",
                    name="Junior Cohort (<30 yrs)",
                    value=round(under_30_pct, 1) if under_30_pct is not None else None,
                    formatted_value=format_value(under_30_pct, "percent"),
                    unit="percent",
                    description="Proportion of early-career workforce under age 30",
                    priority=3,
                    category="demographics",
                    status="positive" if (under_30_pct or 0) >= 25 else "neutral",
                ),
                ReportMetric(
                    id="senior_talent_share",
                    name="Senior Cohort (45+ yrs)",
                    value=round(senior_pct, 1) if senior_pct is not None else None,
                    formatted_value=format_value(senior_pct, "percent"),
                    unit="percent",
                    description="Proportion of senior personnel aged 45 and above",
                    priority=4,
                    category="demographics",
                ),
                ReportMetric(
                    id="age_range",
                    name="Demographic Span",
                    value=f"{min_age}–{max_age}" if min_age and max_age else None,
                    formatted_value=f"{min_age} to {max_age} yrs" if min_age and max_age else "N/A",
                    unit="range",
                    description="Age span from youngest to oldest staff member",
                    priority=5,
                    category="demographics",
                ),
                ReportMetric(
                    id="overall_headcount",
                    name="Total Evaluated",
                    value=employee_count,
                    formatted_value=format_value(employee_count, "people"),
                    unit="people",
                    description="Total verified employee records",
                    priority=6,
                    category="headcount",
                ),
            ]

            sections = []
            # Section 1: Age Brackets
            age_charts = []
            if age_group_col and age_group_col in work_df.columns:
                c = ChartBuilder.categorical_distribution(
                    work_df, age_group_col, "Generational Age Cohort Distribution", "hr_age_cohort_dist"
                )
                if c:
                    age_charts.append(c)
            elif age_col:
                c = ChartBuilder.numeric_histogram(
                    work_df, age_col, "Age Bracket Distribution", "hr_age_hist", bins=5, unit="people"
                )
                if c:
                    age_charts.append(c)

            age_rankings = []
            if age_group_col and age_group_col in work_df.columns:
                # Build detailed cohort breakdown ranking with subtext
                cohort_counts = work_df[age_group_col].value_counts()
                items = []
                for idx, (grp, cnt) in enumerate(cohort_counts.items(), start=1):
                    pct = (cnt / employee_count * 100)
                    sub_str = f"Headcount: {cnt:,}"
                    if "__leave_flag" in work_df.columns:
                        grp_sub = work_df[work_df[age_group_col] == grp]
                        turnover = grp_sub["__leave_flag"].mean() * 100
                        sub_str += f" | Attrition: {turnover:.1f}%"
                    items.append(RankingItem(
                        rank=idx,
                        label=str(grp),
                        value=int(cnt),
                        formatted_value=f"{cnt:,} staff",
                        pct_of_total=round(pct, 1),
                        subtext=sub_str,
                    ))
                age_rankings.append(ReportRanking(
                    id="hr_age_cohort_table",
                    title="Age Cohort Headcount & Retention Matrix",
                    dimension=age_group_col,
                    metric="headcount",
                    items=items,
                ))

            sections.append(ReportSection(
                id="age_distribution_sec",
                title="Generational Age Cohort & Distribution Analysis",
                description="Comprehensive structural breakdown of organizational demographics across generational age tiers.",
                charts=age_charts,
                rankings=age_rankings,
                callout=f"Workforce demographic span ranges from {min_age} to {max_age} years, with a median age of {median_age:.1f} years." if median_age else None,
            ))

            # Section 2: Age vs Retention
            if "__leave_flag" in work_df.columns and age_group_col:
                ret_charts = []
                c = ChartBuilder.rate_by_category(
                    work_df, age_group_col, "__leave_flag", "Turnover Rate by Age Cohort (%)", "hr_age_churn_rate"
                )
                if c:
                    ret_charts.append(c)

                sections.append(ReportSection(
                    id="age_retention_sec",
                    title="Age-Correlated Attrition & Career Retention",
                    description="Evaluates turnover vulnerability and departure rates across different career lifecycles.",
                    charts=ret_charts,
                    callout="Early career cohorts frequently experience heightened attrition requiring dedicated onboarding and growth paths.",
                ))

            anomalies = []
            if under_30_pct and under_30_pct < 15:
                anomalies.append(ReportAnomaly(
                    id="hr_aging_workforce",
                    metric="junior_talent_share",
                    label="Aging Workforce Demographics",
                    value=f"{under_30_pct:.1f}%",
                    expected="> 20.0%",
                    severity="medium",
                    reason="Low proportion of junior professionals signals long-term succession risk.",
                ))
            if "__leave_flag" in work_df.columns and age_group_col:
                cohort_churn = work_df.groupby(age_group_col)["__leave_flag"].mean() * 100
                for grp, rate in cohort_churn.items():
                    if rate > 30.0:
                        anomalies.append(ReportAnomaly(
                            id=f"hr_churn_age_{grp}",
                            metric="age_cohort_attrition",
                            label=f"Elevated Departure in Age Tier {grp}",
                            value=f"{rate:.1f}%",
                            expected="< 20.0%",
                            severity="high",
                            reason=f"Employees in the {grp} bracket exhibit significantly higher flight probability.",
                        ))

            recommendations = [
                ReportRecommendation(
                    id="rec_generational_mentorship",
                    title="Establish Cross-Generational Mentorship Program",
                    description="Pair seasoned personnel with junior talent to transfer institutional knowledge and mitigate turnover in early-tenure brackets.",
                    priority="high",
                    category="retention",
                ),
                ReportRecommendation(
                    id="rec_flexible_demographic_benefits",
                    title="Tailor Career Incentives by Generational Tier",
                    description="Offer career development stipends for junior staff and phased retirement/leadership tracks for senior personnel.",
                    priority="medium",
                    category="optimization",
                ),
            ]
            return kpis, sections, anomalies, recommendations

        # =========================================================================
        # 2. SPECIALIZED: GENDER DIVERSITY & REPRESENTATION
        # =========================================================================
        if rpt in ("gender_analysis", "gender_diversity", "diversity"):
            female_count = 0
            male_count = 0
            if gender_col:
                g_counts = work_df[gender_col].astype(str).str.strip().str.lower().value_counts()
                female_count = int(g_counts.get("female", g_counts.get("f", 0)))
                male_count = int(g_counts.get("male", g_counts.get("m", 0)))

            female_pct = (female_count / employee_count * 100) if employee_count > 0 else 0
            male_pct = (male_count / employee_count * 100) if employee_count > 0 else 0
            parity_ratio = (female_count / male_count) if male_count > 0 else None

            # Turnover by gender
            female_churn = None
            male_churn = None
            if "__leave_flag" in work_df.columns and gender_col:
                sub = work_df.dropna(subset=[gender_col, "__leave_flag"]).copy()
                sub["_g_clean"] = sub[gender_col].astype(str).str.strip().str.lower()
                churn_by_g = sub.groupby("_g_clean")["__leave_flag"].mean() * 100
                female_churn = churn_by_g.get("female", churn_by_g.get("f"))
                male_churn = churn_by_g.get("male", churn_by_g.get("m"))

            kpis = [
                ReportMetric(
                    id="female_representation",
                    name="Female Representation",
                    value=round(female_pct, 1),
                    formatted_value=f"{female_pct:.1f}%",
                    unit="percent",
                    description="Proportion of female staff across workforce",
                    priority=1,
                    category="diversity",
                    status="positive" if female_pct >= 40 else "warning" if female_pct < 25 else "neutral",
                ),
                ReportMetric(
                    id="male_representation",
                    name="Male Representation",
                    value=round(male_pct, 1),
                    formatted_value=f"{male_pct:.1f}%",
                    unit="percent",
                    description="Proportion of male staff across workforce",
                    priority=2,
                    category="diversity",
                ),
                ReportMetric(
                    id="gender_ratio",
                    name="Gender Parity Index",
                    value=round(parity_ratio, 2) if parity_ratio else None,
                    formatted_value=f"1 : {round(1/parity_ratio, 1)}" if parity_ratio and parity_ratio < 1 else f"{round(parity_ratio, 1)} : 1" if parity_ratio else "N/A",
                    unit="ratio",
                    description="Ratio of female to male personnel",
                    priority=3,
                    category="diversity",
                ),
                ReportMetric(
                    id="female_attrition",
                    name="Female Attrition Rate",
                    value=round(female_churn, 1) if female_churn is not None else None,
                    formatted_value=f"{female_churn:.1f}%" if female_churn is not None else "N/A",
                    unit="percent",
                    description="Turnover rate amongst female staff members",
                    priority=4,
                    category="retention",
                    available=female_churn is not None,
                ),
                ReportMetric(
                    id="male_attrition",
                    name="Male Attrition Rate",
                    value=round(male_churn, 1) if male_churn is not None else None,
                    formatted_value=f"{male_churn:.1f}%" if male_churn is not None else "N/A",
                    unit="percent",
                    description="Turnover rate amongst male staff members",
                    priority=5,
                    category="retention",
                    available=male_churn is not None,
                ),
                ReportMetric(
                    id="total_evaluated",
                    name="Total Audited Headcount",
                    value=employee_count,
                    formatted_value=format_value(employee_count, "people"),
                    unit="people",
                    description="Total verified employee records",
                    priority=6,
                    category="headcount",
                ),
            ]

            sections = []
            gender_charts = []
            if gender_col:
                c = ChartBuilder.categorical_distribution(
                    work_df, gender_col, "Workforce Gender Composition", "hr_gender_donut"
                )
                if c:
                    gender_charts.append(c)

            # Departmental breakdown by gender
            gender_rankings = []
            if dept_col and gender_col:
                # Cross-tabulate department by gender
                dept_summary = work_df.groupby(dept_col).size().sort_values(ascending=False)
                items = []
                for idx, (dept, cnt) in enumerate(dept_summary.items(), start=1):
                    d_sub = work_df[work_df[dept_col] == dept]
                    d_fem = (d_sub[gender_col].astype(str).str.strip().str.lower().isin(["female", "f"])).sum()
                    fem_share = (d_fem / cnt * 100) if cnt > 0 else 0
                    items.append(RankingItem(
                        rank=idx,
                        label=str(dept),
                        value=int(cnt),
                        formatted_value=f"{cnt:,} staff",
                        pct_of_total=round(cnt / employee_count * 100, 1),
                        subtext=f"Female: {d_fem:,} ({fem_share:.1f}%) | Male: {cnt - d_fem:,}",
                    ))
                gender_rankings.append(ReportRanking(
                    id="hr_dept_gender_table",
                    title="Departmental Gender Distribution & Parity",
                    dimension=dept_col,
                    metric="headcount",
                    items=items,
                ))

            sections.append(ReportSection(
                id="gender_overview_sec",
                title="Workforce Gender Distribution & Departmental Parity",
                description="Evaluation of organizational gender balance across functional divisions and roles.",
                charts=gender_charts,
                rankings=gender_rankings,
                callout=f"Current organization comprises {female_count:,} female staff ({female_pct:.1f}%) and {male_count:,} male staff ({male_pct:.1f}%).",
            ))

            anomalies = []
            if female_pct < 25:
                anomalies.append(ReportAnomaly(
                    id="hr_gender_skew",
                    metric="female_representation",
                    label="Pronounced Gender Imbalance",
                    value=f"{female_pct:.1f}%",
                    expected=">= 35.0%",
                    severity="high",
                    reason="Female representation falls significantly below industry diversity targets.",
                ))
            if female_churn and male_churn and abs(female_churn - male_churn) > 10:
                higher_g = "Female" if female_churn > male_churn else "Male"
                diff = abs(female_churn - male_churn)
                anomalies.append(ReportAnomaly(
                    id="hr_gender_churn_gap",
                    metric="gender_attrition_gap",
                    label=f"Disproportionate {higher_g} Turnover Gap",
                    value=f"{diff:.1f}% gap",
                    expected="< 5.0% gap",
                    severity="medium",
                    reason=f"{higher_g} staff exhibit an elevated departure disparity requiring qualitative review.",
                ))

            recommendations = [
                ReportRecommendation(
                    id="rec_diversity_hiring",
                    title="Implement Inclusive Talent Acquisition Pipelines",
                    description="Standardize gender-neutral job descriptions and require balanced candidate slates for leadership roles.",
                    priority="high",
                    category="operational",
                ),
                ReportRecommendation(
                    id="rec_parity_audit",
                    title="Conduct Annual Compensation & Promotion Parity Audit",
                    description="Evaluate promotion velocity and pay equity across gender cohorts to prevent retention disparities.",
                    priority="medium",
                    category="retention",
                ),
            ]
            return kpis, sections, anomalies, recommendations

        # =========================================================================
        # 3. SPECIALIZED: EDUCATION LEVEL ANALYSIS
        # =========================================================================
        if rpt in ("education_analysis", "education_level_analysis", "education"):
            active_edu_col = edu_field_col or edu_col
            distinct_edu = int(work_df[active_edu_col].nunique()) if active_edu_col else 0
            dominant_edu = str(work_df[active_edu_col].mode().iloc[0]) if active_edu_col and not work_df[active_edu_col].empty else "N/A"

            kpis = [
                ReportMetric(
                    id="distinct_qualifications",
                    name="Distinct Academic Profiles",
                    value=distinct_edu,
                    formatted_value=f"{distinct_edu} Fields",
                    unit="count",
                    description="Unique degrees or educational disciplines recorded",
                    priority=1,
                    category="education",
                ),
                ReportMetric(
                    id="dominant_qualification",
                    name="Dominant Discipline",
                    value=dominant_edu,
                    formatted_value=dominant_edu,
                    unit="text",
                    description="Most frequent academic specialization across staff",
                    priority=2,
                    category="education",
                ),
                ReportMetric(
                    id="total_workforce",
                    name="Total Audited Headcount",
                    value=employee_count,
                    formatted_value=format_value(employee_count, "people"),
                    unit="people",
                    description="Total verified employee records",
                    priority=3,
                    category="headcount",
                ),
                ReportMetric(
                    id="avg_experience_edu",
                    name="Mean Domain Experience",
                    value=round(avg_exp, 1) if avg_exp else None,
                    formatted_value=format_value(avg_exp, "years"),
                    unit="years",
                    description="Average professional tenure across educational tiers",
                    priority=4,
                    category="experience",
                ),
            ]

            sections = []
            edu_charts = []
            if active_edu_col:
                c = ChartBuilder.categorical_distribution(
                    work_df, active_edu_col, "Workforce by Educational Qualification", "hr_edu_pie"
                )
                if c:
                    edu_charts.append(c)

            edu_rankings = []
            if active_edu_col:
                counts = work_df[active_edu_col].value_counts()
                items = []
                for idx, (edu_name, cnt) in enumerate(counts.items(), start=1):
                    pct = (cnt / employee_count * 100)
                    sub_str = f"Headcount: {cnt:,}"
                    if "__leave_flag" in work_df.columns:
                        grp_sub = work_df[work_df[active_edu_col] == edu_name]
                        churn_r = grp_sub["__leave_flag"].mean() * 100
                        sub_str += f" | Attrition: {churn_r:.1f}%"
                    if exp_col:
                        grp_sub = work_df[work_df[active_edu_col] == edu_name]
                        mean_e = pd.to_numeric(grp_sub[exp_col], errors="coerce").mean()
                        if pd.notna(mean_e):
                            sub_str += f" | Avg Exp: {mean_e:.1f}y"
                    items.append(RankingItem(
                        rank=idx,
                        label=str(edu_name),
                        value=int(cnt),
                        formatted_value=f"{cnt:,} staff",
                        pct_of_total=round(pct, 1),
                        subtext=sub_str,
                    ))
                edu_rankings.append(ReportRanking(
                    id="hr_edu_breakdown_table",
                    title="Educational Qualification & Performance Matrix",
                    dimension=active_edu_col,
                    metric="headcount",
                    items=items,
                ))

            sections.append(ReportSection(
                id="education_breakdown_sec",
                title="Academic Qualifications & Capability Profile",
                description="Distribution of degree attainments, specialized educational disciplines, and tenure correlation.",
                charts=edu_charts,
                rankings=edu_rankings,
                callout=f"The primary academic discipline is {dominant_edu}, comprising {(counts.iloc[0]/employee_count*100):.1f}% of the overall workforce." if active_edu_col and not counts.empty else None,
            ))

            # Attrition by education section
            if "__leave_flag" in work_df.columns and active_edu_col:
                c = ChartBuilder.rate_by_category(
                    work_df, active_edu_col, "__leave_flag", "Attrition Rate by Educational Discipline (%)", "hr_edu_churn_chart"
                )
                if c:
                    sections.append(ReportSection(
                        id="education_attrition_sec",
                        title="Qualification-Specific Turnover Diagnostics",
                        description="Examines whether specialized degree holders exhibit elevated flight risk or compensation friction.",
                        charts=[c],
                    ))

            anomalies = []
            recommendations = [
                ReportRecommendation(
                    id="rec_education_upskilling",
                    title="Align Upskilling Programs with Technical Roles",
                    description="Provide targeted technical credentialing for specialized educational cohorts to maximize project deployment.",
                    priority="medium",
                    category="optimization",
                )
            ]
            return kpis, sections, anomalies, recommendations

        # =========================================================================
        # 4. SPECIALIZED: EMPLOYEE DISTRIBUTION & DEPARTMENTS
        # =========================================================================
        if rpt in ("employee_distribution", "department_analysis", "workforce_distribution"):
            active_dept_col = dept_col or "department"
            num_depts = int(work_df[active_dept_col].nunique()) if active_dept_col in work_df.columns else 0
            top_dept_name = str(work_df[active_dept_col].value_counts().index[0]) if active_dept_col in work_df.columns and not work_df[active_dept_col].empty else "N/A"
            top_dept_cnt = int(work_df[active_dept_col].value_counts().iloc[0]) if active_dept_col in work_df.columns and not work_df[active_dept_col].empty else 0
            top_dept_share = (top_dept_cnt / employee_count * 100) if employee_count > 0 else 0
            num_roles = int(work_df[role_col].nunique()) if role_col and role_col in work_df.columns else 0

            kpis = [
                ReportMetric(
                    id="total_workforce",
                    name="Total Organization Headcount",
                    value=employee_count,
                    formatted_value=format_value(employee_count, "people"),
                    unit="people",
                    description="Aggregate audited personnel roster",
                    priority=1,
                    category="headcount",
                ),
                ReportMetric(
                    id="functional_departments",
                    name="Active Departments",
                    value=num_depts,
                    formatted_value=f"{num_depts} Units",
                    unit="units",
                    description="Total discrete operational departments",
                    priority=2,
                    category="organization",
                ),
                ReportMetric(
                    id="largest_dept_share",
                    name="Primary Unit Share",
                    value=round(top_dept_share, 1),
                    formatted_value=f"{top_dept_share:.1f}% ({top_dept_name})",
                    unit="percent",
                    description="Concentration of staff in largest single division",
                    priority=3,
                    category="organization",
                    status="warning" if top_dept_share > 60 else "neutral",
                ),
                ReportMetric(
                    id="role_specialization",
                    name="Specialized Job Roles",
                    value=num_roles if num_roles > 0 else None,
                    formatted_value=f"{num_roles} Roles" if num_roles > 0 else "N/A",
                    unit="roles",
                    description="Distinct functional titles and designations",
                    priority=4,
                    category="organization",
                    available=num_roles > 0,
                ),
                ReportMetric(
                    id="retained_pool",
                    name="Active Retained Staff",
                    value=employees_retained,
                    formatted_value=format_value(employees_retained, "people"),
                    unit="people",
                    description="Active staff excluding departures",
                    priority=5,
                    category="retention",
                    available=employees_retained is not None,
                ),
            ]

            sections = []
            dept_charts = []
            if active_dept_col in work_df.columns:
                c = ChartBuilder.categorical_distribution(
                    work_df, active_dept_col, "Headcount by Functional Department", "hr_dept_donut"
                )
                if c:
                    dept_charts.append(c)

            if role_col and role_col in work_df.columns:
                c = ChartBuilder.categorical_distribution(
                    work_df, role_col, "Top Job Role Specializations", "hr_role_bar", max_categories=8
                )
                if c:
                    dept_charts.append(c)

            dept_rankings = []
            if active_dept_col in work_df.columns:
                counts = work_df[active_dept_col].value_counts()
                items = []
                for idx, (d_name, cnt) in enumerate(counts.items(), start=1):
                    pct = (cnt / employee_count * 100)
                    sub_str = f"Headcount: {cnt:,}"
                    if "__leave_flag" in work_df.columns:
                        d_sub = work_df[work_df[active_dept_col] == d_name]
                        churn = d_sub["__leave_flag"].mean() * 100
                        sub_str += f" | Attrition: {churn:.1f}%"
                    if role_col and role_col in work_df.columns:
                        d_roles = work_df[work_df[active_dept_col] == d_name][role_col].nunique()
                        sub_str += f" | {d_roles} Roles"
                    items.append(RankingItem(
                        rank=idx,
                        label=str(d_name),
                        value=int(cnt),
                        formatted_value=f"{cnt:,} staff",
                        pct_of_total=round(pct, 1),
                        subtext=sub_str,
                    ))
                dept_rankings.append(ReportRanking(
                    id="hr_dept_hierarchy_table",
                    title="Departmental Staffing & Operational Allocation",
                    dimension=active_dept_col,
                    metric="headcount",
                    items=items,
                ))

            sections.append(ReportSection(
                id="dept_distribution_sec",
                title="Departmental Headcount & Operational Structure",
                description="Functional weight, team size distribution, and role specialization across business divisions.",
                charts=dept_charts,
                rankings=dept_rankings,
                callout=f"Organizational structure is concentrated in {top_dept_name}, representing {top_dept_share:.1f}% of total personnel across {num_depts} functional units.",
            ))

            anomalies = []
            if top_dept_share > 65:
                anomalies.append(ReportAnomaly(
                    id="hr_high_dept_concentration",
                    metric="largest_dept_share",
                    label="Heavy Departmental Concentration Risk",
                    value=f"{top_dept_share:.1f}%",
                    expected="< 50.0%",
                    severity="medium",
                    reason=f"Over two-thirds of personnel are situated within {top_dept_name}, creating operational dependency.",
                ))

            recommendations = [
                ReportRecommendation(
                    id="rec_cross_functional_mobility",
                    title="Establish Cross-Functional Mobility Channels",
                    description="Create internal transfer programs between high-density and emerging units to optimize headcount allocation.",
                    priority="medium",
                    category="optimization",
                )
            ]
            return kpis, sections, anomalies, recommendations

        # =========================================================================
        # 5. SPECIALIZED: ATTRITION & RETENTION ANALYSIS
        # =========================================================================
        if rpt in ("attrition_analysis", "attrition", "retention", "attrition_retention"):
            highest_risk_dept = "N/A"
            dept_churn_rates = {}
            if dept_col and "__leave_flag" in work_df.columns:
                dept_churn_rates = (work_df.groupby(dept_col)["__leave_flag"].mean() * 100).to_dict()
                if dept_churn_rates:
                    highest_risk_dept = max(dept_churn_rates.items(), key=lambda x: x[1])[0]

            kpis = [
                ReportMetric(
                    id="gross_attrition_rate",
                    name="Gross Turnover Rate",
                    value=round(attrition_rate, 2) if attrition_rate is not None else None,
                    formatted_value=format_value(attrition_rate, "percent"),
                    unit="percent",
                    description="Proportion of total staff departed from the organization",
                    priority=1,
                    category="retention",
                    status="warning" if (attrition_rate or 0) > 20 else "positive",
                ),
                ReportMetric(
                    id="total_departures",
                    name="Confirmed Departures",
                    value=employees_left,
                    formatted_value=format_value(employees_left, "people"),
                    unit="people",
                    description="Total recorded employee departures",
                    priority=2,
                    category="retention",
                    status="warning" if (employees_left or 0) > 0 else "neutral",
                ),
                ReportMetric(
                    id="active_retained",
                    name="Retained Talent Pool",
                    value=employees_retained,
                    formatted_value=format_value(employees_retained, "people"),
                    unit="people",
                    description="Staff actively retained without attrition events",
                    priority=3,
                    category="retention",
                    status="positive",
                ),
                ReportMetric(
                    id="highest_risk_division",
                    name="Peak Churn Division",
                    value=highest_risk_dept,
                    formatted_value=f"{highest_risk_dept} ({dept_churn_rates.get(highest_risk_dept, 0):.1f}%)" if highest_risk_dept != "N/A" else "N/A",
                    unit="text",
                    description="Operational department demonstrating highest turnover rate",
                    priority=4,
                    category="risk",
                    status="warning",
                ),
            ]

            sections = []
            churn_charts = []
            if dept_col and "__leave_flag" in work_df.columns:
                c = ChartBuilder.rate_by_category(
                    work_df, dept_col, "__leave_flag", "Attrition Rate by Department (%)", "hr_churn_dept_chart"
                )
                if c:
                    churn_charts.append(c)

            if tier_col and "__leave_flag" in work_df.columns:
                c = ChartBuilder.rate_by_category(
                    work_df, tier_col, "__leave_flag", "Attrition Rate by Compensation Tier (%)", "hr_churn_tier_chart"
                )
                if c:
                    churn_charts.append(c)

            if overtime_col and "__leave_flag" in work_df.columns:
                c = ChartBuilder.rate_by_category(
                    work_df, overtime_col, "__leave_flag", "Attrition Rate by Overtime Demand (%)", "hr_churn_overtime_chart"
                )
                if c:
                    churn_charts.append(c)

            churn_rankings = []
            if dept_col and "__leave_flag" in work_df.columns:
                d_counts = work_df.groupby(dept_col).size()
                d_left = work_df.groupby(dept_col)["__leave_flag"].sum()
                items = []
                for idx, (d_name, l_cnt) in enumerate(d_left.sort_values(ascending=False).items(), start=1):
                    total_d = d_counts.get(d_name, 1)
                    rate = (l_cnt / total_d * 100) if total_d > 0 else 0
                    items.append(RankingItem(
                        rank=idx,
                        label=str(d_name),
                        value=int(l_cnt),
                        formatted_value=f"{int(l_cnt):,} departures",
                        pct_of_total=round(rate, 1),
                        subtext=f"Turnover: {rate:.1f}% | Out of {total_d:,} staff",
                    ))
                churn_rankings.append(ReportRanking(
                    id="hr_dept_churn_rankings",
                    title="Department Flight Risk & Departure Matrix",
                    dimension=dept_col,
                    metric="departures",
                    items=items,
                ))

            sections.append(ReportSection(
                id="attrition_dynamics_sec",
                title="Organizational Flight Risk & Attrition Corridors",
                description="Root-cause diagnostic tracking turnover spikes across departments, compensation tiers, and workload parameters.",
                charts=churn_charts,
                rankings=churn_rankings,
                callout=f"Organization turnover rate stands at {attrition_rate:.1f}%, with highest departure concentration in {highest_risk_dept}." if attrition_rate else None,
            ))

            anomalies = []
            if attrition_rate and attrition_rate > 20.0:
                anomalies.append(ReportAnomaly(
                    id="hr_critical_churn",
                    metric="gross_attrition_rate",
                    label="High Enterprise Attrition Velocity",
                    value=f"{attrition_rate:.1f}%",
                    expected="< 15.0%",
                    severity="high",
                    reason="Enterprise turnover exceeds standard corporate benchmarks, signaling operational talent drain.",
                ))
            if dept_churn_rates.get(highest_risk_dept, 0) > 35.0:
                anomalies.append(ReportAnomaly(
                    id="hr_dept_spike",
                    metric="dept_turnover",
                    label=f"Acute Departure Spike in {highest_risk_dept}",
                    value=f"{dept_churn_rates[highest_risk_dept]:.1f}%",
                    expected="< 20.0%",
                    severity="high",
                    reason=f"Over one in three staff in {highest_risk_dept} have departed, indicating localized retention friction.",
                ))

            recommendations = [
                ReportRecommendation(
                    id="rec_immediate_stay_interviews",
                    title="Initiate Proactive Retention Stay-Interviews",
                    description=f"Deploy pulse surveys and structured stay-interviews within {highest_risk_dept} and high-churn compensation tiers.",
                    priority="high",
                    category="retention",
                ),
                ReportRecommendation(
                    id="rec_workload_burnout_mitigation",
                    title="Implement Workload Balancing & Overtime Caps",
                    description="Review overtime mandates and resource allocation to alleviate burnout among operational teams.",
                    priority="medium",
                    category="operational",
                ),
            ]
            return kpis, sections, anomalies, recommendations

        # =========================================================================
        # 6. DEFAULT / WORKFORCE OVERVIEW (COMPREHENSIVE ENTERPRISE MIS REPORT)
        # =========================================================================
        kpis = [
            ReportMetric(
                id="employee_count",
                name="Total Workforce",
                value=employee_count,
                formatted_value=format_value(employee_count, "people"),
                unit="people",
                description="Total verified active and historical personnel",
                priority=1,
                category="headcount",
                status="neutral",
            ),
            ReportMetric(
                id="attrition_rate",
                name="Attrition Rate",
                value=round(attrition_rate, 2) if attrition_rate is not None else None,
                formatted_value=format_value(attrition_rate, "percent"),
                unit="percent",
                description="Proportion of staff who have separated from the company",
                priority=2,
                category="retention",
                status="warning" if (attrition_rate or 0) > 20 else "positive",
                available=attrition_rate is not None,
            ),
            ReportMetric(
                id="average_age",
                name="Average Age",
                value=round(avg_age, 1) if avg_age is not None else None,
                formatted_value=format_value(avg_age, "years"),
                unit="years",
                description="Mean age across employee demographics",
                priority=3,
                category="demographics",
                status="neutral",
                available=avg_age is not None,
            ),
            ReportMetric(
                id="avg_experience",
                name="Avg Domain Experience",
                value=round(avg_exp, 1) if avg_exp is not None else None,
                formatted_value=format_value(avg_exp, "years"),
                unit="years",
                description="Average tenure within current domain or company",
                priority=4,
                category="experience",
                status="neutral",
                available=avg_exp is not None,
            ),
            ReportMetric(
                id="employees_left",
                name="Departed Personnel",
                value=employees_left,
                formatted_value=format_value(employees_left, "people"),
                unit="people",
                description="Total confirmed separations",
                priority=5,
                category="retention",
                status="warning" if (employees_left or 0) > 0 else "neutral",
                available=employees_left is not None,
            ),
            ReportMetric(
                id="employees_retained",
                name="Active Retained Staff",
                value=employees_retained,
                formatted_value=format_value(employees_retained, "people"),
                unit="people",
                description="Active retained talent pool",
                priority=6,
                category="retention",
                status="positive",
                available=employees_retained is not None,
            ),
        ]

        sections = []

        # SECTION A: Departmental & Structural Composition
        dept_charts = []
        if dept_col and dept_col in work_df.columns:
            c = ChartBuilder.categorical_distribution(
                work_df, dept_col, "Workforce by Department", "hr_dept_dist"
            )
            if c:
                dept_charts.append(c)

        if role_col and role_col in work_df.columns:
            c = ChartBuilder.categorical_distribution(
                work_df, role_col, "Top Job Roles Distribution", "hr_role_dist", max_categories=7
            )
            if c:
                dept_charts.append(c)

        dept_rankings = []
        if dept_col and dept_col in work_df.columns:
            ranking = ChartBuilder.build_ranking(
                work_df, dept_col, dept_col, "Headcount by Department", "hr_dept_rank", agg="count", unit="people"
            )
            if ranking:
                dept_rankings.append(ranking)

        sections.append(ReportSection(
            id="workforce_composition",
            title="Workforce Composition & Departmental Structure",
            description="Functional division breakdown, headcount density, and operational role distribution.",
            metrics=[m for m in kpis if m.id in ("employee_count", "employees_retained")],
            charts=dept_charts,
            rankings=dept_rankings,
            callout=f"Organization encompasses {work_df[dept_col].nunique() if dept_col in work_df.columns else 'multiple'} functional divisions across {employee_count:,} verified personnel records.",
        ))

        # SECTION B: Demographics & Diversity
        demo_charts = []
        if gender_col and gender_col in work_df.columns:
            c = ChartBuilder.categorical_distribution(
                work_df, gender_col, "Gender Diversity Breakdown", "hr_gender_dist"
            )
            if c:
                demo_charts.append(c)

        if age_group_col and age_group_col in work_df.columns:
            c = ChartBuilder.categorical_distribution(
                work_df, age_group_col, "Generational Age Distribution", "hr_age_cohort_dist"
            )
            if c:
                demo_charts.append(c)
        elif age_col and age_col in work_df.columns:
            c = ChartBuilder.numeric_histogram(
                work_df, age_col, "Age Cohort Distribution", "hr_age_dist", bins=5, unit="people"
            )
            if c:
                demo_charts.append(c)

        demo_rankings = []
        edu_active = edu_field_col or edu_col
        if edu_active and edu_active in work_df.columns:
            ranking = ChartBuilder.build_ranking(
                work_df, edu_active, edu_active, "Educational Qualifications Profile", "hr_edu_rank", agg="count", unit="people"
            )
            if ranking:
                demo_rankings.append(ranking)

        sections.append(ReportSection(
            id="workforce_demographics",
            title="Workforce Demographics, Parity & Qualifications",
            description="Detailed audit of gender balance, generational age brackets, and academic credential profiles.",
            metrics=[m for m in kpis if m.id in ("average_age", "avg_experience")],
            charts=demo_charts,
            rankings=demo_rankings,
        ))

        # SECTION C: Attrition & Flight Dynamics
        if attrition_rate is not None:
            attr_charts = []
            if dept_col and "__leave_flag" in work_df.columns:
                c = ChartBuilder.rate_by_category(
                    work_df, dept_col, "__leave_flag", "Attrition Rate by Department (%)", "hr_attr_dept"
                )
                if c:
                    attr_charts.append(c)

            if tier_col and "__leave_flag" in work_df.columns:
                c = ChartBuilder.rate_by_category(
                    work_df, tier_col, "__leave_flag", "Attrition Rate by Salary Tier (%)", "hr_attr_tier"
                )
                if c:
                    attr_charts.append(c)

            attr_rankings = []
            if dept_col and "__leave_flag" in work_df.columns:
                d_left = work_df.groupby(dept_col)["__leave_flag"].sum().sort_values(ascending=False)
                items = [
                    RankingItem(
                        rank=idx,
                        label=str(d_name),
                        value=int(cnt),
                        formatted_value=f"{int(cnt):,} departures",
                        pct_of_total=round(cnt / (employees_left or 1) * 100, 1),
                    )
                    for idx, (d_name, cnt) in enumerate(d_left.items(), start=1)
                ]
                attr_rankings.append(ReportRanking(
                    id="hr_churn_rank_table",
                    title="Departmental Departure Concentration",
                    dimension=dept_col,
                    metric="departures",
                    items=items,
                ))

            sections.append(ReportSection(
                id="attrition_retention",
                title="Attrition & Organizational Retention Dynamics",
                description="Analysis of turnover rates across departments, compensation tiers, and organizational corridors.",
                metrics=[m for m in kpis if m.id in ("attrition_rate", "employees_left")],
                charts=attr_charts,
                rankings=attr_rankings,
                callout=f"Organization turnover rate is {attrition_rate:.1f}%, representing {employees_left:,} cumulative departures.",
            ))

        # Anomalies (Only generated when deterministic statistical variance or verified comparative evidence exists)
        anomalies = []

        # Recommendations (Strictly Report-Specific & Evidence-Grounded)
        recommendations: list[ReportRecommendation] = []
        if rpt in ("attrition_analysis", "attrition") and attrition_rate is not None:
            if attr_rankings and len(attr_rankings) > 0 and attr_rankings[0].items:
                top_cohort = attr_rankings[0].items[0]
                recommendations.append(ReportRecommendation(
                    id="rec_retention_cohort_review",
                    title=f"Review High Turnover in {top_cohort.label}",
                    description=f"Conduct targeted retention reviews for the {top_cohort.label} cohort, which recorded the highest departure rate ({top_cohort.formatted_value}).",
                    priority="high",
                    category="retention",
                ))

        elif rpt in ("age_analysis", "age_demographics", "demographics"):
            recommendations.append(ReportRecommendation(
                id="rec_age_succession",
                title="Align Workforce Demographics with Succession Planning",
                description="Evaluate age cohort concentrations alongside organizational experience to maintain continuity in critical roles.",
                priority="medium",
                category="workforce_planning",
            ))
        elif rpt in ("city_analysis", "location_analysis"):
            recommendations.append(ReportRecommendation(
                id="rec_location_allocation",
                title="Review Regional Office Distribution",
                description="Assess headcount balance and operational capacity across monitored regional office locations.",
                priority="medium",
                category="operations",
            ))
        elif rpt in ("education_analysis",):
            recommendations.append(ReportRecommendation(
                id="rec_education_skills",
                title="Review Educational Profile Alignment",
                description="Incorporate educational degree distributions into technical training and upskilling programs.",
                priority="low",
                category="optimization",
            ))
        elif rpt == "workforce_overview":
            recommendations.append(ReportRecommendation(
                id="rec_workforce_monitoring",
                title="Maintain Baseline Workforce Audits",
                description="Continue structured tracking of active headcount and organizational roster attributes.",
                priority="low",
                category="governance",
            ))

        return kpis, sections, anomalies, recommendations

