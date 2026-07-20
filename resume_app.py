"""
resume_app.py  —  multi-profile resume generator GUI
=====================================================
Run with: python resume_app.py
To add a person: create profiles/<Name>/ with config.json and skills.csv inside.
Requirements: Python 3 (tkinter included), reportlab  ->  pip install reportlab
"""

import os, sys, subprocess, json, csv
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_resume import (
    build_resume, list_profiles, profile_paths,
    _default_skills, _matched_skills, _load_config,
)

_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Edit Profile window
# ---------------------------------------------------------------------------

class EditProfileWindow(tk.Toplevel):
    def __init__(self, parent, profile_name, on_save=None):
        super().__init__(parent)
        self.title("Edit Profile — {}".format(profile_name))
        self.resizable(True, True)
        self.configure(padx=12, pady=12)
        self.profile_name = profile_name
        self.on_save = on_save
        config_path, skills_path, _ = profile_paths(profile_name)
        self.config_path = config_path
        self.skills_path = skills_path
        self.cfg = _load_config(config_path)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self._build_contact_tab(nb)
        self._build_skills_tab(nb)
        self._build_advanced_tab(nb)

        tk.Button(self, text="Save All & Close", font=("Helvetica", 10, "bold"),
                  bg="#1a3c5e", fg="white", padx=12, pady=5,
                  command=self._save_all).pack(pady=(10, 0))

    # ---- Contact & Defaults tab ----

    def _build_contact_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Contact & Defaults")
        frame.configure(padding=12)

        def row(parent, label, row_i, default="", height=1):
            tk.Label(parent, text=label, anchor="w", font=("Helvetica", 9, "bold")).grid(
                row=row_i*2, column=0, sticky="w", pady=(6,1))
            if height == 1:
                w = tk.Entry(parent, width=60)
                w.insert(0, default)
            else:
                w = tk.Text(parent, height=height, width=60, wrap="word")
                w.insert("1.0", default)
            w.grid(row=row_i*2+1, column=0, sticky="ew")
            return w

        c = self.cfg["contact"]
        d = self.cfg["defaults"]

        tk.Label(frame, text="CONTACT", font=("Helvetica", 10, "bold", "underline")).grid(
            row=0, column=0, sticky="w", pady=(0, 4))

        self.f_name     = row(frame, "Name",     1, c.get("name",""))
        self.f_email    = row(frame, "Email",    2, c.get("email",""))
        self.f_phone    = row(frame, "Phone",    3, c.get("phone",""))
        self.f_linkedin = row(frame, "LinkedIn (display)", 4, c.get("linkedin",""))
        self.f_lin_url  = row(frame, "LinkedIn URL",       5, c.get("linkedin_url",""))
        self.f_github   = row(frame, "GitHub (display)",   6, c.get("github",""))
        self.f_git_url  = row(frame, "GitHub URL",         7, c.get("github_url",""))
        self.f_location = row(frame, "Location", 8, c.get("location",""))

        tk.Label(frame, text="DEFAULTS", font=("Helvetica", 10, "bold", "underline")).grid(
            row=18, column=0, sticky="w", pady=(14, 4))

        self.f_job_title = row(frame, "Default Job Title", 10, d.get("job_title",""))
        self.f_headline  = row(frame, "Default Headline",  11, d.get("headline",""))
        self.f_summary   = row(frame, "Default Summary",   12, d.get("summary",""), height=4)
        self.f_cat_order = row(frame, "Category Order (comma-separated)", 13,
                               ", ".join(d.get("category_order",[])))
        frame.columnconfigure(0, weight=1)

    def _contact_defaults_data(self):
        def entry_val(w):
            return w.get() if isinstance(w, tk.Entry) else w.get("1.0","end").strip()
        cat_raw = entry_val(self.f_cat_order)
        cat_list = [c.strip() for c in cat_raw.split(",") if c.strip()]
        contact = {
            "name":         entry_val(self.f_name),
            "email":        entry_val(self.f_email),
            "phone":        entry_val(self.f_phone),
            "linkedin":     entry_val(self.f_linkedin),
            "linkedin_url": entry_val(self.f_lin_url),
            "github":       entry_val(self.f_github),
            "github_url":   entry_val(self.f_git_url),
            "location":     entry_val(self.f_location),
        }
        defaults = {
            "job_title":      entry_val(self.f_job_title),
            "headline":       entry_val(self.f_headline),
            "summary":        entry_val(self.f_summary),
            "category_order": cat_list,
        }
        return contact, defaults

    # ---- Skills tab ----

    def _build_skills_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Skills")
        frame.configure(padding=12)

        cols = ("skill", "category", "years_experience", "professional_use")
        self.skills_tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        for col in cols:
            self.skills_tree.heading(col, text=col.replace("_"," ").title())
            self.skills_tree.column(col, width=140 if col=="skill" else 120, anchor="w")
        self.skills_tree.pack(fill="both", expand=True, side="top")
        self.skills_tree.bind("<Double-1>", self._edit_skill_row)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=(6,0))
        tk.Button(btn_frame, text="Add",    command=self._add_skill).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Edit",   command=self._edit_skill_row).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Delete", command=self._delete_skill).pack(side="left", padx=2)

        self._load_skills_tree()

    def _load_skills_tree(self):
        self.skills_tree.delete(*self.skills_tree.get_children())
        try:
            with open(self.skills_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.skills_tree.insert("", "end", values=(
                        row["skill"], row["category"],
                        row["years_experience"], row["professional_use"]))
        except FileNotFoundError:
            pass

    def _skill_dialog(self, title, defaults=("","","1","Yes")):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.configure(padx=12, pady=12)
        dlg.grab_set()
        labels = ["Skill", "Category", "Years Experience", "Professional Use (Yes/No)"]
        entries = []
        for i, (lbl, val) in enumerate(zip(labels, defaults)):
            tk.Label(dlg, text=lbl, anchor="w").grid(row=i*2, column=0, sticky="w", pady=(4,0))
            e = tk.Entry(dlg, width=40)
            e.insert(0, val)
            e.grid(row=i*2+1, column=0, sticky="ew")
            entries.append(e)
        result = []
        def ok():
            result.extend([e.get().strip() for e in entries])
            dlg.destroy()
        def cancel():
            dlg.destroy()
        bf = tk.Frame(dlg)
        bf.grid(row=9, column=0, pady=(10,0))
        tk.Button(bf, text="OK",     command=ok).pack(side="left", padx=4)
        tk.Button(bf, text="Cancel", command=cancel).pack(side="left", padx=4)
        dlg.columnconfigure(0, weight=1)
        self.wait_window(dlg)
        return result if len(result) == 4 else None

    def _add_skill(self):
        vals = self._skill_dialog("Add Skill")
        if vals:
            self.skills_tree.insert("", "end", values=vals)

    def _edit_skill_row(self, event=None):
        sel = self.skills_tree.selection()
        if not sel:
            return
        item = sel[0]
        current = self.skills_tree.item(item, "values")
        vals = self._skill_dialog("Edit Skill", defaults=current)
        if vals:
            self.skills_tree.item(item, values=vals)

    def _delete_skill(self):
        for item in self.skills_tree.selection():
            self.skills_tree.delete(item)

    def _skills_rows(self):
        rows = []
        for item in self.skills_tree.get_children():
            v = self.skills_tree.item(item, "values")
            rows.append({"skill": v[0], "category": v[1],
                         "years_experience": v[2], "professional_use": v[3]})
        return rows

    # ---- Advanced (JSON) tab ----

    def _build_advanced_tab(self, nb):
        frame = ttk.Frame(nb)
        nb.add(frame, text="Experience / Education / Projects")
        frame.configure(padding=12)
        tk.Label(frame, text="Edit experience, education, and projects as JSON.",
                 anchor="w").pack(anchor="w")
        self.json_editor = tk.Text(frame, width=80, height=30, wrap="none", font=("Courier", 9))
        self.json_editor.pack(fill="both", expand=True, pady=(6,0))
        sb = ttk.Scrollbar(frame, command=self.json_editor.yview)
        self.json_editor["yscrollcommand"] = sb.set
        data = {
            "experience": self.cfg.get("experience", []),
            "education":  self.cfg.get("education",  []),
            "projects":   self.cfg.get("projects",   []),
        }
        self.json_editor.insert("1.0", json.dumps(data, indent=2))

    def _advanced_data(self):
        raw = self.json_editor.get("1.0", "end").strip()
        return json.loads(raw)

    # ---- Save all ----

    def _save_all(self):
        try:
            contact, defaults = self._contact_defaults_data()
            adv = self._advanced_data()
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", "Invalid JSON in Experience/Education/Projects:\n{}".format(e), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        new_cfg = {
            "contact":    contact,
            "defaults":   defaults,
            "experience": adv["experience"],
            "education":  adv["education"],
            "projects":   adv.get("projects", []),
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(new_cfg, f, indent=2)

        rows = self._skills_rows()
        with open(self.skills_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["skill","category","years_experience","professional_use"])
            w.writeheader()
            w.writerows(rows)

        if self.on_save:
            self.on_save()
        self.destroy()


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

class ResumeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Resume Generator")
        self.resizable(True, True)
        self.configure(padx=16, pady=16)

        # --- Profile selector ---
        tk.Label(self, text="Profile", font=("Helvetica", 10, "bold"), anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0,2))
        profile_row = tk.Frame(self)
        profile_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0,12))
        self.profile_var = tk.StringVar()
        self.profile_menu = ttk.Combobox(profile_row, textvariable=self.profile_var,
                                          state="readonly", width=50)
        self.profile_menu.pack(side="left", fill="x", expand=True)
        self.profile_menu.bind("<<ComboboxSelected>>", self._on_profile_change)
        tk.Button(profile_row, text="Edit Profile",
                  command=self._open_edit).pack(side="left", padx=(8,0))

        # --- Job Title ---
        tk.Label(self, text="Job Title", font=("Helvetica", 10, "bold"), anchor="w").grid(
            row=2, column=0, sticky="w", pady=(0,2))
        self.job_title = tk.Entry(self, width=60)
        self.job_title.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0,10))

        # --- Headline ---
        tk.Label(self, text="Headline", font=("Helvetica", 10, "bold"), anchor="w").grid(
            row=4, column=0, sticky="w", pady=(0,2))
        self.headline = tk.Entry(self, width=60)
        self.headline.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0,10))

        # --- Summary ---
        tk.Label(self, text="Summary  (leave blank for default)", font=("Helvetica", 10, "bold"), anchor="w").grid(
            row=6, column=0, sticky="w", pady=(0,2))
        self.summary = tk.Text(self, height=4, width=60, wrap="word")
        self.summary.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0,10))

        # --- Job Description ---
        tk.Label(self, text="Job Description  (paste posting to auto-match skills; leave blank for defaults)",
                 font=("Helvetica", 10, "bold"), anchor="w").grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(0,2))
        self.job_desc = tk.Text(self, height=8, width=60, wrap="word")
        self.job_desc.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0,10))
        self.job_desc.bind("<KeyRelease>", self._update_preview)

        # --- Skills preview ---
        tk.Label(self, text="Skills Preview", font=("Helvetica", 10, "bold"), anchor="w").grid(
            row=10, column=0, sticky="w", pady=(0,2))
        self.preview_var = tk.StringVar()
        tk.Label(self, textvariable=self.preview_var, wraplength=550,
                 justify="left", fg="#555555", anchor="w").grid(
            row=11, column=0, columnspan=2, sticky="w", pady=(0,12))

        # --- Generate button ---
        self.gen_btn = tk.Button(self, text="Generate Resume", font=("Helvetica", 11, "bold"),
                                  bg="#1a3c5e", fg="white", padx=16, pady=6,
                                  command=self._generate)
        self.gen_btn.grid(row=12, column=0, columnspan=2, pady=(0,4))

        # --- Status ---
        self.status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.status_var, fg="#1a3c5e").grid(
            row=13, column=0, columnspan=2)

        self.columnconfigure(0, weight=1)
        self._refresh_profiles()

    def _refresh_profiles(self):
        current = self.profile_var.get()
        profiles = list_profiles()
        self.profile_menu["values"] = profiles
        if current in profiles:
            self.profile_var.set(current)
        elif profiles:
            self.profile_menu.current(0)
            self._load_profile(profiles[0])
        else:
            self.status_var.set("No profiles found. Add a folder under profiles/.")

    def _on_profile_change(self, event=None):
        self._load_profile(self.profile_var.get())

    def _load_profile(self, name):
        config_path, _, _ = profile_paths(name)
        try:
            cfg = _load_config(config_path)
            d = cfg["defaults"]
            self.job_title.delete(0, "end")
            self.job_title.insert(0, d["job_title"])
            self.headline.delete(0, "end")
            self.headline.insert(0, d["headline"])
            self.summary.delete("1.0", "end")
            self.job_desc.delete("1.0", "end")
            self._update_preview()
            self.status_var.set("")
        except Exception as e:
            self.status_var.set("Error loading profile: {}".format(e))

    def _open_edit(self):
        name = self.profile_var.get()
        if not name:
            messagebox.showwarning("No Profile", "Please select a profile first.")
            return
        EditProfileWindow(self, name, on_save=lambda: self._load_profile(name))

    def _update_preview(self, event=None):
        name = self.profile_var.get()
        if not name:
            return
        config_path, skills_path, _ = profile_paths(name)
        try:
            cfg = _load_config(config_path)
            jd = self.job_desc.get("1.0", "end").strip()
            if jd:
                text = "Matched: " + ", ".join(_matched_skills(skills_path, jd))
            else:
                grouped = _default_skills(skills_path, cfg["defaults"]["category_order"])
                text = " | ".join("{}: {}".format(c, ", ".join(i)) for c, i in grouped.items())
            self.preview_var.set(text)
        except Exception:
            self.preview_var.set("")

    def _generate(self):
        name = self.profile_var.get()
        if not name:
            messagebox.showwarning("No Profile", "Please select a profile first.")
            return
        config_path, skills_path, default_output = profile_paths(name)
        cfg = _load_config(config_path)
        d = cfg["defaults"]

        job_config = {
            "job_title":  self.job_title.get().strip() or d["job_title"],
            "headline":   self.headline.get().strip()  or d["headline"],
            "output_dir": default_output,
        }
        summary_text = self.summary.get("1.0", "end").strip()
        jd = self.job_desc.get("1.0", "end").strip()
        if summary_text:
            job_config["summary"] = summary_text
        if jd:
            job_config["job_description"] = jd

        self.gen_btn.config(state="disabled")
        self.status_var.set("Generating...")
        self.update()
        try:
            path = build_resume(job_config, config_path, skills_path)
            self.status_var.set("Saved: {}".format(os.path.basename(path)))
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("")
        finally:
            self.gen_btn.config(state="normal")


if __name__ == "__main__":
    app = ResumeApp()
    app.mainloop()
