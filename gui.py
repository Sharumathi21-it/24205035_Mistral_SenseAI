import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from analyzer import ResumeAnalyzer
from extractor import ExtractionError
import report_generator as rg
from main import collect_resume_paths

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


class ResumeAnalyzerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Intelligent Resume Analyzer")
        self.geometry("880x560")
        self.configure(bg="#0f172a")
        self.jd_path = tk.StringVar()
        self.resumes_dir = tk.StringVar()
        self.results = []
        self.jd_meta = {}

        self._build_widgets()

    # ------------------------------------------------------------ UI --
    def _build_widgets(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        top = tk.Frame(self, bg="#0f172a", pady=10, padx=10)
        top.pack(fill="x")

        tk.Label(top, text="Job Description:", bg="#0f172a", fg="#e2e8f0").grid(row=0, column=0, sticky="w")
        tk.Entry(top, textvariable=self.jd_path, width=60).grid(row=0, column=1, padx=6)
        tk.Button(top, text="Browse", command=self._pick_jd).grid(row=0, column=2)

        tk.Label(top, text="Resumes Folder:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="w", pady=6)
        tk.Entry(top, textvariable=self.resumes_dir, width=60).grid(row=1, column=1, padx=6)
        tk.Button(top, text="Browse", command=self._pick_resumes).grid(row=1, column=2)

        btn_row = tk.Frame(self, bg="#0f172a")
        btn_row.pack(fill="x", padx=10)
        self.run_btn = tk.Button(btn_row, text="Run Analysis", bg="#38bdf8", fg="#04212f",
                                  font=("Segoe UI", 10, "bold"), command=self._run_analysis)
        self.run_btn.pack(side="left")
        tk.Button(btn_row, text="Export HTML Report", command=self._export_html).pack(side="left", padx=8)
        tk.Button(btn_row, text="Export JSON Report", command=self._export_json).pack(side="left")

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self, textvariable=self.status_var, bg="#0f172a", fg="#94a3b8").pack(anchor="w", padx=12, pady=(4, 0))

        columns = ("rank", "filename", "score", "skills", "experience", "education")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        headings = {
            "rank": "Rank", "filename": "Resume", "score": "Final Score %",
            "skills": "Skill Match %", "experience": "Experience %", "education": "Education %",
        }
        widths = {"rank": 50, "filename": 260, "score": 110, "skills": 110, "experience": 110, "education": 110}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._show_detail)

        self.detail_text = tk.Text(self, height=6, bg="#1e293b", fg="#e2e8f0", wrap="word")
        self.detail_text.pack(fill="x", padx=10, pady=(0, 10))

    # -------------------------------------------------------- actions --
    def _pick_jd(self):
        path = filedialog.askopenfilename(
            title="Select Job Description",
            filetypes=[("Supported files", "*.txt *.docx *.pdf"), ("All files", "*.*")],
        )
        if path:
            self.jd_path.set(path)

    def _pick_resumes(self):
        path = filedialog.askdirectory(title="Select Resumes Folder")
        if path:
            self.resumes_dir.set(path)

    def _run_analysis(self):
        if not self.jd_path.get() or not self.resumes_dir.get():
            messagebox.showwarning("Missing input", "Please select both a JD file and a resumes folder.")
            return
        self.run_btn.config(state="disabled")
        self.status_var.set("Analyzing...")
        threading.Thread(target=self._run_analysis_worker, daemon=True).start()

    def _run_analysis_worker(self):
        try:
            resume_paths = collect_resume_paths(self.resumes_dir.get())
            if not resume_paths:
                self._on_error("No supported resume files (.txt/.docx/.pdf) found in that folder.")
                return
            analyzer = ResumeAnalyzer()
            results, jd_meta = analyzer.analyze(self.jd_path.get(), resume_paths)
            self.results, self.jd_meta = results, jd_meta
            self.after(0, self._populate_table)
        except ExtractionError as exc:
            self._on_error(str(exc))
        except Exception as exc:  # pragma: no cover - safety net for the GUI
            self._on_error(f"Unexpected error: {exc}")

    def _on_error(self, message):
        self.after(0, lambda: messagebox.showerror("Error", message))
        self.after(0, lambda: self.status_var.set("Error - see message above."))
        self.after(0, lambda: self.run_btn.config(state="normal"))

    def _populate_table(self):
        self.tree.delete(*self.tree.get_children())
        rank = 0
        for r in self.results:
            if r.error:
                self.tree.insert("", "end", values=("-", os.path.basename(r.filename), "ERROR", "-", "-", "-"))
                continue
            rank += 1
            self.tree.insert("", "end", iid=str(rank - 1), values=(
                rank, os.path.basename(r.filename),
                f"{r.final_score * 100:.2f}", f"{r.skill_score * 100:.1f}",
                f"{r.experience_score * 100:.1f}", f"{r.education_score * 100:.1f}",
            ))
        self.status_var.set(f"Done. {len(self.results)} resume(s) analyzed.")
        self.run_btn.config(state="normal")

    def _show_detail(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        try:
            idx = int(selection[0])
        except ValueError:
            return
        ranked = [r for r in self.results if r.error is None]
        if idx >= len(ranked):
            return
        r = ranked[idx]
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END,
            f"Matched skills: {', '.join(sorted(r.matched_skills)) or 'none'}\n"
            f"Missing skills: {', '.join(sorted(r.missing_skills)) or 'none'}\n"
            f"Candidate experience: {r.candidate_years} year(s)   "
            f"Education keyword detected: {r.education_keyword or 'none'}"
        )

    def _export_html(self):
        if not self.results:
            messagebox.showinfo("Nothing to export", "Run an analysis first.")
            return
        path = rg.save_html_report(self.results, self.jd_meta, os.path.join(OUTPUT_DIR, "report.html"))
        webbrowser.open(f"file://{os.path.abspath(path)}")

    def _export_json(self):
        if not self.results:
            messagebox.showinfo("Nothing to export", "Run an analysis first.")
            return
        path = rg.save_json_report(self.results, self.jd_meta, os.path.join(OUTPUT_DIR, "report.json"))
        messagebox.showinfo("Exported", f"JSON report saved to:\n{os.path.abspath(path)}")


if __name__ == "__main__":
    app = ResumeAnalyzerGUI()
    app.mainloop()
