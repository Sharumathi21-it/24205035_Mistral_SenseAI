import json
import os
from datetime import datetime


def print_console_report(results, jd_meta, top_n=None):
    ranked = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]
    if top_n:
        ranked = ranked[:top_n]

    print("=" * 78)
    print("INTELLIGENT RESUME ANALYZER - RANKING REPORT")
    print("=" * 78)
    print(f"JD required skills   : {', '.join(jd_meta['jd_skills']) or 'none detected'}")
    print(f"JD required experience: {jd_meta['jd_required_years']} year(s)")
    print("-" * 78)

    for i, r in enumerate(ranked, start=1):
        print(f"#{i}  {os.path.basename(r.filename)}  ->  {r.final_score * 100:.2f}%")
        print(f"     text similarity: {r.text_similarity * 100:5.2f}%   "
              f"skills: {r.skill_score * 100:5.2f}%   "
              f"experience: {r.experience_score * 100:5.2f}%   "
              f"education: {r.education_score * 100:5.2f}%")
        if r.matched_skills:
            print(f"     matched skills : {', '.join(sorted(r.matched_skills))}")
        if r.missing_skills:
            print(f"     missing skills : {', '.join(sorted(r.missing_skills))}")
        print("-" * 78)

    if failed:
        print("Files that could not be processed:")
        for r in failed:
            print(f"   - {os.path.basename(r.filename)}: {r.error}")
        print("-" * 78)


def save_json_report(results, jd_meta, output_path):
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "jd_summary": jd_meta,
        "candidates": [r.as_dict() for r in results],
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return output_path


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Resume Analyzer Report</title>
<style>
  :root {{
    --bg: #0f172a;
    --card: #1e293b;
    --accent: #38bdf8;
    --good: #22c55e;
    --warn: #f59e0b;
    --text: #e2e8f0;
    --muted: #94a3b8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 32px;
    background: var(--bg); color: var(--text);
    font-family: 'Segoe UI', Roboto, Arial, sans-serif;
  }}
  h1 {{ margin-bottom: 4px; }}
  .subtitle {{ color: var(--muted); margin-bottom: 24px; }}
  .jd-box {{
    background: var(--card); border-radius: 10px; padding: 16px 20px;
    margin-bottom: 28px; border: 1px solid #334155;
  }}
  .card {{
    background: var(--card); border-radius: 10px; padding: 20px 24px;
    margin-bottom: 18px; border: 1px solid #334155;
  }}
  .card.rank1 {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }}
  .row {{ display: flex; justify-content: space-between; align-items: center; }}
  .score {{ font-size: 1.6em; font-weight: 700; color: var(--accent); }}
  .bar-wrap {{ background: #0b1220; border-radius: 6px; overflow: hidden; height: 10px; margin: 4px 0 10px 0; }}
  .bar {{ height: 100%; background: linear-gradient(90deg, var(--accent), var(--good)); }}
  .metric-label {{ font-size: 0.82em; color: var(--muted); display:flex; justify-content: space-between; }}
  .tags {{ margin-top: 8px; }}
  .tag {{
    display: inline-block; padding: 3px 9px; border-radius: 999px;
    font-size: 0.78em; margin: 3px 4px 0 0;
  }}
  .tag.match {{ background: rgba(34,197,94,0.15); color: var(--good); border: 1px solid var(--good); }}
  .tag.missing {{ background: rgba(245,158,11,0.15); color: var(--warn); border: 1px solid var(--warn); }}
  .error {{ color: #f87171; }}
  .badge {{
    background: var(--accent); color: #04212f; font-weight: 700;
    border-radius: 6px; padding: 2px 10px; font-size: 0.85em;
  }}
</style>
</head>
<body>
  <h1>Intelligent Resume Analyzer</h1>
  <div class="subtitle">Generated {generated_at} &middot; {n_candidates} candidate(s) ranked</div>

  <div class="jd-box">
    <strong>Job Description Requirements Detected</strong><br>
    Skills: {jd_skills}<br>
    Minimum experience: {jd_years} year(s)
  </div>

  {cards}

</body>
</html>
"""

_CARD_TEMPLATE = """
  <div class="card {rank_class}">
    <div class="row">
      <div><span class="badge">#{rank}</span> &nbsp; <strong>{filename}</strong></div>
      <div class="score">{final_score:.2f}%</div>
    </div>

    <div class="metric-label"><span>Text similarity</span><span>{text_sim:.1f}%</span></div>
    <div class="bar-wrap"><div class="bar" style="width:{text_sim:.1f}%"></div></div>

    <div class="metric-label"><span>Skill match</span><span>{skill:.1f}%</span></div>
    <div class="bar-wrap"><div class="bar" style="width:{skill:.1f}%"></div></div>

    <div class="metric-label"><span>Experience match</span><span>{exp:.1f}%</span></div>
    <div class="bar-wrap"><div class="bar" style="width:{exp:.1f}%"></div></div>

    <div class="metric-label"><span>Education match</span><span>{edu:.1f}%</span></div>
    <div class="bar-wrap"><div class="bar" style="width:{edu:.1f}%"></div></div>

    <div class="tags">
      {matched_tags}
      {missing_tags}
    </div>
  </div>
"""

_ERROR_CARD_TEMPLATE = """
  <div class="card">
    <div class="row"><strong>{filename}</strong></div>
    <div class="error">Could not process: {error}</div>
  </div>
"""


def _render_card(rank, result):
    if result.error:
        return _ERROR_CARD_TEMPLATE.format(
            filename=os.path.basename(result.filename), error=result.error
        )

    matched_tags = "".join(
        f'<span class="tag match">{s}</span>' for s in sorted(result.matched_skills)
    )
    missing_tags = "".join(
        f'<span class="tag missing">missing: {s}</span>' for s in sorted(result.missing_skills)
    )

    return _CARD_TEMPLATE.format(
        rank=rank,
        rank_class="rank1" if rank == 1 else "",
        filename=os.path.basename(result.filename),
        final_score=result.final_score * 100,
        text_sim=result.text_similarity * 100,
        skill=result.skill_score * 100,
        exp=result.experience_score * 100,
        edu=result.education_score * 100,
        matched_tags=matched_tags,
        missing_tags=missing_tags,
    )


def save_html_report(results, jd_meta, output_path):
    cards = []
    rank = 0
    for r in results:
        if r.error is None:
            rank += 1
            cards.append(_render_card(rank, r))
        else:
            cards.append(_render_card(0, r))

    html = _HTML_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        n_candidates=len(results),
        jd_skills=", ".join(jd_meta["jd_skills"]) or "none detected",
        jd_years=jd_meta["jd_required_years"],
        cards="".join(cards),
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
