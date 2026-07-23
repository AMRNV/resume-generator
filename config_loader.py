"""
config_loader.py  —  shared profile config.json loader
========================================================
Used by generate_resume.py, generate_resume_functional.py, and resume_app.py
so there's a single place that knows how to read profiles/<Name>/config.json.
"""

import json


def _load_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)
