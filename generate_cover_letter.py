"""
generate_cover_letter.py

build_cover_letter(job_config, config_path) -> str (path to generated PDF)

job_config keys:
    job_title (str, required)
    company (str, required)
    recipient_name (str, optional)   defaults to "Hiring Team"
    date (str, optional)             defaults to today, e.g. "July 20, 2026"
    paragraphs (list[str], required) body paragraphs in order
    closing (str, optional)          defaults to "Sincerely,"
    output_dir (str, optional)       defaults to profiles/<Name>/outputs/
"""

import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from generate_resume import _load_config

ACCENT   = colors.HexColor("#1a3c5e")
DARKGRAY = colors.HexColor("#333333")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "Name": ParagraphStyle(
            "Name", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=16, textColor=ACCENT, spaceAfter=2, leading=19,
        ),
        "Contact": ParagraphStyle(
            "Contact", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=colors.HexColor("#555555"), spaceAfter=14, leading=12,
        ),
        "DateLine": ParagraphStyle(
            "DateLine", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=DARKGRAY, spaceAfter=12,
        ),
        "Recipient": ParagraphStyle(
            "Recipient", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=DARKGRAY, spaceAfter=14, leading=13,
        ),
        "Body": ParagraphStyle(
            "Body", parent=ss["Normal"], fontName="Helvetica",
            fontSize=10, textColor=DARKGRAY, leading=15, spaceAfter=10,
        ),
        "Closing": ParagraphStyle(
            "Closing", parent=ss["Normal"], fontName="Helvetica",
            fontSize=10, textColor=DARKGRAY, spaceBefore=8,
        ),
    }


def build_cover_letter(job_config, config_path):
    cfg     = _load_config(config_path)
    contact = cfg["contact"]
    default_output = os.path.join(os.path.dirname(config_path), "outputs")

    job_title      = job_config["job_title"]
    company        = job_config["company"]
    recipient_name = job_config.get("recipient_name", "Hiring Team")
    paragraphs     = job_config["paragraphs"]
    closing        = job_config.get("closing", "Sincerely,")
    output_dir     = job_config.get("output_dir", default_output)

    today = datetime.date.today()
    date_str = job_config.get("date") or "{} {}, {}".format(
        today.strftime("%B"), today.day, today.year)

    os.makedirs(output_dir, exist_ok=True)
    name     = contact.get("name", "Resume").replace(" ", "_")
    filename = "{}_{}_{}_cover_letter.pdf".format(name, job_title, company)
    filepath = os.path.join(output_dir, filename)

    styles = _styles()
    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        leftMargin=0.85*inch, rightMargin=0.85*inch,
        topMargin=0.75*inch,  bottomMargin=0.75*inch,
        title="{} - {} Cover Letter".format(contact.get("name",""), job_title),
    )

    story = []
    story.append(Paragraph(contact["name"], styles["Name"]))
    contact_parts = [contact[k] for k in ("email","phone","linkedin","github") if contact.get(k)]
    story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_parts), styles["Contact"]))

    story.append(Paragraph(date_str, styles["DateLine"]))
    story.append(Paragraph("{}<br/>{}".format(recipient_name, company), styles["Recipient"]))

    for para in paragraphs:
        story.append(Paragraph(para, styles["Body"]))

    story.append(Spacer(1, 8))
    story.append(Paragraph(closing, styles["Closing"]))
    story.append(Spacer(1, 24))
    story.append(Paragraph(contact["name"], styles["Closing"]))

    doc.build(story)
    return filepath
