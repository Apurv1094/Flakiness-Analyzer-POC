"""Generate a standalone, interactive HTML report from AI failure analysis CSV.

Usage:
    python generate_ai_dashboard.py --input internet_output/ai_failure_analysis.csv --output internet_output/ai_dashboard.html

Requires only Python standard library.
"""
import argparse
import csv
import html
import json
from collections import Counter
from pathlib import Path


def generate(input_path: Path, output_path: Path):
    if not input_path.is_file():
        raise FileNotFoundError(f"AI results CSV not found: {input_path}")
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames or []
    required = {"test_name", "rule_category", "ai_category", "agreement", "probable_root_cause", "recommended_action"}
    missing = required - set(columns)
    if missing:
        raise ValueError("Missing required CSV columns: " + ", ".join(sorted(missing)))

    def value(row, key):
        return (row.get(key) or "").strip()

    def analyzed(row):
        return bool(value(row, "ai_category")) and value(row, "ai_category").lower() not in {"not analyzed", "n/a", "none"} and not value(row, "ai_error")

    completed = [r for r in rows if analyzed(r)]
    ai_counts = Counter(value(r, "ai_category") or "Uncategorized" for r in completed)
    # Treat "Different" (produced by the AI analyzer) as a disagreement.
    # Normalize for reporting without modifying the source CSV.
    def agreement_status(row):
        raw = value(row, "agreement").lower()
        if raw == "match":
            return "Match"
        if raw in {"different", "mismatch"}:
            return "Mismatch"
        return "Not available"

    matches = sum(agreement_status(r) == "Match" for r in completed)
    mismatches = sum(agreement_status(r) == "Mismatch" for r in completed)
    errors = sum(bool(value(r, "ai_error")) for r in rows)
    rate = f"{matches / (matches + mismatches) * 100:.1f}%" if matches + mismatches else "N/A"

    # JSON is embedded as an inert data script. Escape '<' to prevent accidental script closing.
    payload = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    categories = sorted(ai_counts.items(), key=lambda p: (-p[1], p[0]))
    bars = "".join(
        f'<div class="bar-row"><span class="bar-label" title="{html.escape(cat, quote=True)}">{html.escape(cat)}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{(count/max(ai_counts.values())*100) if ai_counts else 0:.1f}%"></div></div>'
        f'<strong>{count}</strong></div>' for cat, count in categories
    ) or '<p class="muted">No successful AI classifications found.</p>'

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Failure Analysis Dashboard</title>
<style>
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#e9eef8;background:#0d1424;font-size:14px}
*{box-sizing:border-box}body{margin:0}main{max-width:1380px;margin:auto;padding:32px 24px 64px}
h1{font-size:29px;margin:0 0 6px}h2{font-size:18px;margin:0 0 18px}p{line-height:1.5}
.muted{color:#9aacc6}.intro{margin:0 0 28px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:14px;margin-bottom:22px}
.card,.panel{background:#172239;border:1px solid #2b3a55;border-radius:14px;padding:20px}
.metric{font-size:29px;font-weight:750;margin-top:10px}.metric-label{color:#b7c5dc;font-size:12px}
.panels{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(260px,1fr);gap:18px;margin-bottom:20px}
.bar-row{display:grid;grid-template-columns:180px 1fr 35px;align-items:center;gap:12px;margin:12px 0}.bar-label{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{height:16px;background:#263753;border-radius:8px;overflow:hidden}.bar-fill{height:100%;background:linear-gradient(90deg,#3d8eff,#67d5cc);border-radius:8px}
.agree{display:flex;flex-wrap:wrap;gap:10px}.pill{border-radius:99px;padding:9px 13px;background:#263753}.pill strong{color:#8cddcc}
.filters{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 14px}input,select{background:#0e192c;color:#f0f5ff;border:1px solid #435370;border-radius:8px;padding:11px;min-width:180px}input{flex:1;min-width:220px}
.table-wrap{overflow:auto;max-height:650px;border:1px solid #30415e;border-radius:10px}
table{width:100%;border-collapse:collapse;min-width:1080px}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #2c3a53}th{position:sticky;top:0;background:#23324d;z-index:1}td{max-width:290px;overflow-wrap:anywhere}tr:hover td{background:#1e2c45}
.tag{display:inline-block;border-radius:6px;padding:4px 7px;background:#30435f}.match{color:#7be0c0}.mismatch{color:#ffca87}.err{color:#ff9ca7}
details{margin:0}summary{cursor:pointer;color:#a8caff;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:250px;overflow:auto;font:12px/1.5 Consolas,monospace;color:#d2deee}
.note{font-size:12px;color:#9aacc6;margin-top:15px}@media(max-width:850px){.panels{grid-template-columns:1fr}.bar-row{grid-template-columns:130px 1fr 25px}main{padding:20px 12px}}
</style></head><body><main>
<h1>AI Failure Analysis Dashboard</h1><p class="muted intro">AI-generated classifications, probable root causes, and recommended actions for test execution failures.</p>
<section class="cards">
<div class="card"><div class="metric-label">Total input records</div><div class="metric">__TOTAL__</div></div>
<div class="card"><div class="metric-label">Successfully AI analyzed</div><div class="metric">__ANALYZED__</div></div>
<div class="card"><div class="metric-label">AI errors</div><div class="metric">__ERRORS__</div></div>
<div class="card"><div class="metric-label">Rule vs AI agreement</div><div class="metric">__RATE__</div></div>
</section>
<section class="panels"><div class="panel"><h2>AI Failure Categories</h2>__BARS__</div>
<div class="panel"><h2>Rule-Based vs AI Classification</h2><div class="agree"><span class="pill">Match: <strong>__MATCHES__</strong></span><span class="pill">Mismatch: <strong>__MISMATCHES__</strong></span></div>
<p class="note">Agreement compares two automated classifiers. It does not establish correctness or replace manual validation.</p>
<h2 style="margin-top:25px">Review required</h2><p id="review-count" class="metric">—</p><p class="muted">Based on the CSV review_required field.</p></div></section>
<section class="panel"><h2>Detailed AI Analysis <span class="muted" id="visible-count"></span></h2>
<div class="filters"><input id="search" placeholder="Search tests, root causes, recommendations, errors..." aria-label="Search results">
<select id="category" aria-label="Filter AI category"><option value="">All AI categories</option></select>
<select id="agreement" aria-label="Filter agreement"><option value="">All agreements</option></select>
<select id="review" aria-label="Filter review status"><option value="">All review statuses</option><option value="true">Review required</option><option value="false">Review not required</option></select></div>
<div class="table-wrap"><table><thead><tr><th>Test / Timestamp</th><th>Rule category</th><th>AI category</th><th>Agreement</th><th>Confidence</th><th>Probable root cause</th><th>Recommended action</th><th>Details</th></tr></thead><tbody id="rows"></tbody></table></div>
<p class="note">AI recommendations are hypotheses based on supplied failure logs; investigate before changing tests or application code. Data is embedded in this HTML, so treat the report as potentially sensitive.</p>
</section></main>
<script type="application/json" id="dataset">__PAYLOAD__</script>
<script>
const records=JSON.parse(document.getElementById('dataset').textContent);
const el=id=>document.getElementById(id);
const text=(r,k)=>String(r[k]??'').trim();
const clean=(v)=>v.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const agreementStatus=(r)=>{const a=text(r,'agreement').toLowerCase();return a==='match'?'Match':['different','mismatch'].includes(a)?'Mismatch':'Not available'};
const review=(r)=>['true','yes','1'].includes(text(r,'review_required').toLowerCase());
const opts=(id,key)=>{[...new Set(records.map(r=>text(r,key)).filter(Boolean))].sort().forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=v;el(id).append(o)})};
opts('category','ai_category');
[...new Set(records.map(agreementStatus))].sort().forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=v;el('agreement').append(o)});
el('review-count').textContent=records.filter(review).length;
function render(){
 const query=el('search').value.toLowerCase(),cat=el('category').value,agree=el('agreement').value,rev=el('review').value;
 const filtered=records.filter(r=>(!cat||text(r,'ai_category')===cat)&&(!agree||agreementStatus(r)===agree)&&(!rev||String(review(r))===rev)&&(!query||Object.values(r).some(v=>String(v??'').toLowerCase().includes(query))));
 el('visible-count').textContent=`(${filtered.length} of ${records.length})`;
 el('rows').innerHTML=filtered.map(r=>{
  const a=agreementStatus(r),cl=a==='Match'?'match':a==='Mismatch'?'mismatch':'';
  const extra=[['Explanation','explanation'],['Error message','error_message'],['AI error','ai_error']].filter(([label,key])=>text(r,key)).map(([label,key])=>`<strong>${label}</strong><pre>${clean(text(r,key))}</pre>`).join('');
  return `<tr><td><strong>${clean(text(r,'test_name'))}</strong><div class="muted">${clean(text(r,'execution_timestamp'))}</div></td><td>${clean(text(r,'rule_category'))}</td><td><span class="tag">${clean(text(r,'ai_category')||'Not analyzed')}</span></td><td class="${cl}">${clean(a)}</td><td>${clean(text(r,'confidence'))}</td><td>${clean(text(r,'probable_root_cause'))}</td><td>${clean(text(r,'recommended_action'))}</td><td><details><summary>View</summary>${extra||'No additional details'}</details></td></tr>`
 }).join('')||'<tr><td colspan="8">No records match the selected filters.</td></tr>';
}
['search','category','agreement','review'].forEach(id=>el(id).addEventListener(id==='search'?'input':'change',render));render();
</script></body></html>'''
    replacements = {
        "__TOTAL__": str(len(rows)), "__ANALYZED__": str(len(completed)),
        "__ERRORS__": str(errors), "__RATE__": rate,
        "__BARS__": bars, "__MATCHES__": str(matches),
        "__MISMATCHES__": str(mismatches), "__PAYLOAD__": payload,
    }
    for key, replacement in replacements.items():
        page = page.replace(key, replacement)
    output_path.write_text(page, encoding="utf-8")
    print(f"Created: {output_path.resolve()}")
    print(f"Records: {len(rows)} | AI analyzed: {len(completed)} | Errors: {errors} | Agreement: {rate}")


def main():
    parser = argparse.ArgumentParser(description="Generate standalone HTML AI failure analysis dashboard")
    parser.add_argument("--input", default="internet_output/ai_failure_analysis.csv", type=Path)
    parser.add_argument("--output", default="internet_output/ai_dashboard.html", type=Path)
    args = parser.parse_args()
    generate(args.input, args.output)

if __name__ == "__main__":
    main()
