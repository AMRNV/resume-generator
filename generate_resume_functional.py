"""
generate_resume_functional.py  —  functional/competency-style PDF resume engine
================================================================================
Companion to generate_resume.py. Produces a "functional" resume layout instead
of the chronological one: a colored header banner (name/location/phone/email
only — no headline or links), a CORE SKILLS & COMPETENCIES section grouped
into narrative bullets by theme, a bullet-less PROFESSIONAL EXPERIENCE list
(title/employer/location/dates only), plus TECHNICAL PROJECTS and EDUCATION
AND CERTIFICATIONS sections.

Uses the same profiles/<Name>/config.json as generate_resume.py, where
history[] holds both jobs and projects tagged by "kind", plus:

    history[].competencies (list, optional)     per-job/per-project competency bullets
        shaped as [{"category": str, "bullets": [str, ...]}, ...]
    defaults.functional_summary (str, optional) falls back to defaults.summary

The CORE SKILLS & COMPETENCIES section is assembled automatically by pulling
the "competencies" entries off every entry in history, grouping their bullets
by category (in first-seen order), and tagging each bullet with the job/project
it came from.

build_resume_functional(job_config, config_path) -> str (path to generated PDF)
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from config_loader import _load_config

ACCENT   = colors.HexColor("#153d63")
DARKGRAY = colors.HexColor("#333333")
MIDGRAY  = colors.HexColor("#555555")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "Name": ParagraphStyle("Name", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=20, textColor=colors.white, alignment=TA_CENTER, spaceAfter=2, leading=24),
        "HeaderContact": ParagraphStyle("HeaderContact", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=colors.white, alignment=TA_CENTER, leading=13),
        "SectionHeader": ParagraphStyle("SectionHeader", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=11, textColor=ACCENT, spaceBefore=10, spaceAfter=4, leading=13),
        "Summary": ParagraphStyle("Summary", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9.3, textColor=DARKGRAY, leading=12.5, alignment=TA_LEFT, spaceAfter=2),
        "CompCategory": ParagraphStyle("CompCategory", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=9.5, textColor=colors.black, spaceBefore=5, spaceAfter=1, leading=12),
        "Bullet": ParagraphStyle("Bullet", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, leading=11.8, leftIndent=12, spaceAfter=1.5),
        "JobTitle": ParagraphStyle("JobTitle", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=9.7, textColor=colors.black, spaceAfter=0, leading=12),
        "JobMeta": ParagraphStyle("JobMeta", parent=ss["Normal"], fontName="Helvetica-Oblique",
            fontSize=8.6, textColor=MIDGRAY, spaceAfter=5, leading=10.5),
        "ProjName": ParagraphStyle("ProjName", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=9.3, textColor=colors.black, spaceAfter=0, leading=11.5),
        "ProjDesc": ParagraphStyle("ProjDesc", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, leading=11.8, spaceAfter=3),
        "EduLine": ParagraphStyle("EduLine", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, leading=11.8, spaceAfter=3),
    }


def _aggregate_competencies(cfg, include_hidden=False):
    """Pull competencies off every entry in history, grouped by category
    (first-seen order), each bullet tagged with its source."""
    order = []
    grouped = {}

    def add_source(kind, label, comp_groups):
        for group in comp_groups or []:
            cat = group["category"]
            if cat not in grouped:
                grouped[cat] = []
                order.append(cat)
            for bullet in group.get("bullets", []):
                grouped[cat].append(bullet)

    for h in cfg.get("history", []):
        if h.get("kind") == "job":
            add_source("Job", "{} — {}".format(h["title"], h["employer"]), h.get("competencies"))
        elif h.get("kind") == "project" and (not h.get("hidden") or include_hidden):
            add_source("Project", h["name"], h.get("competencies"))

    return [{"category": cat, "items": grouped[cat]} for cat in order]


def build_resume_functional(job_config, config_path):
    cfg      = _load_config(config_path)
    contact  = cfg["contact"]
    defaults = cfg["defaults"]
    default_output = os.path.join(os.path.dirname(config_path), "outputs")

    job_title      = job_config.get("job_title", defaults["job_title"])
    summary        = job_config.get("summary", defaults.get("functional_summary", defaults["summary"]))
    include_hidden = job_config.get("include_hidden_projects", False)
    competencies   = job_config.get("competencies") or _aggregate_competencies(cfg, include_hidden)
    output_dir     = job_config.get("output_dir", default_output)

    os.makedirs(output_dir, exist_ok=True)
    name = contact.get("name", "Resume").replace(" ", "_")
    if "job_title" in job_config:
        filepath = os.path.join(output_dir, "{}_{}_functional_resume.pdf".format(name, job_title.replace(" ", "_")))
    else:
        filepath = os.path.join(output_dir, "{}_functional_resume.pdf".format(name))

    styles = _styles()
    doc = SimpleDocTemplate(filepath, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.4*inch,  bottomMargin=0.4*inch,
        title="{} - {} Resume".format(contact.get("name",""), job_title))

    story = []

    # Header banner — name/location/phone/email only (no headline, no links)
    contact_line = " &nbsp;|&nbsp; ".join(
        c for c in (contact.get("location"), contact.get("phone"), contact.get("email")) if c)
    header_cell = [
        Paragraph(contact.get("name",""), styles["Name"]),
        Paragraph(contact_line, styles["HeaderContact"]),
    ]
    header_table = Table([[header_cell]], colWidths=[7.3*inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), ACCENT),
        ("TOPPADDING",   (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("ALIGN",        (0,0),(-1,-1), "CENTER"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Summary
    story.append(Paragraph("SUMMARY OF QUALIFICATIONS", styles["SectionHeader"]))
    story.append(Paragraph(summary, styles["Summary"]))

    # Core Skills & Competencies
    story.append(Paragraph("CORE SKILLS &amp; COMPETENCIES", styles["SectionHeader"]))
    for group in competencies:
        story.append(Paragraph(group["category"], styles["CompCategory"]))
        for item in group.get("items", group.get("bullets", [])):
            story.append(Paragraph("&bull; {}".format(item), styles["Bullet"]))

    jobs     = [h for h in cfg.get("history", []) if h.get("kind") == "job"]
    projects = [h for h in cfg.get("history", []) if h.get("kind") == "project"
                and (not h.get("hidden") or include_hidden)]

    # Professional Experience — headers only, no accomplishment bullets
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["SectionHeader"]))
    for job in jobs:
        header_row = Table(
            [[Paragraph("{} — {}".format(job["title"], job["employer"]), styles["JobTitle"]),
              Paragraph(job["dates"], styles["JobTitle"])]],
            colWidths=[4.6*inch, 2.7*inch])
        header_row.setStyle(TableStyle([
            ("ALIGN",        (1,0),(1,0),"RIGHT"),
            ("VALIGN",       (0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",  (0,0),(-1,-1),0),
            ("RIGHTPADDING", (0,0),(-1,-1),0),
            ("TOPPADDING",   (0,0),(-1,-1),0),
            ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ]))
        story.append(header_row)
        story.append(Paragraph(job["location"], styles["JobMeta"]))

    # Technical Projects
    if projects:
        story.append(Paragraph("TECHNICAL PROJECTS", styles["SectionHeader"]))
        for p in projects:
            story.append(Paragraph('{} <font color="#555555">({})</font>'.format(p["name"], p["url"]), styles["ProjName"]))
            story.append(Paragraph(p["description"], styles["ProjDesc"]))

    # Education and Certifications
    story.append(Paragraph("EDUCATION AND CERTIFICATIONS", styles["SectionHeader"]))
    for e in cfg["education"]:
        story.append(Paragraph("<b>{}</b> — {} &nbsp;({})".format(
            e["program"], e["school"], e["dates"]), styles["EduLine"]))

    doc.build(story)
    return filepath
