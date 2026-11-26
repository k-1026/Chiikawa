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
@page{size:A4;margin:17mm 16mm 19mm}
*{box-sizing:border-box;word-break:keep-all;overflow-wrap:normal;hyphens:none}
body{font-family:'Apple SD Gothic Neo','Malgun Gothic','Noto Sans CJK KR',sans-serif;color:#29243B;font-size:10.5pt;line-height:1.65;-webkit-print-color-adjust:exact;print-color-adjust:exact}
h1{font-size:20pt;text-align:center;margin:0 0 12px;line-height:1.4}h1 small{font-size:11pt;color:#70677F;font-weight:400}
.warn{background:#FFF6DE;border:1px solid #D9BC71;padding:9px 12px;font-size:9pt;line-height:1.6;margin:8px 0;break-inside:avoid}
.meta{text-align:right;color:#70677F;font-size:9pt}
h2{font-size:13pt;margin:18px 0 8px;padding:5px 8px;border-left:5px solid #7955AE;background:#EEE8F7;break-after:avoid;page-break-after:avoid}
h3{font-size:11pt;margin:12px 0 6px;break-after:avoid;page-break-after:avoid}
p{margin:5px 0;orphans:3;widows:3}.note{font-size:9pt;color:#645870}
table{width:100%;table-layout:fixed;border-collapse:separate;border-spacing:0;margin:8px 0 12px;font-size:9.5pt;border:0;break-inside:auto}
thead{display:table-header-group}tbody{break-inside:auto}
tr{break-inside:avoid;page-break-inside:avoid}
th,td{border:1px solid #8B7D9B;border-bottom:1px solid #8B7D9B;padding:7px 9px;vertical-align:top;text-align:left;box-decoration-break:clone;-webkit-box-decoration-break:clone}
th{background:#EEE8F7;color:#413053;font-weight:700}tbody tr:nth-child(even) td{background:#F8F6FC}
.blank{color:#8F4929;background:#FFF0E6;padding:0 3px;font-size:9pt}
.fig{text-align:center;margin:8px 0;break-inside:avoid}.fig img{width:56%;max-width:100%;border:1px solid #8B7D9B}.fig small{display:block;color:#70677F;font-size:9pt}
.foot{text-align:center;color:#81788D;font-size:9pt;margin-top:18px;border-top:1px solid #C9BED8;padding-top:8px;break-inside:avoid}
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
                header="<thead>"+rows[0]+"</thead>" if hdr=="col" and rows else ""
                bodyrows=rows[1:] if header else rows
                count=max((len(r) for r in b.get("rows",[])),default=1)
                widths=([30,70] if hdr=="row" else [35,65]) if count==2 else [100/count]*count
                cols="<colgroup>"+"".join('<col style="width:'+str(v)+'%">' for v in widths)+"</colgroup>"
                o.append("<table>"+cols+header+"<tbody>"+"".join(bodyrows)+"</tbody></table>")
            elif t == "img":
                o.append('<p class="fig"><img src="'+html.escape(b.get("src",""),quote=True)+'" alt="">'+('<small>'+html.escape(b.get("caption",""))+'</small>' if b.get("caption") else '')+'</p>')
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
        import os
        sandbox = ["--no-sandbox"] if hasattr(os, "geteuid") and os.geteuid() == 0 else []  # Render(Docker)는 root 로 실행된다
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", *sandbox,
                        f"--user-data-dir={d}/prof", f"--print-to-pdf={p}", h.as_uri()],
                       check=True, capture_output=True, timeout=60)
        return p.read_bytes()


def to_docx(m: dict) -> bytes:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    from docx.shared import Pt, Cm

    def xml(parent,tag,**attrs):
        node=OxmlElement('w:'+tag)
        for key,value in attrs.items():node.set(qn('w:'+key),str(value))
        parent.append(node);return node
    def paragraph_style(p):
        prop=p._p.get_or_add_pPr()
        # Word uses on=word-level and off=character-level for Korean (MS-OI29500).
        xml(prop,'wordWrap',val='1');xml(prop,'kinsoku',val='1');xml(prop,'suppressAutoHyphens',val='1')
        p.paragraph_format.space_after=Pt(4);p.paragraph_format.line_spacing=1.5
        for run in p.runs:
            rpr=run._r.get_or_add_rPr();xml(rpr,'lang',val='ko-KR',eastAsia='ko-KR')
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "맑은 고딕"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")
    st.font.size = Pt(10.5)
    for s in d.sections:
        s.page_width=Cm(21);s.page_height=Cm(29.7)
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
                tb.style = "Table Grid";tb.autofit=False
                hdr=b.get('hdr','row');count=len(tb.columns)
                widths=([30,70] if hdr=='row' else [35,65]) if count==2 else [100/count]*count
                for ci,column in enumerate(tb.columns):column.width=Cm(17*widths[ci]/100)
                borders=xml(tb._tbl.tblPr,'tblBorders')
                for side in ('top','left','bottom','right','insideH','insideV'):xml(borders,side,val='single',sz='8',color='8B7D9B')
                for ri,row in enumerate(tb.rows):
                    trpr=row._tr.get_or_add_trPr();xml(trpr,'cantSplit')
                    if hdr=='col' and ri==0:xml(trpr,'tblHeader')
                    for ci,cell in enumerate(row.cells):
                        cell.width=Cm(17*widths[ci]/100)
                        pr=cell._tc.get_or_add_tcPr();cb=xml(pr,'tcBorders')
                        for side in ('top','left','bottom','right'):xml(cb,side,val='single',sz='8',color='8B7D9B')
                        is_head=(hdr=='col' and ri==0) or (hdr=='row' and ci==0)
                        xml(pr,'shd',val='clear',color='auto',fill='EEE8F7' if is_head else 'F8F6FC' if ri%2 else 'FFFFFF')
                        mar=xml(pr,'tcMar')
                        for side in ('top','bottom'):xml(mar,side,w='100',type='dxa')
                        for side in ('left','right'):xml(mar,side,w='115',type='dxa')
                for ri, r in enumerate(rows):
                    for ci, v in enumerate(r):
                        cell = tb.cell(ri, ci); cell.text = ""
                        run = cell.paragraphs[0].add_run(_c(v)); run.font.size = Pt(9.5)
                        if (b.get("hdr", "row") == "col" and ri == 0) or (b.get("hdr", "row") == "row" and ci == 0):
                            run.bold = True
                d.add_paragraph()
            elif tp == "img":
                import base64
                try:
                    pic = d.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    pic.add_run().add_picture(io.BytesIO(base64.b64decode(b.get("src", "").split(",", 1)[-1])), width=Cm(8.5))
                    if b.get("caption"):
                        cap = d.add_paragraph(b["caption"]); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER; cap.runs[0].font.size = Pt(9)
                except Exception:
                    pass
            elif tp == "h3":
                p = d.add_paragraph(); rr = p.add_run(b.get("text", "")); rr.bold = True
            else:
                p = d.add_paragraph(_c(b.get("text", "")))
                if tp == "note":
                    p.runs[0].font.size = Pt(9)
    if m.get("foot"):
        p = d.add_paragraph(m["foot"]); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].font.size = Pt(9)
    for para in d.paragraphs:paragraph_style(para)
    for table in d.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:paragraph_style(para)
    for para in d.paragraphs:
        if para.runs and para.runs[0].bold:para.paragraph_format.keep_with_next=True
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
            elif tp == "img":
                if b.get("caption"):
                    d.add_paragraph(b["caption"])  # 한글 파일에는 그림 대신 설명만 넣는다(그림은 PDF·Word 에 포함)
            else:
                d.add_paragraph(_c(b.get("text", "")) if tp != "h3" else b.get("text", ""))
    if m.get("foot"):
        d.add_paragraph(m["foot"])
    return style_hwpx(d.to_bytes(),m)


def style_hwpx(data,model):
    """Preserve package namespaces, set word-level flow and non-clipping multipage tables."""
    import copy,math,unicodedata,zipfile
    from lxml import etree as E
    ns={'hh':'http://www.hancom.co.kr/hwpml/2011/head','hp':'http://www.hancom.co.kr/hwpml/2011/paragraph','hc':'http://www.hancom.co.kr/hwpml/2011/core'}
    q=lambda prefix,name:'{'+ns[prefix]+'}'+name
    zin=zipfile.ZipFile(io.BytesIO(data));head=E.fromstring(zin.read('Contents/header.xml'))
    fills=head.find('.//hh:borderFills',ns);base=next(f for f in fills if f.get('id')=='3')
    ids={};maximum=max(int(f.get('id','0')) for f in fills)
    for i,color in enumerate(['#EEE8F7','#FFFFFF','#F8F6FC'],1):
        fill=copy.deepcopy(base);fill.set('id',str(maximum+i));fill.set('breakCellSeparateLine','1')
        for side in ('leftBorder','rightBorder','topBorder','bottomBorder'):
            border=fill.find('hh:'+side,ns);border.set('width','0.2 mm');border.set('color','#8B7D9B');border.set('type','SOLID')
        brush=E.SubElement(fill,q('hc','fillBrush'));E.SubElement(brush,q('hc','winBrush'),faceColor=color,hatchColor='#8B7D9B',alpha='0')
        fills.append(fill);ids[color]=fill.get('id')
    fills.set('itemCnt',str(len(fills)))
    for setting in head.findall('.//hh:breakSetting',ns):
        setting.set('breakLatinWord','KEEP_WORD');setting.set('breakNonLatinWord','KEEP_WORD');setting.set('widowOrphan','1')
    table_models=[b for s in model.get('sections',[]) for b in s.get('blocks',[]) if b.get('t')=='table' and b.get('rows')]
    sections={};ti=0
    for name in zin.namelist():
        if not (name.startswith('Contents/section') and name.endswith('.xml')):continue
        section=E.fromstring(zin.read(name))
        for table in section.findall('.//hp:tbl',ns):
            spec=table_models[ti];ti+=1;hdr=spec.get('hdr','row');nc=int(table.get('colCnt'))
            table.set('pageBreak','CELL');table.set('repeatHeader','1' if hdr=='col' else '0');table.set('borderFillIDRef',ids['#FFFFFF'])
            pos=table.find('hp:pos',ns);pos.set('treatAsChar','0');pos.set('flowWithText','1');pos.set('allowOverlap','0')
            fractions=([.30,.70] if hdr=='row' else [.35,.65]) if nc==2 else [1/nc]*nc
            widths=[int(42520*f) for f in fractions];widths[-1]=42520-sum(widths[:-1]);total_height=0
            for ri,row in enumerate(table.findall('hp:tr',ns)):
                cells=row.findall('hp:tc',ns);heights=[]
                for ci,cell in enumerate(cells):
                    is_head=(hdr=='col' and ri==0) or (hdr=='row' and ci==0)
                    cell.set('header','1' if hdr=='col' and ri==0 else '0');cell.set('hasMargin','1')
                    cell.set('borderFillIDRef',ids['#EEE8F7' if is_head else '#F8F6FC' if ri%2 else '#FFFFFF'])
                    sub=cell.find('hp:subList',ns);sub.set('vertAlign','TOP')
                    margin=cell.find('hp:cellMargin',ns)
                    for edge,value in [('left','650'),('right','650'),('top','400'),('bottom','400')]:margin.set(edge,value)
                    text=''.join(cell.itertext());capacity=max(1,(widths[ci]-1300)/1000)
                    # Conservative initial height; editable cells still flow across pages.
                    lines=sum(max(1,math.ceil(sum(1 if unicodedata.east_asian_width(c) in 'WF' else .55 for c in part)/capacity)) for part in text.split('\n'))
                    heights.append(800+max(1,lines)*1600)
                    cell.find('hp:cellSz',ns).set('width',str(widths[ci]))
                height=max(heights,default=2400);total_height+=height
                for cell in cells:cell.find('hp:cellSz',ns).set('height',str(height))
            table.find('hp:sz',ns).set('height',str(total_height))
        # Stale caches prevent the target editor from reflowing word-level changes.
        for seg in section.findall('.//hp:linesegarray',ns):seg.getparent().remove(seg)
        sections[name]=E.tostring(section,xml_declaration=True,encoding='UTF-8',standalone=True)
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for info in zin.infolist():z.writestr(info,E.tostring(head,xml_declaration=True,encoding='UTF-8',standalone=True) if info.filename=='Contents/header.xml' else sections.get(info.filename,zin.read(info.filename)))
    return out.getvalue()
