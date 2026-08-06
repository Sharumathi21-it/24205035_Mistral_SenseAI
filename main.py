import argparse
import glob
import os
import sys

from analyzer import ResumeAnalyzer
from extractor import ExtractionError
import report_generator as rg

SUPPORTED_EXTENSIONS = (".txt", ".docx", ".pdf")


def collect_resume_paths(resumes_arg):
    """resumes_arg can be a folder or a comma-separated list of files."""
    paths = []
    if os.path.isdir(resumes_arg):
        for ext in SUPPORTED_EXTENSIONS:
            paths.extend(sorted(glob.glob(os.path.join(resumes_arg, f"*{ext}"))))
    else:
        for p in resumes_arg.split(","):
            p = p.strip()
            if p:
                paths.append(p)
    return paths


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Intelligent Resume Analyzer - rank resumes against a job description "
                    "using only Python's standard library."
    )
    parser.add_argument("--jd", required=True, help="Path to the job description file (.txt/.docx/.pdf)")
    parser.add_argument("--resumes", required=True,
                        help="Folder containing resumes, or a comma-separated list of resume file paths")
    parser.add_argument("--top", type=int, default=None, help="Only show the top N candidates")
    parser.add_argument("--output", default="../output", help="Output directory for reports")
    parser.add_argument("--format", choices=["console", "json", "html", "all"], default="all",
                        help="Which report format(s) to generate")
    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not os.path.isfile(args.jd):
        print(f"Error: JD file not found: {args.jd}", file=sys.stderr)
        return 1

    resume_paths = collect_resume_paths(args.resumes)
    if not resume_paths:
        print(f"Error: no resumes found at: {args.resumes}", file=sys.stderr)
        return 1

    analyzer = ResumeAnalyzer()
    try:
        results, jd_meta = analyzer.analyze(args.jd, resume_paths)
    except ExtractionError as exc:
        print(f"Error reading job description: {exc}", file=sys.stderr)
        return 1

    if args.format in ("console", "all"):
        rg.print_console_report(results, jd_meta, top_n=args.top)

    if args.format in ("json", "all"):
        path = rg.save_json_report(results, jd_meta, os.path.join(args.output, "report.json"))
        print(f"JSON report written to: {os.path.abspath(path)}")

    if args.format in ("html", "all"):
        path = rg.save_html_report(results, jd_meta, os.path.join(args.output, "report.html"))
        print(f"HTML report written to: {os.path.abspath(path)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
