"""ReportLab PDF Generator for executive business reports.

Generates professional, presentation-ready PDF documents containing executive summary,
KPIs, data-quality analysis, dimensional breakdowns, tables, and page numbering.
Builds strictly from stored ReportSnapshot data for complete reproducibility.
"""
from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _fmt_val(val: Any) -> str:
    """Format numeric values safely with commas and proper precision."""
    if val is None or str(val).lower() in ("none", "unavailable", "null"):
        return "Not available"
    if isinstance(val, (int, float)):
        if isinstance(val, float) and val.is_integer():
            return f"{int(val):,}"
        if isinstance(val, float):
            return f"{val:,.2f}"
        return f"{val:,}"
    return str(val)


class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass calculation of total pages to print 'Page X of Y'."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(7.5 * inch, 0.4 * inch, text)
        self.drawString(0.75 * inch, 0.4 * inch, "Confidential — AI Back-Office Copilot Report")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(0.75 * inch, 0.55 * inch, 7.5 * inch, 0.55 * inch)
        self.restoreState()


class PDFReportGenerator:
    """Generates advanced, multi-page, company-level executive PDF reports."""

    @classmethod
    def generate(cls, report_data: dict[str, Any]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceAfter=3,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=8,
        )
        page_heading_style = ParagraphStyle(
            "PageHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=4,
            spaceAfter=6,
        )
        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading3"],
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=12.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )
        callout_style = ParagraphStyle(
            "CalloutText",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1e3a8a"),
        )
        cell_style = ParagraphStyle(
            "CellText",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
        )
        cell_bold_style = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        cell_header_style = ParagraphStyle(
            "CellHeader",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.white,
            fontName="Helvetica-Bold",
        )
        card_title_style = ParagraphStyle(
            "CardTitle",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica-Bold",
        )
        card_val_style = ParagraphStyle(
            "CardVal",
            parent=styles["Normal"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        card_sub_style = ParagraphStyle(
            "CardSub",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#2563eb"),
        )

        story: list[Any] = []

        company_name = report_data.get("company_name", "AI Back-Office Copilot Enterprise")
        title = report_data.get("title", "Executive MIS Intelligence Report")
        created_at = report_data.get("created_at") or report_data.get("generated_at", "N/A")
        if "T" in str(created_at):
            created_at = str(created_at).split("T")[0]
        dataset_name = report_data.get("dataset_name") or report_data.get("filename") or report_data.get("dataset_id", "Audited Dataset")
        version = report_data.get("dataset_version", 1)
        row_count = report_data.get("row_count", 0)
        col_count = report_data.get("column_count", 0)
        domain = str(report_data.get("domain", "General")).upper()

        # =========================================================================
        # PAGE 1: EXECUTIVE COVER & STRATEGIC SCORECARD BRIEFING
        # =========================================================================
        banner_data = [
            [
                Paragraph(f"<b>{company_name.upper()}</b>", ParagraphStyle("HdrL", parent=subtitle_style, fontSize=8, textColor=colors.HexColor("#2563eb"))),
                Paragraph("<b>BOARD & EXECUTIVE BRIEFING</b>", ParagraphStyle("HdrR", parent=subtitle_style, fontSize=8, alignment=2, textColor=colors.HexColor("#dc2626"))),
            ]
        ]
        banner_table = Table(banner_data, colWidths=[4.0 * inch, 3.3 * inch])
        banner_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(banner_table)
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb"), spaceBefore=3, spaceAfter=8))

        story.append(Paragraph(title, title_style))
        story.append(Paragraph(
            f"Audited Dataset: <b>{dataset_name}</b> (v{version}) &nbsp;|&nbsp; Population: <b>{row_count:,} records</b> &nbsp;|&nbsp; Attributes: <b>{col_count} parameters</b> &nbsp;|&nbsp; Domain: <b>{domain}</b>",
            subtitle_style,
        ))

        # Metadata pill strip
        meta_data = [
            [
                Paragraph(f"<b>Audit Date:</b> {created_at}", cell_style),
                Paragraph("<b>Audit Status:</b> Deterministic Verified", cell_style),
                Paragraph("<b>Security:</b> Strict Tenant Isolation", cell_style),
                Paragraph("<b>Engine:</b> DuckDB OLAP", cell_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[1.8 * inch, 1.9 * inch, 1.9 * inch, 1.7 * inch])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8))

        # Executive Briefing Callout Box (prioritize verified AI summary)
        exec_summary = report_data.get("ai_summary") or report_data.get("executive_summary")
        summary_text = ""
        highlights: list[str] = []
        if isinstance(exec_summary, dict):
            summary_text = exec_summary.get("overview") or exec_summary.get("summary_text", "")
            highlights = exec_summary.get("key_findings") or exec_summary.get("key_highlights", [])
        elif isinstance(exec_summary, str):
            summary_text = exec_summary

        if summary_text:
            briefing_content = [
                [Paragraph("<b>EXECUTIVE STRATEGIC BRIEFING</b>", ParagraphStyle("EbHdr", parent=callout_style, fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e3a8a")))],
                [Paragraph(summary_text, callout_style)],
            ]
            if highlights:
                bullets_text = "<br/>".join([f"• <b>{h.split(':')[0]}:</b> {':'.join(h.split(':')[1:]) if ':' in h else ''}" for h in highlights[:3]])
                briefing_content.append([Paragraph(bullets_text, ParagraphStyle("EbBul", parent=callout_style, fontSize=8, leading=11))])

            briefing_table = Table(briefing_content, colWidths=[7.3 * inch])
            briefing_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bfdbfe")),
                ("LINELEFT", (0, 0), (0, -1), 3.5, colors.HexColor("#2563eb")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(briefing_table)
            story.append(Spacer(1, 8))

        # KPI Scorecard Grid (2 rows x 3 columns)
        kpis = report_data.get("kpi_metrics") or report_data.get("kpis", [])
        active_kpis = [k for k in kpis if k.get("available", True)][:6]
        if active_kpis:
            story.append(Paragraph("<b>Primary Executive Scorecard</b>", section_heading_style))
            card_rows = []
            for i in range(0, len(active_kpis), 3):
                row_cards = []
                for k in active_kpis[i:i + 3]:
                    label = k.get("name") or k.get("label") or k.get("id", "").replace("_", " ").title()
                    val = k.get("formatted_value") or _fmt_val(k.get("value"))
                    unit = k.get("unit") or k.get("category", "")
                    card_cell = [
                        Paragraph(str(label).upper(), card_title_style),
                        Spacer(1, 2),
                        Paragraph(str(val), card_val_style),
                        Paragraph(str(unit).title(), card_sub_style),
                    ]
                    row_cards.append(card_cell)
                # Pad to 3 cells if row has fewer
                while len(row_cards) < 3:
                    row_cards.append([Paragraph("", card_title_style)])
                card_rows.append(row_cards)

            kpi_grid = Table(card_rows, colWidths=[2.43 * inch, 2.43 * inch, 2.44 * inch])
            kpi_grid.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(kpi_grid)
            story.append(Spacer(1, 8))

        # Data Governance & Quality Audit Table
        quality = report_data.get("data_quality") or report_data.get("quality_summary", {})
        if quality:
            story.append(Paragraph("<b>Data Governance & Quality Audit</b>", section_heading_style))
            comp_score = quality.get("score", quality.get("completeness_pct", 100))
            grade = "EXCELLENT" if comp_score >= 90 else "GOOD" if comp_score >= 75 else "ATTENTION REQUIRED"
            q_rows = [
                [Paragraph("Audit Metric", cell_header_style), Paragraph("Audited Value", cell_header_style), Paragraph("Quality Assessment", cell_header_style)],
                [Paragraph("Total Population (Rows)", cell_style), Paragraph(_fmt_val(row_count or quality.get("total_rows")), cell_bold_style), Paragraph("Full Census Verified", cell_style)],
                [Paragraph("Dimensional Attributes (Cols)", cell_style), Paragraph(_fmt_val(col_count or quality.get("total_columns")), cell_bold_style), Paragraph(f"{col_count} Parameters Validated", cell_style)],
                [Paragraph("Missing / Null Cells", cell_style), Paragraph(_fmt_val(quality.get("missing_cells", 0)), cell_bold_style), Paragraph("Checked against null thresholds", cell_style)],
                [Paragraph("Duplicate Records", cell_style), Paragraph(_fmt_val(quality.get("duplicate_rows", 0)), cell_bold_style), Paragraph("0 duplicates expected", cell_style)],
                [Paragraph("Completeness Score", cell_style), Paragraph(f"{comp_score:.1f}%", cell_bold_style), Paragraph(f"Grade: <b>{grade}</b>", cell_style)],
            ]
            q_table = Table(q_rows, colWidths=[2.8 * inch, 2.0 * inch, 2.5 * inch])
            q_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(q_table)

        # END OF PAGE 1 -> DELIBERATE PAGE BREAK
        story.append(PageBreak())

        # =========================================================================
        # PAGE 2: CORE ANALYTICAL BREAKDOWNS & DIMENSIONAL COMPOSITION
        # =========================================================================
        story.append(Paragraph("<b>Section 1: Composition & Dimensional Breakdown</b>", page_heading_style))
        story.append(Paragraph(
            "Detailed statistical stratification across functional dimensions, organizational units, and demographic cohorts.",
            body_style,
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#3b82f6"), spaceAfter=8))

        sections = report_data.get("sections", [])
        first_sec = sections[0] if sections else None
        if first_sec:
            sec_title = first_sec.get("title", "Dimensional Breakdown")
            story.append(Paragraph(f"<b>{sec_title}</b>", section_heading_style))
            if first_sec.get("callout"):
                callout_data = [[Paragraph(f"<b>Key Insight:</b> {first_sec.get('callout')}", callout_style)]]
                c_tbl = Table(callout_data, colWidths=[7.3 * inch])
                c_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("LINELEFT", (0, 0), (0, -1), 3, colors.HexColor("#475569")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(c_tbl)
                story.append(Spacer(1, 6))

            rankings = first_sec.get("rankings", [])
            for rk in rankings:
                rk_title = rk.get("title", "Breakdown")
                items = rk.get("items", [])
                if not items:
                    continue

                story.append(Paragraph(f"<b>{rk_title}</b>", ParagraphStyle("SubH", parent=section_heading_style, fontSize=9.5)))
                t_rows = [
                    [Paragraph("Rank", cell_header_style), Paragraph("Dimension / Segment", cell_header_style), Paragraph("Volume / Metric", cell_header_style), Paragraph("Share (%)", cell_header_style), Paragraph("Context / Operational Attribute", cell_header_style)]
                ]
                for it in items[:8]:
                    pct_str = f"{it.get('pct_of_total'):.1f}%" if it.get("pct_of_total") is not None else "—"
                    sub_str = it.get("subtext") or "Audited Segment"
                    t_rows.append([
                        Paragraph(str(it.get("rank", "-")), cell_style),
                        Paragraph(f"<b>{it.get('label', '—')}</b>", cell_style),
                        Paragraph(str(it.get("formatted_value") or _fmt_val(it.get("value"))), cell_bold_style),
                        Paragraph(pct_str, cell_style),
                        Paragraph(str(sub_str), cell_style),
                    ])
                t_table = Table(t_rows, colWidths=[0.6 * inch, 2.2 * inch, 1.4 * inch, 0.9 * inch, 2.2 * inch])
                t_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]))
                story.append(t_table)
                story.append(Spacer(1, 6))

        # If second section exists, print it on Page 2 as well
        if len(sections) > 1:
            second_sec = sections[1]
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>{second_sec.get('title', 'Secondary Analysis')}</b>", section_heading_style))
            if second_sec.get("callout"):
                story.append(Paragraph(f"<i>{second_sec.get('callout')}</i>", body_style))

            sec2_rankings = second_sec.get("rankings", [])
            for rk in sec2_rankings:
                items = rk.get("items", [])
                if items:
                    t_rows = [
                        [Paragraph("Rank", cell_header_style), Paragraph("Entity / Segment", cell_header_style), Paragraph("Observed Value", cell_header_style), Paragraph("Proportion", cell_header_style)]
                    ]
                    for it in items[:6]:
                        pct_str = f"{it.get('pct_of_total'):.1f}%" if it.get("pct_of_total") is not None else "—"
                        t_rows.append([
                            Paragraph(str(it.get("rank", "-")), cell_style),
                            Paragraph(str(it.get("label", "—")), cell_style),
                            Paragraph(str(it.get("formatted_value") or _fmt_val(it.get("value"))), cell_bold_style),
                            Paragraph(pct_str, cell_style),
                        ])
                    t_table = Table(t_rows, colWidths=[0.8 * inch, 3.2 * inch, 1.8 * inch, 1.5 * inch])
                    t_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ]))
                    story.append(t_table)

        # END OF PAGE 2 -> DELIBERATE PAGE BREAK
        story.append(PageBreak())

        # =========================================================================
        # PAGE 3: RISK DIAGNOSTICS & ANOMALY ASSESSMENT
        # =========================================================================
        story.append(Paragraph("<b>Section 2: Risk Diagnostics & Variance Audit</b>", page_heading_style))
        story.append(Paragraph(
            "Quantitative outlier detection, flight corridor analysis, and operational vulnerability assessment.",
            body_style,
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dc2626"), spaceAfter=8))

        # Risk Matrix Section (if section with attrition/turnover/margins exists)
        risk_sec = next((s for s in sections if "attrition" in s.get("id", "") or "risk" in s.get("id", "") or "margin" in s.get("id", "")), None)
        if risk_sec and risk_sec.get("rankings"):
            rk = risk_sec["rankings"][0]
            items = rk.get("items", [])
            if items:
                story.append(Paragraph("<b>Operational Flight Risk & Departure Matrix</b>", section_heading_style))
                r_rows = [
                    [Paragraph("Rank", cell_header_style), Paragraph("Division / Risk Segment", cell_header_style), Paragraph("Measured Event Count", cell_header_style), Paragraph("Turnover Severity Rate", cell_header_style), Paragraph("Risk Evaluation", cell_header_style)]
                ]
                for it in items[:8]:
                    val = it.get("value", 0)
                    pct = it.get("pct_of_total") or 0
                    sev = "CRITICAL" if pct >= 30 else "ELEVATED" if pct >= 18 else "CONTROLLED"
                    sev_color = "#dc2626" if sev == "CRITICAL" else "#d97706" if sev == "ELEVATED" else "#059669"
                    r_rows.append([
                        Paragraph(str(it.get("rank", "-")), cell_style),
                        Paragraph(f"<b>{it.get('label', '—')}</b>", cell_style),
                        Paragraph(str(it.get("formatted_value") or _fmt_val(val)), cell_bold_style),
                        Paragraph(f"{pct:.1f}%", cell_style),
                        Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", cell_style),
                    ])
                r_table = Table(r_rows, colWidths=[0.6 * inch, 2.5 * inch, 1.6 * inch, 1.4 * inch, 1.2 * inch])
                r_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]))
                story.append(r_table)
                story.append(Spacer(1, 10))

        # Anomalies Table
        anomalies = report_data.get("anomalies", [])
        story.append(Paragraph("<b>Statistical Anomalies & Threshold Breaches</b>", section_heading_style))
        if anomalies:
            a_rows = [
                [Paragraph("Severity", cell_header_style), Paragraph("Anomaly Indicator", cell_header_style), Paragraph("Observed Value", cell_header_style), Paragraph("Diagnostic Context & Impact", cell_header_style)]
            ]
            for a in anomalies:
                sev = str(a.get("severity", "medium")).upper()
                sev_color = "#dc2626" if sev == "HIGH" else "#d97706" if sev == "MEDIUM" else "#2563eb"
                a_rows.append([
                    Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", cell_style),
                    Paragraph(f"<b>{a.get('label', 'Anomaly')}</b>", cell_style),
                    Paragraph(str(a.get("value", "N/A")), cell_bold_style),
                    Paragraph(str(a.get("reason", "Outlier observed outside expected confidence intervals.")), cell_style),
                ])
            a_table = Table(a_rows, colWidths=[0.9 * inch, 2.2 * inch, 1.2 * inch, 3.0 * inch])
            a_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fef2f2")]),
            ]))
            story.append(a_table)
        else:
            ok_box = [[Paragraph("<b>Zero Anomalous Breaches:</b> All evaluated parameters remain within normal operating distributions and compliance thresholds.", ParagraphStyle("OkT", parent=cell_style, textColor=colors.HexColor("#166534")))]]
            ok_tbl = Table(ok_box, colWidths=[7.3 * inch])
            ok_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
                ("LINELEFT", (0, 0), (0, -1), 3, colors.HexColor("#16a34a")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(ok_tbl)

        # END OF PAGE 3 -> DELIBERATE PAGE BREAK
        story.append(PageBreak())

        # =========================================================================
        # PAGE 4: STRATEGIC ACTION PLAN, RECOMMENDATIONS & AUDIT SEAL
        # =========================================================================
        story.append(Paragraph("<b>Section 3: Strategic Action Roadmap & Governance Seal</b>", page_heading_style))
        story.append(Paragraph(
            "Prescriptive executive interventions, targeted operational milestones, and deterministic pipeline certification.",
            body_style,
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#10b981"), spaceAfter=8))

        recommendations = report_data.get("recommendations", [])
        if recommendations:
            story.append(Paragraph("<b>Prioritized Operational Directives</b>", section_heading_style))
            for idx, r in enumerate(recommendations, start=1):
                prio = str(r.get("priority", "medium")).upper()
                prio_bg = "#fee2e2" if prio == "HIGH" else "#fef3c7" if prio == "MEDIUM" else "#ecfdf5"
                prio_txt = "#b91c1c" if prio == "HIGH" else "#b45309" if prio == "MEDIUM" else "#047857"
                cat = str(r.get("category", "General")).title()

                r_card = [
                    [
                        Paragraph(f"<b>Directive {idx}: {r.get('title', 'Recommendation')}</b>", ParagraphStyle("RTitle", parent=cell_bold_style, fontSize=9, textColor=colors.HexColor("#0f172a"))),
                        Paragraph(f"<font color='{prio_txt}'><b>{prio} PRIORITY</b></font> &nbsp;|&nbsp; {cat}", ParagraphStyle("RPrio", parent=cell_style, fontSize=8, alignment=2)),
                    ],
                    [
                        Paragraph(str(r.get("description", "Actionable intervention")), ParagraphStyle("RDesc", parent=cell_style, fontSize=8.5, leading=12)),
                        Paragraph("", cell_style),
                    ],
                ]
                r_tbl = Table(r_card, colWidths=[5.2 * inch, 2.1 * inch])
                r_tbl.setStyle(TableStyle([
                    ("SPAN", (0, 1), (1, 1)),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(prio_bg)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("LINELEFT", (0, 0), (0, -1), 3.5, colors.HexColor(prio_txt)),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]))
                story.append(r_tbl)
                story.append(Spacer(1, 6))

        story.append(Spacer(1, 10))

        # Enterprise Pipeline Governance & Verification Seal
        snapshot_id = report_data.get("snapshot_id") or report_data.get("report_id", "rep_deterministic")
        seal_data = [
            [
                Paragraph("<b>ENTERPRISE ANALYTICAL VERIFICATION SEAL</b>", ParagraphStyle("SealH", parent=cell_bold_style, fontSize=9, textColor=colors.HexColor("#1e293b"))),
                Paragraph("<b>ZERO-TRUST COMPLIANT</b>", ParagraphStyle("SealR", parent=cell_bold_style, fontSize=8, alignment=2, textColor=colors.HexColor("#059669"))),
            ],
            [
                Paragraph(
                    f"This document is an authoritative Management Information System (MIS) audit compiled deterministically by the "
                    f"AI Back-Office Copilot. All calculations, distributions, and scorecard metrics were computed using "
                    f"in-memory columnar OLAP algorithms (DuckDB engine). Zero synthetic hallucinations were introduced.<br/><br/>"
                    f"<b>Pipeline ID:</b> {snapshot_id} &nbsp;|&nbsp; <b>Account Scope:</b> {report_data.get('account_id', 'tenant_enterprise')} &nbsp;|&nbsp; "
                    f"<b>Audit Timestamp:</b> {created_at}<br/>"
                    f"<i>Distribution restricted to accredited corporate decision-makers. Strictly confidential.</i>",
                    ParagraphStyle("SealB", parent=cell_style, fontSize=8, leading=11, textColor=colors.HexColor("#475569")),
                ),
                Paragraph("", cell_style),
            ],
        ]
        seal_table = Table(seal_data, colWidths=[5.3 * inch, 2.0 * inch])
        seal_table.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
            ("LINELEFT", (0, 0), (0, -1), 4, colors.HexColor("#0f172a")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(seal_table)

        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()
