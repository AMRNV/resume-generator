"""
career_data.py — backward compatibility shim
Edit config.json instead.
"""
import json, os
_cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")))
CONTACT    = _cfg["contact"]
EXPERIENCE = _cfg["experience"]
EDUCATION  = _cfg["education"]
PROJECTS   = _cfg["projects"]
DEFAULT_JOB_TITLE      = _cfg["defaults"]["job_title"]
DEFAULT_HEADLINE       = _cfg["defaults"]["headline"]
DEFAULT_SUMMARY        = _cfg["defaults"]["summary"]
DEFAULT_CATEGORY_ORDER = _cfg["defaults"]["category_order"]
