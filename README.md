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
    "category_order": ["Languages", "Web", "Databases", "DevOps & Cloud", "AI & ML", "Other"]
  },
  "experience": [
    {
      "employer": "Acme Corp",
      "note": null,
      "location": "Toronto, ON",
      "title": "Software Developer",
      "dates": "Jan 2020 - Present",
      "bullets": [
        "Built and maintained X, resulting in Y",
        "Led migration from A to B"
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
  ],
  "projects": [
    {
      "name": "My Project",
      "url": "github.com/janesmith/myproject",
      "description": "One or two sentence description of the project and what it does."
    }
  ]
}
```

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

## File Structure

```
resume_app.py          — GUI app (run this)
generate_resume.py     — PDF engine (used by the app and importable)
generate_cover_letter.py
career_data.py         — backward-compat shim (legacy)
profiles/
└── <Name>/
    ├── config.json    — contact info, defaults, experience, education, projects
    ├── skills.csv     — skill inventory
    └── outputs/       — generated PDFs land here
```

## Editing a Profile in the App

Click **Edit Profile** in the main window to open the profile editor. Changes to contact info, defaults, and skills save back to the profile files immediately on "Save All & Close".

For experience, education, and projects, use the **Experience / Education / Projects** tab — it exposes the raw JSON for those sections.
