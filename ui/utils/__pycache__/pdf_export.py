"""
AREE — PDF Report Exporter
Generates a downloadable PDF risk report from RE data and incident logs.
Place this file at: ui/utils/pdf_export.py
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch


def generate_pdf(data: dict, incidents: list) -> bytes:
    """
    Generate a PDF risk report.

    Args:
        data: dict of RE scores and metrics (e.g. from compute_re_from_real)
        incidents: list of incident log dicts

    Returns:
        PDF as bytes (ready for st.download_button)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Title ──────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=16,
    )

    story.append(Paragraph("AREE Risk Evolution Engine", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        subtitle_style,
    ))

    # ── Section header helper ───────────────────────────────────
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e40af"),
        spaceBefore=16,
        spaceAfter=6,
    )

    normal = styles["Normal"]

    # ── RE Metrics Summary ──────────────────────────────────────
    story.append(Paragraph("Risk Energy (RE) Metrics", section_style))

    if isinstance(data, dict) and data:
        metric_rows = [["Metric", "Value"]]
        for key, value in data.items():
            if isinstance(value, float):
                value = f"{value:.2f}"
            metric_rows.append([str(key), str(value)])

        metric_table = Table(metric_rows, colWidths=[3 * inch, 3.5 * inch])
        metric_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(metric_table)
    else:
        story.append(Paragraph("No RE metric data available.", normal))

    story.append(Spacer(1, 12))

    # ── Incident Log ───────────────────────────────────────────
    story.append(Paragraph("Incident Log", section_style))

    if incidents:
        # Determine columns from first incident
        if isinstance(incidents[0], dict):
            cols = list(incidents[0].keys())
            inc_rows = [cols]
            for inc in incidents:
                inc_rows.append([str(inc.get(c, "")) for c in cols])
        else:
            inc_rows = [["Incident"], [str(i) for i in incidents]]

        col_width = 6.5 * inch / max(len(inc_rows[0]), 1)
        inc_table = Table(inc_rows, colWidths=[col_width] * len(inc_rows[0]))
        inc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff1f2"), colors.white]),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("WORDWRAP", (0, 0), (-1, -1), True),
        ]))
        story.append(inc_table)
    else:
        story.append(Paragraph("No incidents recorded this session.", normal))

    # ── Footer ─────────────────────────────────────────────────
    story.append(Spacer(1, 24))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
    )
    story.append(Paragraph("AREE — Automated Risk & Remediation Engine | Confidential", footer_style))

    doc.build(story)
    return buffer.getvalue()