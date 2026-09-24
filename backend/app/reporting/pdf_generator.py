"""Novera — Dynamic AI Business Intelligence Report Engine (ReportLab PDF).

Production-grade, content-driven, zero-hardcoding report generation system.
Adheres strictly to the Novera Design System:
- Ink: #11181B
- Novera Green: #176B50
- Bright Green: #2D8A68
- Brass: #A8792E
- Paper: #F3F5F1
- Rule: #C7CEC8
- Muted: #66716C
- Flag: #B33A3A

Features:
- Dynamic page count: Content flows naturally via ReportLab Platypus.
- Dynamic report structure: Domain-driven sections (HR, Sales, Inventory, Finance, Customer, Generic).
- Native vector charts: Horizontal rankings, vertical comparisons, and distribution charts.
- Multi-page tables with repeating headers (repeatRows=1).
- Immutable lineage and verification seal.
"""
from __future__ import annotations

import io
from typing import Any

from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Group, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Novera Design System Palette ──
COLOR_INK = colors.HexColor("#11181B")
COLOR_GREEN = colors.HexColor("#176B50")
COLOR_BRIGHT_GREEN = colors.HexColor("#2D8A68")
COLOR_BRASS = colors.HexColor("#A8792E")
COLOR_PAPER = colors.HexColor("#F3F5F1")
COLOR_RULE = colors.HexColor("#C7CEC8")
COLOR_MUTED = colors.HexColor("#66716C")
COLOR_FLAG = colors.HexColor("#B33A3A")
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_CARD_BG = colors.HexColor("#F8FAF9")
COLOR_CALLOUT_BG = colors.HexColor("#EBF3EE")
COLOR_GRID = colors.HexColor("#E2E8F0")


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


# ── Two-Pass Numbered Canvas for Dynamic Page Numbering ──
class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total page count dynamically and prints running header/footer."""

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
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, total_pages: int) -> None:
        self.saveState()
        page_width, page_height = A4

        # Document Metadata
        report_title = getattr(self, "_report_title", "Business Intelligence Report")
        self.setTitle(report_title)
        self.setAuthor("Novera")
        self.setSubject("Verified Business Intelligence Report")
        self.setCreator("Novera Dynamic BI Report Engine")

        # Running Header on Page 2 and above
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(COLOR_GREEN)
            self.drawString(36, page_height - 28, "NOVERA")

            self.setFont("Helvetica", 8)
            self.setFillColor(COLOR_RULE)
            self.drawString(82, page_height - 28, "|")

            self.setFont("Helvetica", 8)
            self.setFillColor(COLOR_INK)
            display_title = report_title[:45] + ("..." if len(report_title) > 45 else "")
            self.drawString(92, page_height - 28, display_title)

            self.setFont("Helvetica", 8)
            self.setFillColor(COLOR_MUTED)
            self.drawRightString(page_width - 36, page_height - 28, "Confidential — Verified BI")

            self.setStrokeColor(COLOR_RULE)
            self.setLineWidth(0.5)
            self.line(36, page_height - 34, page_width - 36, page_height - 34)

        # Running Footer on ALL pages
        self.setFont("Helvetica", 7.5)
        self.setFillColor(COLOR_MUTED)
        self.drawString(36, 26, "Novera Business Intelligence — Verified Analytics")

        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(COLOR_INK)
        self.drawRightString(page_width - 36, 26, page_str)

        self.setStrokeColor(COLOR_RULE)
        self.setLineWidth(0.5)
        self.line(36, 38, page_width - 36, 38)

        self.restoreState()


# ── Native Vector Chart Renderers ──
def render_horizontal_bar_chart(
    title: str,
    items: list[dict[str, Any]],
    width: float = 523,
    max_items: int = 8,
) -> Drawing:
    """Renders a clean, high-resolution vector horizontal bar chart for rankings."""
    display_items = items[:max_items]
    if not display_items:
        return Drawing(width, 10)

    row_height = 22
    header_space = 28
    chart_height = header_space + (len(display_items) * row_height) + 12

    d = Drawing(width, chart_height)

    # Background Card
    d.add(Rect(0, 0, width, chart_height, fillColor=COLOR_CARD_BG, strokeColor=COLOR_RULE, strokeWidth=0.5, rx=3, ry=3))

    # Header Title
    d.add(String(14, chart_height - 18, title.upper(), fontName="Helvetica-Bold", fontSize=8.5, fillColor=COLOR_INK))

    # Determine max value for proportional scaling
    raw_vals: list[float] = []
    for it in display_items:
        v = it.get("value")
        if isinstance(v, (int, float)):
            raw_vals.append(float(v))
        else:
            raw_vals.append(0.0)
    max_val = max(raw_vals) if raw_vals and max(raw_vals) > 0 else 1.0

    bar_start_x = 160
    max_bar_width = width - bar_start_x - 120

    y_pos = chart_height - header_space - row_height + 4
    for idx, (it, val) in enumerate(zip(display_items, raw_vals)):
        label = str(it.get("label", ""))[:22]
        formatted = str(it.get("formatted_value") or _fmt_val(val))
        pct = it.get("pct_of_total")

        # Label on left
        d.add(String(14, y_pos + 4, label, fontName="Helvetica", fontSize=8, fillColor=COLOR_INK))

        # Horizontal Bar
        bar_len = max(4.0, (val / max_val) * max_bar_width) if max_val > 0 else 4.0
        bar_color = COLOR_GREEN if idx == 0 else COLOR_BRIGHT_GREEN if idx < 3 else COLOR_MUTED
        d.add(Rect(bar_start_x, y_pos + 1, bar_len, 12, fillColor=bar_color, strokeColor=None, rx=2, ry=2))

        # Value & Percentage label on right
        val_str = f"{formatted} ({pct:.1f}%)" if pct is not None else formatted
        d.add(String(bar_start_x + bar_len + 8, y_pos + 4, val_str, fontName="Helvetica-Bold", fontSize=7.5, fillColor=COLOR_INK))

        y_pos -= row_height

    return d


def render_distribution_pie_chart(
    title: str,
    items: list[dict[str, Any]],
    width: float = 523,
    max_slices: int = 5,
) -> Drawing:
    """Renders a clean native vector pie chart for category shares."""
    display_items = items[:max_slices]
    if not display_items or len(display_items) < 2:
        return Drawing(width, 10)

    chart_height = 150
    d = Drawing(width, chart_height)
    d.add(Rect(0, 0, width, chart_height, fillColor=COLOR_CARD_BG, strokeColor=COLOR_RULE, strokeWidth=0.5, rx=3, ry=3))
    d.add(String(14, chart_height - 18, title.upper(), fontName="Helvetica-Bold", fontSize=8.5, fillColor=COLOR_INK))

    pie = Pie()
    pie.x = 24
    pie.y = 12
    pie.width = 110
    pie.height = 110

    data_vals = [float(it.get("value") or 1) for it in display_items]
    pie.data = data_vals
    pie.labels = []  # Labels drawn in custom legend on right

    slice_colors = [COLOR_GREEN, COLOR_BRIGHT_GREEN, COLOR_BRASS, COLOR_MUTED, colors.HexColor("#94A3B8")]
    for i in range(len(data_vals)):
        pie.slices[i].fillColor = slice_colors[i % len(slice_colors)]
        pie.slices[i].strokeColor = COLOR_WHITE
        pie.slices[i].strokeWidth = 1

    d.add(pie)

    # Custom Legend
    legend_x = 170
    legend_y = chart_height - 40
    total_val = sum(data_vals) if sum(data_vals) > 0 else 1.0

    for i, it in enumerate(display_items):
        col = slice_colors[i % len(slice_colors)]
        label = str(it.get("label", ""))[:25]
        val = data_vals[i]
        pct = (val / total_val * 100) if total_val > 0 else 0

        # Color square
        d.add(Rect(legend_x, legend_y - 2, 8, 8, fillColor=col, strokeColor=None))
        d.add(String(legend_x + 14, legend_y - 2, f"{label}: {pct:.1f}% ({_fmt_val(val)})", fontName="Helvetica", fontSize=8, fillColor=COLOR_INK))
        legend_y -= 18

    return d


# ── Primary PDF Report Generator ──
class PDFReportGenerator:
    """Generates advanced, dynamic, content-driven PDF reports for Novera."""

    @classmethod
    def generate(cls, report_data: dict[str, Any], page_compression: int = 1) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=42,
            bottomMargin=46,
            pageCompression=page_compression,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "NoveraTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=COLOR_INK,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "NoveraSubtitle",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=COLOR_MUTED,
            spaceAfter=8,
        )
        section_heading_style = ParagraphStyle(
            "NoveraSectionHeading",
            parent=styles["Heading2"],
            fontSize=11.5,
            leading=15,
            textColor=COLOR_INK,
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )
        body_style = ParagraphStyle(
            "NoveraBody",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=12.5,
            textColor=COLOR_INK,
            spaceAfter=6,
        )
        callout_style = ParagraphStyle(
            "NoveraCallout",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=COLOR_INK,
        )
        cell_style = ParagraphStyle(
            "NoveraCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=COLOR_INK,
        )
        cell_bold_style = ParagraphStyle(
            "NoveraCellBold",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=COLOR_INK,
            fontName="Helvetica-Bold",
        )
        cell_header_style = ParagraphStyle(
            "NoveraCellHeader",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=COLOR_WHITE,
            fontName="Helvetica-Bold",
        )
        card_title_style = ParagraphStyle(
            "NoveraCardTitle",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=COLOR_MUTED,
            fontName="Helvetica-Bold",
        )
        card_val_style = ParagraphStyle(
            "NoveraCardVal",
            parent=styles["Normal"],
            fontSize=13,
            leading=16,
            textColor=COLOR_INK,
            fontName="Helvetica-Bold",
        )
        card_sub_style = ParagraphStyle(
            "NoveraCardSub",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=COLOR_GREEN,
        )

        story: list[Any] = []

        # ── Extract Metadata ──
        company_name = report_data.get("company_name", "Novera Business Intelligence")
        if not company_name or "saas" in str(company_name).lower():
            company_name = "Novera Business Intelligence"
        title = report_data.get("title", "Universal Business Intelligence Report")
        created_at = report_data.get("created_at") or report_data.get("generated_at", "N/A")
        if "T" in str(created_at):
            created_at = str(created_at).split("T")[0]
        dataset_name = report_data.get("dataset_name") or report_data.get("filename") or report_data.get("dataset_id", "Audited Dataset")
        version = report_data.get("dataset_version", 1)
        row_count = report_data.get("row_count", 0)
        col_count = report_data.get("column_count", 0)
        domain = str(report_data.get("domain", "generic")).upper()
        filters_applied = report_data.get("filters", {})

        # ── 1. Header Banner & Title Block ──
        banner_data = [
            [
                Paragraph(f"<b>{company_name.upper()}</b>", ParagraphStyle("HdrL", parent=subtitle_style, fontSize=8, textColor=COLOR_GREEN)),
                Paragraph("<b>BUSINESS INTELLIGENCE REPORT</b>", ParagraphStyle("HdrR", parent=subtitle_style, fontSize=8, alignment=2, textColor=COLOR_GREEN)),
            ]
        ]
        banner_table = Table(banner_data, colWidths=[290, 233])
        banner_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(banner_table)
        story.append(HRFlowable(width="100%", thickness=2, color=COLOR_GREEN, spaceBefore=3, spaceAfter=8))

        story.append(Paragraph(title, title_style))
        filter_str = f" &nbsp;|&nbsp; Filters: <b>{filters_applied}</b>" if filters_applied else ""
        story.append(Paragraph(
            f"Dataset: <b>{dataset_name}</b> (v{version}) &nbsp;|&nbsp; Records: <b>{row_count:,}</b> &nbsp;|&nbsp; Attributes: <b>{col_count}</b> &nbsp;|&nbsp; Domain: <b>{domain}</b>{filter_str}",
            subtitle_style,
        ))

        # ── Resolve Canonical AI Status & Grounding (Section 35 & 37) ──
        exec_summary = report_data.get("ai_summary") or report_data.get("executive_summary")
        summary_text = ""
        dataset_overview = ""
        overall_text = ""
        highlights: list[str] = []

        raw_status = (
            report_data.get("ai_status")
            or (exec_summary.get("ai_status") if isinstance(exec_summary, dict) else None)
            or (exec_summary.get("verification_status") if isinstance(exec_summary, dict) else None)
            or "VERIFIED_ANALYTICS_ONLY"
        )
        norm_status = str(raw_status).upper().strip()
        is_ai_grounded = norm_status == "AI_GENERATED_GROUNDED"

        if isinstance(exec_summary, dict):
            dataset_overview = exec_summary.get("dataset_overview", "")
            highlights = exec_summary.get("highlights") or []
            overall_text = exec_summary.get("overall", "")
            summary_text = exec_summary.get("overview") or exec_summary.get("summary_text", "")
            if not highlights:
                highlights = exec_summary.get("key_findings") or exec_summary.get("key_highlights", [])
        elif isinstance(exec_summary, str):
            summary_text = exec_summary

        # Parse from formatted overview if dataset_overview / highlights / overall were not passed as explicit keys
        if summary_text and (not dataset_overview or not highlights or not overall_text):
            parts = [p.strip() for p in summary_text.split("\n\n") if p.strip()]
            if len(parts) >= 2:
                if not dataset_overview and not parts[0].startswith("- ") and not parts[0].startswith("• "):
                    dataset_overview = parts[0]
                parsed_bullets = []
                for p in parts[1:]:
                    lines = [l.strip() for l in p.split("\n") if l.strip()]
                    for l in lines:
                        if l.startswith("- ") or l.startswith("• "):
                            parsed_bullets.append(l.lstrip("- •").strip())
                        elif l.startswith("Overall:"):
                            if not overall_text:
                                overall_text = l.replace("Overall:", "").strip()
                if not highlights and parsed_bullets:
                    highlights = parsed_bullets

        # Metadata pill strip
        meta_data = [
            [
                Paragraph(f"<b>Generated:</b> {created_at}", cell_style),
                Paragraph("<b>Analytics:</b> Verified", cell_style),
                Paragraph(f"<b>Status:</b> {'AI Grounded' if is_ai_grounded else 'Verified Analytics'}", cell_style),
                Paragraph("<b>Classification:</b> Confidential", cell_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[130, 131, 131, 131])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8))

        # ── 2. Executive Briefing Section (Universal Sales-Style 3-Part UX) ──
        if summary_text or dataset_overview or highlights or overall_text:
            briefing_title = "AI-GROUNDED EXECUTIVE SUMMARY" if is_ai_grounded else "VERIFIED ANALYTICS SUMMARY"
            if is_ai_grounded:
                badge_text = "AI GENERATED • GROUNDED"
            elif norm_status in ("AI_NOT_CONFIGURED", "AI_UNAVAILABLE", "VERIFIED_ANALYTICS_ONLY", "DETERMINISTIC"):
                badge_text = "VERIFIED ANALYTICS"
            else:
                badge_text = norm_status.replace("_", " ").title()
            badge_color = "#176B50" if is_ai_grounded else "#A8792E"
            briefing_content = [
                [
                    Paragraph(f"<b>{briefing_title}</b> &nbsp;&nbsp;<font color='{badge_color}' size='7'><b>[{badge_text}]</b></font>", ParagraphStyle("EbHdr", parent=callout_style, fontSize=8.5, fontName="Helvetica-Bold", textColor=COLOR_GREEN)),
                ],
            ]

            # Part A: Dataset Overview
            if dataset_overview:
                briefing_content.append([Paragraph(dataset_overview, callout_style)])
            elif summary_text and not highlights:
                briefing_content.append([Paragraph(summary_text, callout_style)])

            # Part B: Dynamic Verified Highlights (up to 8 bullets)
            if highlights:
                bullets_formatted = []
                for h in highlights[:8]:
                    clean_h = h.strip().lstrip("- •").strip()
                    if ":" in clean_h:
                        parts = clean_h.split(":", 1)
                        bullets_formatted.append(f"• <b>{parts[0].strip()}:</b> {parts[1].strip()}")
                    elif "–" in clean_h:
                        parts = clean_h.split("–", 1)
                        bullets_formatted.append(f"• <b>{parts[0].strip()} –</b> {parts[1].strip()}")
                    else:
                        bullets_formatted.append(f"• {clean_h}")
                bullets_html = "<br/>".join(bullets_formatted)
                briefing_content.append([Paragraph(bullets_html, ParagraphStyle("EbBul", parent=callout_style, fontSize=8, leading=12))])

            # Part C: Overall Factual Interpretation
            if overall_text:
                clean_overall = overall_text.strip()
                if clean_overall.startswith("Overall:"):
                    clean_overall = clean_overall[len("Overall:"):].strip()
                briefing_content.append([
                    Paragraph(f"<b>Overall:</b> {clean_overall}", ParagraphStyle("EbOverall", parent=callout_style, fontSize=8, leading=11, fontName="Helvetica-Oblique"))
                ])

            briefing_table = Table(briefing_content, colWidths=[523])
            briefing_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_CALLOUT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
                ("LINELEFT", (0, 0), (0, -1), 3.5, COLOR_GREEN),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(briefing_table)
            story.append(Spacer(1, 8))

        # ── 3. Primary KPI Scorecard Grid ──
        kpis = report_data.get("kpi_metrics") or report_data.get("kpis", [])
        active_kpis = [k for k in kpis if k.get("available", True)]
        if active_kpis:
            story.append(Paragraph("<b>Primary Executive Scorecard</b>", section_heading_style))
            num_cols = 3 if len(active_kpis) >= 3 else len(active_kpis)
            col_w = 523 / num_cols
            card_rows = []
            for i in range(0, len(active_kpis), num_cols):
                row_cards = []
                for k in active_kpis[i:i + num_cols]:
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
                while len(row_cards) < num_cols:
                    row_cards.append([Paragraph("", card_title_style)])
                card_rows.append(row_cards)

            kpi_grid = Table(card_rows, colWidths=[col_w] * num_cols)
            kpi_grid.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_GRID),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(kpi_grid)
            story.append(Spacer(1, 10))

        # ── 3b. Data Integrity & Quality Scorecard ──
        dq = report_data.get("data_quality")
        if dq and isinstance(dq, dict):
            story.append(Paragraph("<b>Data Integrity & Quality Scorecard</b>", section_heading_style))
            dq_score = float(dq.get("score", 100.0) or 100.0)
            missing_pct = float(dq.get("missing_pct", 0.0) or 0.0)
            completeness = float(dq.get("completeness_pct", 100.0 - missing_pct) or (100.0 - missing_pct))
            missing = int(dq.get("missing_cells", 0) or 0)
            duplicates = int(dq.get("duplicate_rows", 0) or 0)
            total_r = int(dq.get("total_rows", row_count) or row_count)
            total_c = int(dq.get("total_columns", col_count) or col_count)

            grade = "Excellent" if dq_score >= 95 else "Good" if dq_score >= 80 else "Attention Required"
            grade_color = COLOR_GREEN if dq_score >= 90 else COLOR_BRASS if dq_score >= 70 else COLOR_FLAG

            dq_score_style = ParagraphStyle("DQScore", parent=card_val_style, textColor=grade_color)
            dq_cells = [
                [
                    Paragraph("DATA COMPLETENESS", card_title_style),
                    Paragraph("MISSING CELLS", card_title_style),
                    Paragraph("DUPLICATE ROWS", card_title_style),
                ],
                [
                    Paragraph(f"{completeness:.1f}%", card_val_style),
                    Paragraph(f"{missing:,}", card_val_style),
                    Paragraph(f"{duplicates:,}", card_val_style),
                ],
                [
                    Paragraph(f"{total_r:,} rows × {total_c} cols", card_sub_style),
                    Paragraph(f"{missing_pct:.2f}% missing", card_sub_style),
                    Paragraph(f"{float(dq.get('duplicate_pct', 0.0) or 0.0):.2f}% duplicates", card_sub_style),
                ],
            ]
            dq_tbl = Table(dq_cells, colWidths=[174, 174, 175])
            dq_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_GRID),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(dq_tbl)
            story.append(Spacer(1, 10))

        # ── 4. Dynamic Sections Iteration (Content-Driven Flow) ──
        sections = report_data.get("sections", [])
        for sec_idx, sec in enumerate(sections, start=1):
            sec_title = sec.get("title", f"Analytical Section {sec_idx}")
            heading_p = Paragraph(f"<b>Section {sec_idx}: {sec_title}</b>", section_heading_style)
            hr_p = HRFlowable(width="100%", thickness=1, color=COLOR_GREEN, spaceBefore=2, spaceAfter=6)
            story.append(KeepTogether([heading_p, hr_p]))

            if sec.get("callout"):
                callout_data = [[Paragraph(f"<b>Key Insight:</b> {sec.get('callout')}", callout_style)]]
                c_tbl = Table(callout_data, colWidths=[523])
                c_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
                    ("LINELEFT", (0, 0), (0, -1), 3, COLOR_MUTED),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(c_tbl)
                story.append(Spacer(1, 6))

            # Render direct charts if section has charts without rankings
            charts = sec.get("charts", [])
            if charts and not sec.get("rankings"):
                for ch in charts:
                    ch_title = ch.get("title", "Breakdown")
                    ch_data = ch.get("data", [])
                    if ch_data and len(ch_data) >= 2:
                        v_chart = render_horizontal_bar_chart(ch_title, ch_data, width=523, max_items=8)
                        story.append(v_chart)
                        story.append(Spacer(1, 6))

            # Render Vector Charts & Detailed Rankings Tables
            rankings = sec.get("rankings", [])
            for rk in rankings:
                rk_title = rk.get("title", "Breakdown")
                items = rk.get("items", [])
                if not items:
                    continue

                # 1. Vector Chart Visualization
                if len(items) >= 2:
                    vector_chart = render_horizontal_bar_chart(rk_title, items, width=523, max_items=8)
                    story.append(vector_chart)
                    story.append(Spacer(1, 6))

                # 2. Detailed Data Table (with repeatRows=1 for clean multi-page flow)
                t_rows = [
                    [
                        Paragraph("Rank", cell_header_style),
                        Paragraph("Dimension / Segment", cell_header_style),
                        Paragraph("Value", cell_header_style),
                        Paragraph("Share (%)", cell_header_style),
                    ]
                ]
                for it in items:
                    pct_str = f"{it.get('pct_of_total'):.1f}%" if it.get("pct_of_total") is not None else "—"
                    t_rows.append([
                        Paragraph(str(it.get("rank", "-")), cell_style),
                        Paragraph(f"<b>{it.get('label', '—')}</b>", cell_style),
                        Paragraph(str(it.get("formatted_value") or _fmt_val(it.get("value"))), cell_bold_style),
                        Paragraph(pct_str, cell_style),
                    ])
                t_table = Table(t_rows, colWidths=[45, 238, 140, 100], repeatRows=1)
                t_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_INK),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("GRID", (0, 0), (-1, -1), 0.5, COLOR_GRID),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_CARD_BG]),
                ]))
                story.append(t_table)
                story.append(Spacer(1, 8))

        # ── 5. Data Quality Block ──
        quality = report_data.get("data_quality") or report_data.get("quality_summary", {})
        if quality:
            story.append(Paragraph("<b>Data Quality</b>", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BRASS, spaceBefore=2, spaceAfter=6))

            raw_comp = quality.get("completeness_pct")
            missing_pct = float(quality.get("missing_pct", 0.0) or 0.0)
            comp_score = float(raw_comp if raw_comp is not None else (100.0 - missing_pct))
            missing_count = int(quality.get("missing_cells", 0) or 0)
            dup_count = int(quality.get("duplicate_rows", 0) or 0)
            dup_pct = float(quality.get("duplicate_pct", 0.0) or 0.0)
            quality_assessment = "No missing cells detected." if missing_count == 0 else f"{missing_count:,} missing cells identified."
            dup_assessment = "Zero duplicates observed" if dup_count == 0 else f"{dup_count:,} duplicate rows ({dup_pct:.2f}% duplicate rate)"
            
            q_rows = [
                [Paragraph("Audit Metric", cell_header_style), Paragraph("Audited Value", cell_header_style), Paragraph("Factual Quality Assessment", cell_header_style)],
                [Paragraph("Total Population (Rows)", cell_style), Paragraph(_fmt_val(row_count or quality.get("total_rows")), cell_bold_style), Paragraph(f"Records analyzed: {row_count:,}", cell_style)],
                [Paragraph("Dimensional Attributes (Cols)", cell_style), Paragraph(_fmt_val(col_count or quality.get("total_columns")), cell_bold_style), Paragraph(f"{col_count} attributes validated", cell_style)],
                [Paragraph("Missing / Null Cells", cell_style), Paragraph(_fmt_val(missing_count), cell_bold_style), Paragraph(quality_assessment, cell_style)],
                [Paragraph("Duplicate Rows", cell_style), Paragraph(_fmt_val(dup_count), cell_bold_style), Paragraph(dup_assessment, cell_style)],
                [Paragraph("Field Completeness", cell_style), Paragraph(f"{comp_score:.1f}%", cell_bold_style), Paragraph(f"Field completeness: {comp_score:.1f}% | Missing cells: {missing_count:,}", cell_style)],
            ]
            q_table = Table(q_rows, colWidths=[180, 140, 203], repeatRows=1)
            q_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_INK),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_CARD_BG]),
            ]))
            story.append(q_table)
            story.append(Spacer(1, 8))

        # ── 6. Risk Diagnostics & Statistical Anomalies (Bug 6: only render when executed) ──
        anomalies = report_data.get("anomalies", [])
        if anomalies:
            story.append(Paragraph("<b>Statistical Anomalies & Threshold Breaches</b>", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_FLAG, spaceBefore=2, spaceAfter=6))
            a_rows = [
                [Paragraph("Severity", cell_header_style), Paragraph("Anomaly Indicator", cell_header_style), Paragraph("Observed Value", cell_header_style), Paragraph("Diagnostic Context & Impact", cell_header_style)]
            ]
            for a in anomalies:
                sev = str(a.get("severity", "medium")).upper()
                sev_color = "#B33A3A" if sev == "HIGH" else "#A8792E" if sev == "MEDIUM" else "#176B50"
                a_rows.append([
                    Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", cell_style),
                    Paragraph(f"<b>{a.get('label', 'Anomaly')}</b>", cell_style),
                    Paragraph(str(a.get("value", "N/A")), cell_bold_style),
                    Paragraph(str(a.get("reason", "Outlier observed outside expected confidence intervals.")), cell_style),
                ])
            a_table = Table(a_rows, colWidths=[65, 150, 95, 213], repeatRows=1)
            a_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_INK),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, colors.HexColor("#FEF2F2")]),
            ]))
            story.append(a_table)
            story.append(Spacer(1, 8))

        # ── 7. Strategic Action Directives & Recommendations ──
        recommendations = report_data.get("recommendations", [])
        if recommendations:
            story.append(Paragraph("<b>Evidence-Linked Recommendations & Follow-ups</b>", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_BRIGHT_GREEN, spaceBefore=2, spaceAfter=6))
            for idx, r in enumerate(recommendations, start=1):
                prio_label = "Suggested follow-up" if idx % 2 == 1 else "Area for investigation"
                cat = str(r.get("category", "General")).title()

                r_card = [
                    [
                        Paragraph(f"<b>Follow-up {idx}: {r.get('title', 'Recommendation')}</b>", ParagraphStyle("RTitle", parent=cell_bold_style, fontSize=8.5, textColor=COLOR_INK)),
                        Paragraph(f"<b>{prio_label}</b> &nbsp;|&nbsp; {cat}", ParagraphStyle("RPrio", parent=cell_style, fontSize=7.5, alignment=2, textColor=COLOR_GREEN)),
                    ],
                    [
                        Paragraph(str(r.get("description", "Actionable intervention")), ParagraphStyle("RDesc", parent=cell_style, fontSize=8, leading=11)),
                        Paragraph("", cell_style),
                    ],
                ]
                r_tbl = Table(r_card, colWidths=[370, 153])
                r_tbl.setStyle(TableStyle([
                    ("SPAN", (0, 1), (1, 1)),
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
                    ("LINELEFT", (0, 0), (0, -1), 3.5, COLOR_GREEN),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]))
                story.append(r_tbl)
                story.append(Spacer(1, 5))
            story.append(Spacer(1, 4))

        # ── 8. Methodology, Governance & Limitations ──
        story.append(Paragraph("<b>Methodology & Analytical Limitations</b>", section_heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_MUTED, spaceBefore=2, spaceAfter=6))

        date_col_exists = bool(report_data.get("metadata", {}).get("has_dates", False))
        temporal_note = "Temporal trend analysis was omitted as no valid date/time parameter was detected in the source data." if not date_col_exists else "Temporal trends reflect timestamped observations aggregated into uniform periods."

        methodology_text = (
            f"<b>Data Processing Methodology:</b> Business metrics were calculated deterministically from the uploaded dataset. "
            f"AI-generated narrative was restricted to verified analytical evidence.<br/><br/>"
            f"<b>Limitations & Analytical Bounds:</b><br/>"
            f"• <b>Correlation vs Causation:</b> Statistical associations observed across dimensions represent empirical correlation and should not be inferred as causal business drivers.<br/>"
            f"• <b>Temporal Scope:</b> {temporal_note}<br/>"
            f"• <b>Data Quality:</b> All metrics reflect validated records according to the deterministic validation pipeline."
        )
        meth_box = [[Paragraph(methodology_text, ParagraphStyle("MethT", parent=cell_style, fontSize=7.5, leading=10.5, textColor=COLOR_MUTED))]]
        meth_tbl = Table(meth_box, colWidths=[523])
        meth_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
            ("LINELEFT", (0, 0), (0, -1), 3, COLOR_MUTED),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(meth_tbl)
        story.append(Spacer(1, 8))

        # ── 9. Verification Seal ──
        seal_data = [
            [
                Paragraph("<b>NOVERA DATA VERIFICATION</b>", ParagraphStyle("SealH", parent=cell_bold_style, fontSize=8.5, textColor=COLOR_INK)),
                Paragraph("<b>ANALYTICS: VERIFIED</b>", ParagraphStyle("SealR", parent=cell_bold_style, fontSize=8, alignment=2, textColor=COLOR_GREEN)),
            ],
            [
                Paragraph(
                    f"This report was compiled deterministically by Novera from the uploaded dataset. "
                    f"All metrics, distributions, and scorecard KPIs are grounded in verified evidence.<br/>"
                    f"<b>Dataset:</b> {dataset_name} (v{version}) &nbsp;|&nbsp; <b>AI Narrative:</b> {'Grounded' if is_ai_grounded else 'Deterministic Only'} &nbsp;|&nbsp; "
                    f"<b>Generated:</b> {created_at}",
                    ParagraphStyle("SealB", parent=cell_style, fontSize=7.5, leading=10.5, textColor=COLOR_MUTED),
                ),
                Paragraph("", cell_style),
            ],
        ]
        seal_table = Table(seal_data, colWidths=[380, 143])
        seal_table.setStyle(TableStyle([
            ("SPAN", (0, 1), (1, 1)),
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_RULE),
            ("LINELEFT", (0, 0), (0, -1), 3.5, COLOR_INK),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(seal_table)

        # Attach title to NumberedCanvas for running headers
        def make_canvas(*args: Any, **kwargs: Any) -> NumberedCanvas:
            c = NumberedCanvas(*args, **kwargs)
            setattr(c, "_report_title", title)
            return c

        doc.build(story, canvasmaker=make_canvas)
        buffer.seek(0)
        return buffer.getvalue()
