# -*- coding: utf-8 -*-

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
import pandas as pd
import io


def generate_pdf(data_df, incidents_df):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("AREE Risk Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Service Risk Overview", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    table_data = [list(data_df.columns)] + data_df.values.tolist()

    table = Table(table_data)

    table.setStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
    ])

    elements.append(table)

    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Recent Incidents", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    incident_data = [list(incidents_df.columns)] + incidents_df.values.tolist()

    incident_table = Table(incident_data)

    incident_table.setStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
    ])

    elements.append(incident_table)

    doc.build(elements)

    buffer.seek(0)

    return buffer