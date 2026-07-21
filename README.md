# Resume Generator

A standalone Python app for generating tailored PDF resumes. Drop in your profile once, then generate job-specific resumes in seconds — with automatic skill matching from the job posting.

## Requirements

- Python 3.8+
- `reportlab` — the only third-party dependency

```bash
pip install reportlab
```

## Quick Start

```bash
python resume_app.py
```

## Adding a Profile

1. Create a folder under `profiles/` named after the person:
   ```
   profiles/
   └── Jane Smith/
       ├── config.json
       ├── skills.csv
       └── outputs/       ← auto-created on first generate
   ```

2. Use the files below as templates.

### `config.json`

```json
{
  "contact": {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "555-000-1234",
    "linkedin": "linkedin.com/in/janesmith",
    "linkedin_url": "https://www.linkedin.com/in/janesmith/",
    "github": "github.com/janesmith",
    "github_url": "https://github.com/janesmith",
    "location": "City, Province"
  },
  "defaults": {
    "job_title": "Software Developer",
    "headline": "Full-stack developer | 5 years experience",
    "summary": "Your default summary paragraph here.",
    "functional_summary": "Optional alternate summary used by the functional-style resume; falls back to summary if omitted.",
    "category_order": ["Languages", "Web", "Databases", "DevOps & Cloud", "AI & ML", "Other"]
  },
  "history": [
    {
      "kind": "job",
      "employer": "Acme Corp",
      "note": null,
      "location": "Toronto, ON",
      "title": "Software Developer",
      "dates": "Jan 2020 - Present",
      "bullets": [
        "Built and maintained X, resulting in Y",
        "Led migration from A to B"
      ],
      "competencies": [
        {
          "category": "Enterprise Software Development",
          "bullets": [
            "Narrative-style accomplishment bullet used by the functional resume's Skills section."
          ]
        }
      ]
    },
    {
      "kind": "project",
      "name": "My Project",
      "url": "github.com/janesmith/myproject",
      "description": "One or two sentence description of the project and what it does.",
      "competencies": [
        {
          "category": "AI & Emerging Technology Solutions",
          "bullets": [
            "Narrative-style accomplishment bullet sourced from a project instead of a job."
          ]
        }
      ]
    }
  ],
  "education": [
    {
      "program": "Computer Science",
      "school": "University of Example",
      "dates": "2016 - 2020",
      "note": "Focus: Algorithms, Distributed Systems"
    }
  ]
}
```

`history` holds both jobs and projects, distinguished by `"kind"` (`"job"` or `"project"`) — order in the list is the order they render in. `competencies` on a `history` entry is optional and only used by the functional-style resume (see below); it's ignored by the default chronological resume.

### `skills.csv`

```csv
skill,category,years_experience,professional_use
Python,Languages,5,Yes
JavaScript,Languages,4,Yes
SQL,Databases,5,Yes
Docker,DevOps & Cloud,2,No
```

**Columns:**
- `skill` — display name
- `category` — must match a category in `defaults.category_order` to appear in the default view
- `years_experience` — integer; used for sorting and skill-match scoring
- `professional_use` — `Yes` or `No`; only `Yes` skills appear in the default resume

## How It Works

**Default resume** (no job description): shows all `professional_use=Yes` skills grouped by category, sorted by years of experience descending.

**Matched resume** (job description pasted in): scores every skill against the posting text and picks the top 18. Whole-word matches score highest; professional use and years of experience break ties.

## Functional-Style Resume

Click **Generate Functional Resume** in the app for an alternate layout: a colored header banner (name/location/phone/email only — no headline or links), a **CORE SKILLS & COMPETENCIES** section grouped into narrative bullets by theme, and a bullet-less **PROFESSIONAL EXPERIENCE** list (title/employer/location/dates only).

The Skills section is assembled automatically — no separate list to maintain. It pulls the optional `competencies` entries off every entry in `history`, groups their bullets by category (in first-seen order), and tags each bullet with the job or project it came from, e.g. `(Job: Software Developer — Acme Corp)` or `(Project: My Project)`. Entries without a `competencies` field are simply skipped.

This is produced by `generate_resume_functional.py`, a separate engine from `generate_resume.py` — use `build_resume_functional(job_config, config_path)` if calling it directly.

## File Structure

```
resume_app.py                 — GUI app (run this)
generate_resume.py            — chronological PDF engine (used by the app and importable)
generate_resume_functional.py — functional/competency-style PDF engine
generate_cover_letter.py
profiles/
└── <Name>/
    ├── config.json    — contact info, defaults, history (jobs + projects), education
    ├── skills.csv     — skill inventory
    └── outputs/       — generated PDFs land here
```

## Editing a Profile in the App

Click **Edit Profile** in the main window to open the profile editor. It has a tab per section — **Contact & Defaults**, **Skills**, **Experience & Projects**, **Education** — each with Add/Edit/Delete controls instead of raw JSON. Entries in **Experience & Projects** are added via separate "Add Job" / "Add Project" buttons and rendered in whatever order they're listed in. Bullets are entered one per line; competencies (used only by the functional-style resume) use a light `### Category` / `- bullet` format. Everything saves back to the profile files on "Save All & Close".
