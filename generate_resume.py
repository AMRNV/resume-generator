"""
generate_resume.py  —  generic PDF resume engine
=================================================
To add a new person: create profiles/<Name>/config.json and profiles/<Name>/skills.csv

build_resume(job_config, config_path, skills_path) -> str (path to generated PDF)

job_config keys:
    job_title (str, optional)           defaults to config defaults.job_title
    headline (str, optional)            defaults to config defaults.headline
    summary (str, optional)             defaults to config defaults.summary
    job_description (str, optional)     raw posting text -- auto-ranks skills from skills.csv
    skills_order (list[str], optional)  explicit skill list, overrides auto-selection
    experience_bullets (dict, optional) {employer: [bullet, ...]} overrides for that employer
    output_dir (str, optional)          defaults to profiles/<Name>/outputs/
"""

import os
import csv
import re
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

from config_loader import _load_config

_DIR = os.path.dirname(os.path.abspath(__file__))
_PROFILES_DIR = os.path.join(_DIR, "profiles")


def list_profiles():
    """Return list of profile names (subdirectory names under profiles/)."""
    if not os.path.isdir(_PROFILES_DIR):
        return []
    return sorted(
        d for d in os.listdir(_PROFILES_DIR)
        if os.path.isdir(os.path.join(_PROFILES_DIR, d))
        and os.path.isfile(os.path.join(_PROFILES_DIR, d, "config.json"))
    )


def profile_paths(name):
    """Return (config_path, skills_path, output_dir) for a profile name."""
    folder = os.path.join(_PROFILES_DIR, name)
    return (
        os.path.join(folder, "config.json"),
        os.path.join(folder, "skills.csv"),
        os.path.join(folder, "outputs"),
    )


def _load_skills_csv(skills_path):
    with open(skills_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _default_skills(skills_path, category_order):
    rows = _load_skills_csv(skills_path)
    grouped = defaultdict(list)
    for row in rows:
        if row["professional_use"].strip().lower() == "yes":
            grouped[row["category"]].append(row)
    for cat in grouped:
        grouped[cat].sort(key=lambda r: int(r["years_experience"]), reverse=True)
    return {cat: [r["skill"] for r in grouped[cat]] for cat in category_order if cat in grouped}


def _matched_skills(skills_path, job_description, top_n=18):
    rows = _load_skills_csv(skills_path)
    jd_lower = job_description.lower()
    jd_tokens = set(re.findall(r"[a-z0-9#+.]+", jd_lower))
    scored = []
    for row in rows:
        skill = row["skill"]
        skill_lower = skill.lower()
        score = 0.0
        pattern = r"(?<![a-z0-9])" + re.escape(skill_lower) + r"(?![a-z0-9])"
        if re.search(pattern, jd_lower):
            score += 3
        skill_tokens = set(re.findall(r"[a-z0-9#+.]+", skill_lower))
        score += len(skill_tokens & jd_tokens)
        if row["professional_use"].strip().lower() == "yes":
            score += 2
        score += 0.1 * int(row["years_experience"])
        scored.append((score, skill))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_n]]


ACCENT   = colors.HexColor("#1a3c5e")
DARKGRAY = colors.HexColor("#333333")
MIDGRAY  = colors.HexColor("#555555")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "Name": ParagraphStyle("Name", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=20, textColor=ACCENT, spaceAfter=2, leading=24),
        "Headline": ParagraphStyle("Headline", parent=ss["Normal"], fontName="Helvetica-Oblique",
            fontSize=10.5, textColor=MIDGRAY, spaceAfter=6, leading=13),
        "Contact": ParagraphStyle("Contact", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, spaceAfter=10, leading=12),
        "SectionHeader": ParagraphStyle("SectionHeader", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=11, textColor=ACCENT, spaceBefore=7, spaceAfter=3, leading=13),
        "Summary": ParagraphStyle("Summary", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9.3, textColor=DARKGRAY, spaceAfter=2, leading=12.5, alignment=TA_LEFT),
        "JobTitle": ParagraphStyle("JobTitle", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=9.7, textColor=colors.black, spaceAfter=0, leading=12),
        "JobMeta": ParagraphStyle("JobMeta", parent=ss["Normal"], fontName="Helvetica-Oblique",
            fontSize=8.6, textColor=MIDGRAY, spaceAfter=2, leading=10.5),
        "Bullet": ParagraphStyle("Bullet", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, leading=11.8, leftIndent=12, spaceAfter=1.5, bulletIndent=0),
        "SkillLine": ParagraphStyle("SkillLine", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, leading=12, spaceAfter=1.5),
        "ProjName": ParagraphStyle("ProjName", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=9.3, textColor=colors.black, spaceAfter=0, leading=11.5),
        "ProjDesc": ParagraphStyle("ProjDesc", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, leading=11.8, spaceAfter=3),
        "EduLine": ParagraphStyle("EduLine", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=DARKGRAY, leading=11.8, spaceAfter=3),
    }


def _rule():
    return HRFlowable(width="100%", thickness=0.75, color=ACCENT, spaceBefore=1, spaceAfter=6)


def build_resume(job_config, config_path, skills_path):
    cfg      = _load_config(config_path)
    contact  = cfg["contact"]
    defaults = cfg["defaults"]
    default_output = os.path.join(os.path.dirname(config_path), "outputs")

    job_title     = job_config.get("job_title", defaults["job_title"])
    headline      = job_config.get("headline",  defaults["headline"])
    summary       = job_config.get("summary",   defaults["summary"])
    skills_order          = job_config.get("skills_order")
    job_desc              = job_config.get("job_description")
    exp_overrides         = job_config.get("experience_bullets", {})
    include_hidden        = job_config.get("include_hidden_projects", False)
    output_dir            = job_config.get("output_dir", default_output)

    os.makedirs(output_dir, exist_ok=True)
    name = contact.get("name", "Resume").replace(" ", "_")
    filepath = os.path.join(output_dir, "{}_resume.pdf".format(name))

    styles = _styles()
    doc = SimpleDocTemplate(filepath, pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.4*inch,  bottomMargin=0.4*inch,
        title="{} - {} Resume".format(contact.get("name",""), job_title) if "job_title" in job_config else "{} Resume".format(contact.get("name","")))

    story = []

    # Header
    story.append(Paragraph(contact["name"], styles["Name"]))
    story.append(Paragraph(headline, styles["Headline"]))
    contact_parts = [contact[k] for k in ("email","phone","linkedin","github","location") if contact.get(k)]
    story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_parts), styles["Contact"]))
    story.append(_rule())

    # Summary
    story.append(Paragraph("SUMMARY", styles["SectionHeader"]))
    story.append(Paragraph(summary, styles["Summary"]))

    # Skills
    story.append(Paragraph("SKILLS", styles["SectionHeader"]))
    if skills_order:
        story.append(Paragraph(", ".join(skills_order), styles["SkillLine"]))
    elif job_desc:
        story.append(Paragraph(", ".join(_matched_skills(skills_path, job_desc)), styles["SkillLine"]))
    else:
        for cat, items in _default_skills(skills_path, defaults["category_order"]).items():
            story.append(Paragraph("<b>{}:</b> {}".format(cat, ", ".join(items)), styles["SkillLine"]))

    jobs     = [h for h in cfg.get("history", []) if h.get("kind") == "job"]
    projects = [h for h in cfg.get("history", []) if h.get("kind") == "project"
                and (not h.get("hidden") or include_hidden)]

    # Experience
    story.append(Paragraph("EXPERIENCE", styles["SectionHeader"]))
    for job in jobs:
        header_row = Table(
            [[Paragraph("{} — {}".format(job["title"], job["employer"]), styles["JobTitle"]),
              Paragraph(job["dates"], styles["JobTitle"])]],
            colWidths=[4.6*inch, 2.1*inch])
        header_row.setStyle(TableStyle([
            ("ALIGN",        (1,0),(1,0),"RIGHT"),
            ("VALIGN",       (0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",  (0,0),(-1,-1),0),
            ("RIGHTPADDING", (0,0),(-1,-1),0),
            ("TOPPADDING",   (0,0),(-1,-1),0),
            ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ]))
        story.append(header_row)
        meta_bits = [job["location"]]
        if job.get("note"):
            meta_bits.append(job["note"])
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(meta_bits), styles["JobMeta"]))
        for b in exp_overrides.get(job["employer"], job["bullets"]):
            story.append(Paragraph("&bull; {}".format(b), styles["Bullet"]))
        story.append(Spacer(1, 4))

    # Projects
    if projects:
        story.append(Paragraph("PROJECTS", styles["SectionHeader"]))
        for p in projects:
            story.append(Paragraph('{} <font color="#555555">({})</font>'.format(p["name"], p["url"]), styles["ProjName"]))
            story.append(Paragraph(p["description"], styles["ProjDesc"]))

    # Education
    story.append(Paragraph("EDUCATION", styles["SectionHeader"]))
    for e in cfg["education"]:
        story.append(Paragraph("<b>{}</b> — {} &nbsp;({})<br/>{}".format(
            e["program"], e["school"], e["dates"], e["note"]), styles["EduLine"]))

    doc.build(story)
    return filepath
