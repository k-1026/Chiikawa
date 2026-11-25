"""기획안 문서 모델 -> HTML / PDF(headless Chrome) / Word(.docx) / 한글(.hwpx) 로 내보낸다.

문서 모델(dict):
  title, subtitle, warn[list[str]], meta, foot
  sections[ {h, blocks[ {t:'p'|'h3'|'note', text} | {t:'table', rows:[[..]], hdr:'col'|'row'|'none'} ] } ]
빈 문자열 칸은 '미입력 · 직접 작성'으로 표시한다."""
import html
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

BLANK = "미입력 · 직접 작성"
CHROME = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "",
]

CSS = """
@page{size:A4;margin:16mm}
body{font-family:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans CJK KR',sans-serif;color:#111;font-size:11pt;line-height:1.6}
h1{font-size:20pt;text-align:center;margin:0 0 10px;line-height:1.35}h1 small{font-size:12pt;color:#667;font-weight:400}
.warn{background:#FFF6D6;border:1px solid #E8C65A;padding:7px 10px;font-size:9.5pt;line-height:1.55;border-radius:4px;margin:6px 0}
.meta{text-align:right;color:#667;font-size:9.5pt;margin:4px 0}
h2{font-size:13pt;margin:16px 0 6px;padding:3px 0 3px 8px;border-left:5px solid #3DA9DB;background:#F1F8FD;page-break-after:avoid}
h3{font-size:11pt;margin:10px 0 4px}
p{margin:4px 0}.note{font-size:9.5pt;color:#445}
table{width:100%;border-collapse:collapse;margin:5px 0;font-size:10pt;page-break-inside:auto}
tr{page-break-inside:avoid}
th,td{border:1px solid #9AA7B5;padding:4px 7px;vertical-align:top;text-align:left}
th{background:#EEF3F8;font-weight:700}.k{background:#F6F8FA;font-weight:700}
.blank{color:#B0481F;background:#FFF0E6;padding:0 4px;border-radius:3px;font-size:9.5pt}
.foot{text-align:center;color:#889;font-size:9pt;margin-top:18px;border-top:1px solid #CCD;padding-top:6px}
"""


def _c(x):
    x = "" if x is None else str(x).strip()
    return x if x else BLANK


def _hc(x):
    t = _c(x)
    return f'<span class="blank">{BLANK}</span>' if t == BLANK else html.escape(t).replace("\n", "<br>")


def model_to_html(m: dict, full=True) -> str:
    o = [f'<h1>{html.escape(m.get("title",""))}<br><small>{html.escape(m.get("subtitle",""))}</small></h1>']
    if m.get("warn"):
        o.append('<div class="warn">' + "<br>".join(html.escape(w) for w in m["warn"]) + "</div>")
    if m.get("meta"):
        o.append(f'<p class="meta">{html.escape(m["meta"])}</p>')
    for s in m.get("sections", []):
        o.append(f'<h2>{html.escape(s.get("h",""))}</h2>')
        for b in s.get("blocks", []):
            t = b.get("t")
            if t == "table":
                hdr = b.get("hdr", "row")
                rows = []
                for ri, r in enumerate(b.get("rows", [])):
                    cells = []
                    for ci, v in enumerate(r):
                        tag = "th" if (hdr == "col" and ri == 0) or (hdr == "row" and ci == 0) else "td"
                        cells.append(f"<{tag}>{_hc(v)}</{tag}>")
                    rows.append("<tr>" + "".join(cells) + "</tr>")
                o.append("<table>" + "".join(rows) + "</table>")
            elif t == "h3":
                o.append(f'<h3>{html.escape(b.get("text",""))}</h3>')
            elif t == "note":
                o.append(f'<p class="note">{_hc(b.get("text",""))}</p>')
            else:
                o.append(f'<p>{_hc(b.get("text",""))}</p>')
    if m.get("foot"):
        o.append(f'<p class="foot">{html.escape(m["foot"])}</p>')
    body = "\n".join(o)
    if not full:
        return body
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(m.get("title",""))}</title><style>{CSS}</style></head><body>{body}</body></html>'


def to_pdf(m: dict) -> bytes:
    chrome = next((c for c in CHROME if c and Path(c).exists()), None)
    if not chrome:
        raise RuntimeError("PDF를 만들 Chrome을 찾지 못했어요. 브라우저 인쇄(PDF로 저장)를 쓰세요.")
    with tempfile.TemporaryDirectory() as d:
        h, p = Path(d) / "plan.html", Path(d) / "plan.pdf"
        h.write_text(model_to_html(m), encoding="utf-8")
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={d}/prof", f"--print-to-pdf={p}", h.as_uri()],
                       check=True, capture_output=True, timeout=60)
        return p.read_bytes()


def to_docx(m: dict) -> bytes:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Pt, Cm

    d = Document()
    st = d.styles["Normal"]
    st.font.name = "맑은 고딕"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")
    st.font.size = Pt(10.5)
    for s in d.sections:
        s.left_margin = s.right_margin = Cm(2)
        s.top_margin = s.bottom_margin = Cm(1.8)

    t = d.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run(m.get("title", "")); r.bold = True; r.font.size = Pt(19)
    if m.get("subtitle"):
        t2 = d.add_paragraph(); t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = t2.add_run(m["subtitle"]); r2.font.size = Pt(12)
    for w in m.get("warn", []):
        p = d.add_paragraph(); rr = p.add_run(w); rr.font.size = Pt(9); rr.font.color.rgb = None
    if m.get("meta"):
        p = d.add_paragraph(m["meta"]); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.runs[0].font.size = Pt(9)
    for s in m.get("sections", []):
        h = d.add_paragraph(); rh = h.add_run(s.get("h", "")); rh.bold = True; rh.font.size = Pt(13)
        for b in s.get("blocks", []):
            tp = b.get("t")
            if tp == "table":
                rows = b.get("rows", [])
                if not rows:
                    continue
                tb = d.add_table(rows=len(rows), cols=max(len(r) for r in rows))
                tb.style = "Table Grid"
                for ri, r in enumerate(rows):
                    for ci, v in enumerate(r):
                        cell = tb.cell(ri, ci); cell.text = ""
                        run = cell.paragraphs[0].add_run(_c(v)); run.font.size = Pt(9.5)
                        if (b.get("hdr", "row") == "col" and ri == 0) or (b.get("hdr", "row") == "row" and ci == 0):
                            run.bold = True
                d.add_paragraph()
            elif tp == "h3":
                p = d.add_paragraph(); rr = p.add_run(b.get("text", "")); rr.bold = True
            else:
                p = d.add_paragraph(_c(b.get("text", "")))
                if tp == "note":
                    p.runs[0].font.size = Pt(9)
    if m.get("foot"):
        p = d.add_paragraph(m["foot"]); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].font.size = Pt(9)
    bio = io.BytesIO(); d.save(bio)
    return bio.getvalue()


def to_hwpx(m: dict) -> bytes:
    from hwpx import HwpxDocument
    d = HwpxDocument.new()
    d.add_paragraph(m.get("title", ""))
    if m.get("subtitle"):
        d.add_paragraph(m["subtitle"])
    for w in m.get("warn", []):
        d.add_paragraph(w)
    if m.get("meta"):
        d.add_paragraph(m["meta"])
    for s in m.get("sections", []):
        d.add_paragraph("")
        d.add_paragraph(s.get("h", ""))
        for b in s.get("blocks", []):
            tp = b.get("t")
            if tp == "table":
                rows = b.get("rows", [])
                if not rows:
                    continue
                nc = max(len(r) for r in rows)
                tb = d.add_table(len(rows), nc)
                for ri, r in enumerate(rows):
                    for ci in range(nc):
                        tb.set_cell_text(ri, ci, _c(r[ci] if ci < len(r) else ""))
            else:
                d.add_paragraph(_c(b.get("text", "")) if tp != "h3" else b.get("text", ""))
    if m.get("foot"):
        d.add_paragraph(m["foot"])
    return d.to_bytes()
