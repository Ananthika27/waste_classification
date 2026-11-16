"""Build the project report by filling the college's own format file (report/template/CV_report_format.docx).

The title page (SRM logo, fonts, sizes, layout) is kept exactly as in the template; only the highlighted fields are changed.
Everything after it is generated in the same typography: Times New Roman, 14 pt bold centred chapter headings,
12 pt bold section headings, 12 pt justified body text.

    python report/build_figures.py && python report/build_report.py
"""
import math
import re
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import report_content as RC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "report/template/CV_report_format.docx"
OUT = ROOT / "report/EcoSort_AI_Project_Report.docx"
BUILD = ROOT / "report/_build"
FIG = ROOT / "report/figures"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = (f'xmlns:w="{W}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
q = lambda t: "{%s}%s" % (W, t)

# ---- page geometry (A4, as in the template) ; margins chosen for a bound report
PG_W, PG_H = 11910, 16840
M_TOP, M_BOT, M_LEFT, M_RIGHT = 1440, 1440, 2160, 1440
TW = PG_W - M_LEFT - M_RIGHT                     # text width in twips (8310)
TWP = TW / 20                                    # in points
CAP = (PG_H - M_TOP - M_BOT) / 20                # text height per page in points

# ---- font metrics for the page-number estimate (Word refreshes the real numbers on open)
SUP = "/System/Library/Fonts/Supplemental/"
_fonts = {}
def font(kind, pt):
    key = (kind, pt)
    if key not in _fonts:
        f = {"r": "Times New Roman.ttf", "b": "Times New Roman Bold.ttf", "c": "Courier New.ttf"}[kind]
        _fonts[key] = ImageFont.truetype(SUP + f, int(pt * 10))
    return _fonts[key]

def strip_md(t):
    return re.sub(r"\*\*|\*", "", t)

def n_lines(text, width_pt, pt=12, kind="r"):
    f = font(kind, pt)
    lines, cur = 1, 0.0
    for tok in re.findall(r"\S+\s*", strip_md(text)) or [""]:
        w, wt = f.getlength(tok) / 10, f.getlength(tok.rstrip()) / 10
        if cur + wt > width_pt and cur > 0:
            lines += 1
            cur = 0.0
        cur += w
    return lines

class Flow:
    def __init__(self, page):
        self.page, self.y = page, 0.0
    def add(self, h):
        self.y += h
        while self.y > CAP:
            self.page += 1
            self.y -= CAP
    def whole(self, h):
        if self.y + h > CAP:
            self.page += 1
            self.y = 0.0
        self.y += h
    def newpage(self):
        if self.y > 0:
            self.page += 1
            self.y = 0.0

# ---- XML helpers
esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
_bm = [100]
def next_id():
    _bm[0] += 1
    return _bm[0]

def rpr(b=False, i=False, sz=24, font_=None, hl=None):
    f = '<w:rFonts w:ascii="%s" w:hAnsi="%s" w:cs="%s"/>' % (font_, font_, font_) if font_ else ""
    bb = "<w:b/>" if b else ""
    ii = "<w:i/>" if i else ""
    hh = '<w:highlight w:val="%s"/>' % hl if hl else ""
    return "<w:rPr>%s%s%s<w:sz w:val=\"%d\"/><w:szCs w:val=\"%d\"/>%s</w:rPr>" % (f, bb, ii, sz, sz, hh)

def run(text, **kw):
    return f'<w:r>{rpr(**kw)}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

def runs(text, sz=24, b=False, i=False, font_=None):
    out = []
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not tok:
            continue
        if tok.startswith("**"):
            out.append(run(tok[2:-2], b=True, i=i, sz=sz, font_=font_))
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            out.append(run(tok[1:-1], b=b, i=True, sz=sz, font_=font_))
        else:
            out.append(run(tok, b=b, i=i, sz=sz, font_=font_))
    return "".join(out)

def para(inner, jc="both", before=0, after=120, line=360, left=None, right=None, hanging=None, keep_next=False,
         pbb=False, num=None, tabs=None, keep_lines=False, ppr_extra="", style=None):
    p = "<w:pPr>"
    if style: p += '<w:pStyle w:val="%s"/>' % style
    if keep_next: p += "<w:keepNext/>"
    if keep_lines: p += "<w:keepLines/>"
    if pbb: p += "<w:pageBreakBefore/>"
    if num is not None: p += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>'
    if tabs: p += "<w:tabs>" + "".join(f'<w:tab w:val="{v}" w:pos="{pos}"/>' for v, pos in tabs) + "</w:tabs>"
    p += f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>'
    if left is not None or right is not None or hanging is not None:
        p += "<w:ind" + (f' w:left="{left}"' if left is not None else "") + (f' w:right="{right}"' if right is not None else "") \
             + (f' w:hanging="{hanging}"' if hanging is not None else "") + "/>"
    p += f'<w:jc w:val="{jc}"/>{ppr_extra}</w:pPr>'
    return f"<w:p>{p}{inner}</w:p>"

def bookmark(name, inner):
    i = next_id()
    return f'<w:bookmarkStart w:id="{i}" w:name="{name}"/>{inner}<w:bookmarkEnd w:id="{i}"/>'

def field_pageref(bm, sz=24, b=False):
    rp = rpr(b=b, sz=sz)
    return (f'<w:r>{rp}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{rp}<w:instrText xml:space="preserve"> PAGEREF {bm} \\h </w:instrText></w:r>'
            f'<w:r>{rp}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{rp}<w:t>@@{bm}@@</w:t></w:r><w:r>{rp}<w:fldChar w:fldCharType="end"/></w:r>')

def roman(n):
    out = ""
    for v, s in [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]:
        while n >= v:
            out += s
            n -= v
    return out

def table_xml(rows, widths, aligns, header=True, borders=True, sz=22, shade="D9D9D9", spacing_cells=False):
    tot = sum(widths)
    bd = ("<w:tblBorders>" + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
          for s in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>") if borders else ""
    x = (f'<w:tbl><w:tblPr><w:tblW w:w="{tot}" w:type="dxa"/><w:jc w:val="center"/>{bd}<w:tblLayout w:type="fixed"/>'
         '<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>'
         '<w:tblLook w:val="04A0"/></w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>")
    for ri, row in enumerate(rows):
        hdr = header and ri == 0
        bold_row = (not hdr) and str(row[0]).startswith(("Total", "Macro", "All "))
        x += "<w:tr><w:trPr><w:cantSplit/>" + ("<w:tblHeader/>" if hdr else "") + "</w:trPr>"
        for ci, cell in enumerate(row):
            al = {"l": "left", "c": "center", "r": "right"}[aligns[ci]] if not hdr else "center"
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>' if (hdr and borders) else ""
            ps = "".join(para(runs(str(t), sz=sz, b=hdr or bold_row), jc=al, after=0, line=240) for t in str(cell).split("\n"))
            x += f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>{shd}<w:vAlign w:val="center"/></w:tcPr>{ps}</w:tc>'
        x += "</w:tr>"
    return x + "</w:tbl>"

def table_height(rows, widths, sz=22):
    h = 0.0
    for row in rows:
        h += max(sum(n_lines(l, w / 20 - 8, sz / 2) for l in str(c).split("\n")) for c, w in zip(row, widths)) * (sz / 2 * 1.15) + 5
    return h

# ---------------------------------------------------------------- Word-native headings, captions and fields
def plain(text):
    return f'<w:r><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

def hstyle(style, bm, text):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{bookmark(bm, plain(text))}</w:p>'

def pageref_plain(bm):
    return (f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGEREF {bm} \\h </w:instrText></w:r>'
            f'<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>@@{bm}@@</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>')

def caption_xml(word, chap, seq, n, cap, bm, above):
    rp = rpr(b=True, sz=24)
    seqf = (f'<w:r>{rp}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{rp}<w:instrText xml:space="preserve"> SEQ {seq} \\* ARABIC </w:instrText></w:r>'
            f'<w:r>{rp}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{rp}<w:t>{n}</w:t></w:r><w:r>{rp}<w:fldChar w:fldCharType="end"/></w:r>')
    inner = run(f"{word} {chap}.", b=True) + seqf + run(": ", b=True) + run(cap)
    return para(bookmark(bm, inner), style="Caption", jc="center", before=120 if above else 0, after=100 if above else 200, line=276, keep_next=above)

def toc_field(instr, entries, styles):
    """A real Word TOC field. entries: (text, bookmark, level). Word regenerates the content when fields are updated."""
    out = []
    for i, (text, bm, lvl) in enumerate(entries):
        pre = ""
        if i == 0:
            pre = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> %s </w:instrText></w:r>'
                   '<w:r><w:fldChar w:fldCharType="separate"/></w:r>' % instr)
        post = '<w:r><w:fldChar w:fldCharType="end"/></w:r>' if i == len(entries) - 1 else ""
        link = (f'<w:hyperlink w:anchor="{bm}" w:history="1"><w:r><w:t xml:space="preserve">{esc(text)}</w:t></w:r><w:r><w:tab/></w:r>{pageref_plain(bm)}</w:hyperlink>')
        out.append(f'<w:p><w:pPr><w:pStyle w:val="{styles[lvl]}"/></w:pPr>{pre}{link}{post}</w:p>')
    return out

# ---------------------------------------------------------------- body emission
media, rels = [], []
reg = {"heads": [], "figs": [], "tbls": []}
pages = {}          # bookmark -> estimated page text

def emit_body(blocks):
    out, fl = [], Flow(1)
    chap = "0"
    nfig = ntbl = 0
    n_ol = 0
    first_h1 = True
    for blk in blocks:
        k = blk[0]
        if k == "h1":
            chap, title = blk[1], blk[2]
            nfig = ntbl = 0
            bm = f"bm_ch{chap}"
            fl.newpage(); fl.add(24 * 2 + 40)
            pages[bm] = fl.page
            reg["heads"].append(("h1", chap, title, bm))
            out.append(f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>' + bookmark(bm, plain(f"CHAPTER {chap}") + "<w:r><w:br/></w:r>" + plain(title)) + "</w:p>")
        elif k == "h2":
            num, title, toc = blk[1], blk[2], blk[3]
            bm = "bm_h" + num.replace(".", "_")
            fl.add(12 + n_lines(f"{num} {title}", TWP, 12, "b") * 20.7 + 6)
            pages[bm] = fl.page
            reg["heads"].append(("h2", num, toc, bm))
            out.append(hstyle("Heading2", bm, f"{num} {toc}"))
        elif k == "h3":
            fl.add(6 + n_lines(f"{blk[1]} {blk[2]}", TWP, 12, "b") * 20.7 + 3)
            out.append(hstyle("Heading3", "bm_h3_" + blk[1].replace(".", "_"), f"{blk[1]} {blk[2]}"))
        elif k == "p":
            fl.add(n_lines(blk[1], TWP) * 20.7 + 6)
            out.append(para(runs(blk[1])))
        elif k in ("ul", "ol"):
            num = 90
            if k == "ol":
                n_ol += 1
                num = 100 + n_ol
            for it in blk[1]:
                fl.add(n_lines(it, TWP - 36) * 20.7 + 3)
                out.append(para(runs(it), after=60, num=num))
            out.append(para("", after=0, line=120))
        elif k == "tbl":
            ntbl += 1
            cap, header, rows, widths, aligns = blk[1:6]
            label = f"Table {chap}.{ntbl}"
            bm = f"bm_t{chap}_{ntbl}"
            fl.whole(27 + table_height([header] + rows, widths) + 10)
            pages[bm] = fl.page
            reg["tbls"].append((label, cap, bm, f"Tab{chap}"))
            out.append(caption_xml("Table", chap, f"Tab{chap}", ntbl, cap, bm, above=True))
            out.append(table_xml([header] + rows, widths, aligns))
            out.append(para("", after=120, line=240))
        elif k == "fig":
            nfig += 1
            fname, cap, wi, alt = blk[1:5]
            label = f"Figure {chap}.{nfig}"
            bm = f"bm_f{chap}_{nfig}"
            im = Image.open(FIG / fname)
            ratio = im.height / im.width
            cx, cy = int(wi * 914400), int(wi * ratio * 914400)
            rid = f"rId{200 + len(media)}"
            media.append((fname, rid))
            did = next_id()
            drawing = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
                       f'<wp:docPr id="{did}" name="Figure {chap}.{nfig}" descr="{esc(alt)}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                       f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="{did}" name="{fname}"/><pic:cNvPicPr/></pic:nvPicPr>'
                       f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                       '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
            fl.whole(wi * ratio * 72 + 12 + n_lines(f"{label}: {cap}", TWP) * 13.8 + 16)
            pages[bm] = fl.page
            reg["figs"].append((label, cap, bm, f"Fig{chap}"))
            out.append(para(drawing, jc="center", before=120, after=60, line=240, keep_next=True))
            out.append(caption_xml("Figure", chap, f"Fig{chap}", nfig, cap, bm, above=False))
        elif k == "figcap":
            nfig += 1
            label = f"Figure {chap}.{nfig}"
            bm = f"bm_f{chap}_{nfig}"
            fl.whole(30)
            pages[bm] = fl.page
            reg["figs"].append((label, blk[1], bm, f"Fig{chap}"))
            out.append(caption_xml("Figure", chap, f"Fig{chap}", nfig, blk[1], bm, above=False))
        elif k == "note":
            fl.add(n_lines(blk[1], TWP) * 20.7 + 6)
            out.append(para(run(blk[1], i=True, hl="yellow"), jc="center", before=120))
    return out, fl

def emit_back():
    out = []
    fl = Flow(0)
    # REFERENCES
    fl.page = pages["__after_ch5"]
    fl.newpage(); fl.add(60)
    pages["bm_refs"] = fl.page
    reg["heads"].append(("u", "", "REFERENCES", "bm_refs"))
    out.append(hstyle("Heading1", "bm_refs", "REFERENCES"))
    for n, r in enumerate(RC.REFERENCES, 1):
        fl.add(n_lines(f"[{n}] {r}", TWP - 28) * 16.1 + 4)
        out.append(para(run(f"[{n}]\t") + runs(r), after=80, line=276, left=567, hanging=567, tabs=[("left", 567)]))
    # APPENDIX
    fl.newpage(); fl.add(80)
    pages["bm_appx"] = fl.page
    reg["heads"].append(("u", "", "APPENDIX", "bm_appx"))
    reg["heads"].append(("a", "A", "CODING", "bm_appxa"))
    pages["bm_appxa"] = fl.page
    out.append(hstyle("Heading1", "bm_appx", "APPENDIX"))
    out.append(hstyle("Heading2", "bm_appxa", "A  Coding"))
    out.append(para(runs("The listings below are the main source files of the project. The complete code is in the project repository."), after=120))
    fl.add(60)
    for num, title, path in RC.CODE_FILES:
        lines = (ROOT / path).read_text(encoding="utf8").rstrip("\n").split("\n")
        fl.add(24)
        out.append(para(run(f"Listing {num}: {title}", b=True), jc="left", before=240, after=80, keep_next=True))
        for ln in lines:
            fl.add(max(1, math.ceil(len(ln.expandtabs(4)) / 76)) * 10.4)
            out.append(f'<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
                       f'<w:r><w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr>'
                       f'<w:t xml:space="preserve">{esc(ln.expandtabs(4)) if ln else " "}</w:t></w:r></w:p>')
    return out

# ---------------------------------------------------------------- front matter
def emit_front():
    out = []
    fl = Flow(5)
    pages["bm_abs"] = fl.page
    out.append(hstyle("Heading1", "bm_abs", "ABSTRACT"))
    fl.add(40)
    for t in RC.ABSTRACT:
        fl.add(n_lines(t, TWP) * 20.7 + 6)
        out.append(para(runs(t)))
    # ---- TABLE OF CONTENTS: a real Word TOC field built from Heading 1 and Heading 2
    fl.newpage(); pages["bm_toc"] = fl.page
    out.append(hstyle("Heading1", "bm_toc", "TABLE OF CONTENTS"))
    out.append(para(run("PAGE NO.", b=True), jc="right", after=60, line=276))
    fl.add(60)
    entries = [("ABSTRACT", "bm_abs", 1), ("TABLE OF CONTENTS", "bm_toc", 1), ("LIST OF FIGURES", "bm_lof", 1),
               ("LIST OF TABLES", "bm_lot", 1), ("ABBREVIATIONS", "bm_abbr", 1)]
    for kind, num, title, bm in reg["heads"]:
        if kind == "h1": entries.append((f"CHAPTER {num} {title}", bm, 1))
        elif kind == "h2": entries.append((f"{num} {title}", bm, 2))
        elif kind == "u": entries.append((title, bm, 1))
        elif kind == "a": entries.append((f"{num}  Coding", bm, 2))
    out += toc_field(r'TOC \o "1-2" \h \z', entries, {1: "TOC1", 2: "TOC2"})
    fl.add(19 * len(entries))
    # ---- LIST OF FIGURES / TABLES: real TOC fields over the numbered captions (SEQ fields)
    def listing(title, bm, items):
        fl.newpage(); pages[bm] = fl.page
        o = [hstyle("Heading1", bm, title), para(run("PAGE NO.", b=True), jc="right", after=60, line=276)]
        fl.add(60)
        groups = {}
        for label, cap, b_, seq in items:
            groups.setdefault(seq, []).append((f"{label}: {cap}", b_, 1))
            fl.add(n_lines(cap, TWP - 100) * 16.1 + 4)
        for seq, ents in groups.items():
            o += toc_field(r'TOC \h \z \c "%s"' % seq, ents, {1: "TableofFigures"})
        return o
    out += listing("LIST OF FIGURES", "bm_lof", reg["figs"])
    out += listing("LIST OF TABLES", "bm_lot", reg["tbls"])
    # ---- ABBREVIATIONS
    fl.newpage(); pages["bm_abbr"] = fl.page
    out.append(hstyle("Heading1", "bm_abbr", "ABBREVIATIONS"))
    rows = [["Abbreviation", "Full Form"]] + [[a_, b_] for a_, b_ in RC.ABBREVIATIONS]
    out.append(table_xml(rows, [2000, 6310], ["l", "l"], header=True, borders=False, sz=24))
    out.append('<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:sectPr>'
               '<w:footerReference w:type="default" r:id="rId10"/>'
               f'<w:pgSz w:w="{PG_W}" w:h="{PG_H}"/><w:pgMar w:top="{M_TOP}" w:right="{M_RIGHT}" w:bottom="{M_BOT}" w:left="{M_LEFT}" w:header="720" w:footer="720" w:gutter="0"/>'
               '<w:pgNumType w:fmt="lowerRoman" w:start="5"/><w:cols w:space="720"/></w:sectPr></w:pPr></w:p>')
    return out

# ---------------------------------------------------------------- assembling
def patch_styles(path):
    """Real Heading 1/2/3, TOC 1/2, Table of Figures and Caption styles; title-page headings keep their look under new names."""
    st = path.read_text(encoding="utf8")
    for n in (2, 3, 4):                                           # exact copies for the title page, not headings any more
        m = re.search(r'<w:style [^>]*w:styleId="Heading%d".*?</w:style>' % n, st, re.S)
        c = m.group(0).replace('w:styleId="Heading%d"' % n, 'w:styleId="TitleHeading%d"' % n)
        c = c.replace('<w:name w:val="heading %d"/>' % n, '<w:name w:val="Title Page Heading %d"/>' % n)
        c = re.sub(r"<w:outlineLvl [^>]*/>", "", c)
        c = re.sub(r"<w:link [^>]*/>", "", c)
        st = st.replace("</w:styles>", c + "</w:styles>")
    def put(sid, xml):
        nonlocal st
        pat = r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid
        if re.search(pat, st, re.S):
            st = re.sub(pat, lambda m: xml, st, count=1, flags=re.S)
        else:
            st = st.replace("</w:styles>", xml + "</w:styles>")
    tab = f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{TW}"/></w:tabs>'
    put("Heading1", '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:link w:val="Heading1Char"/><w:uiPriority w:val="9"/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:keepLines/><w:pageBreakBefore/><w:spacing w:before="0" w:after="240" w:line="360" w:lineRule="auto"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/></w:pPr>'
        '<w:rPr><w:b/><w:bCs/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>')
    put("Heading2", '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:unhideWhenUsed/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120" w:line="276" w:lineRule="auto"/><w:jc w:val="left"/><w:outlineLvl w:val="1"/></w:pPr>'
        '<w:rPr><w:b/><w:bCs/><w:caps/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>')
    put("Heading3", '<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:unhideWhenUsed/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="120" w:after="60" w:line="276" w:lineRule="auto"/><w:jc w:val="left"/><w:outlineLvl w:val="2"/></w:pPr>'
        '<w:rPr><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>')
    put("TOC1", '<w:style w:type="paragraph" w:styleId="TOC1"><w:name w:val="toc 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:autoRedefine/><w:uiPriority w:val="39"/><w:unhideWhenUsed/>'
        f'<w:pPr>{tab}<w:spacing w:before="60" w:after="60" w:line="276" w:lineRule="auto"/><w:ind w:right="560"/></w:pPr><w:rPr><w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>')
    put("TOC2", '<w:style w:type="paragraph" w:styleId="TOC2"><w:name w:val="toc 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:autoRedefine/><w:uiPriority w:val="39"/><w:unhideWhenUsed/>'
        f'<w:pPr>{tab}<w:spacing w:before="0" w:after="60" w:line="276" w:lineRule="auto"/><w:ind w:left="400" w:right="560"/></w:pPr><w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>')
    put("TableofFigures", '<w:style w:type="paragraph" w:styleId="TableofFigures"><w:name w:val="table of figures"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="99"/><w:unhideWhenUsed/>'
        f'<w:pPr>{tab}<w:spacing w:before="0" w:after="80" w:line="276" w:lineRule="auto"/><w:ind w:right="560"/></w:pPr><w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>')
    put("Caption", '<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="35"/><w:unhideWhenUsed/><w:qFormat/>'
        '<w:pPr><w:spacing w:before="0" w:after="200" w:line="276" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr><w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>')
    path.write_text(st, encoding="utf8")

def set_text(p, text, hl=None):
    runs_ = [r for r in p.findall(q("r")) if r.find(q("t")) is not None]
    first = runs_[0]
    for r in runs_[1:]:
        p.remove(r)
    first.find(q("t")).text = text
    first.find(q("t")).set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    rp = first.find(q("rPr"))
    h = rp.find(q("highlight")) if rp is not None else None
    if hl is None and h is not None:
        rp.remove(h)

def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    zipfile.ZipFile(TEMPLATE).extractall(BUILD)

    body_xml, fl = emit_body(RC.B)
    pages["__after_ch5"] = fl.page
    back_xml = emit_back()
    front_xml = emit_front()

    # ---- document.xml: keep the title page elements, replace everything after it
    tree = etree.parse(str(BUILD / "word/document.xml"))
    root = tree.getroot()
    body = root.find(q("body"))
    kids = list(body)
    title_page = kids[:32]                       # paragraphs 0..31 (31 carries the title-page section break)
    final_sect = kids[-1]
    assert final_sect.tag == q("sectPr")
    for el in kids[32:-1]:
        body.remove(el)

    for el in title_page:                                                          # title-page headings -> identical copies of the old styles
        ps = el.find(q("pPr") + "/" + q("pStyle"))
        if ps is not None and ps.get(q("val")) in ("Heading2", "Heading3", "Heading4"):
            ps.set(q("val"), "TitleHeading" + ps.get(q("val"))[-1])
    paras = [e for e in title_page]
    set_text(paras[0], RC.PRIMARY_TITLE)                                         # title: highlight removed
    set_text(paras[7], "ANANTHIKA GAJENDRAN [RA2311003011665]")                  # from the file's own author property
    set_text(paras[8], "[STUDENT NAME 2] [REGISTER NO. 2]", hl=True)
    set_text(paras[9], "[STUDENT NAME 3] [REGISTER NO. 3]", hl=True)
    set_text(paras[10], "[STUDENT NAME 4] [REGISTER NO. 4]", hl=True)
    # name 1 is a real entry: drop its highlight
    for r in paras[7].iter(q("rPr")):
        h = r.find(q("highlight"))
        if h is not None: r.remove(h)

    xml = "".join(front_xml + body_xml + back_xml)
    tokens = {}
    for bm, pg in pages.items():
        if bm.startswith("__"): continue
        tokens[bm] = roman(pg) if bm in ("bm_abs", "bm_toc", "bm_lof", "bm_lot", "bm_abbr") else str(pg)
    xml = re.sub(r"@@(\w+)@@", lambda m: tokens.get(m.group(1), "1"), xml)
    for child in etree.fromstring(f"<root {NS}>{xml}</root>"):
        body.append(child)
    # final (chapters) section
    for old in list(final_sect):
        final_sect.remove(old)
    for frag in etree.fromstring(
        f'<s {NS}><w:footerReference w:type="default" r:id="rId10"/><w:pgSz w:w="{PG_W}" w:h="{PG_H}"/>'
        f'<w:pgMar w:top="{M_TOP}" w:right="{M_RIGHT}" w:bottom="{M_BOT}" w:left="{M_LEFT}" w:header="720" w:footer="720" w:gutter="0"/>'
        '<w:pgNumType w:fmt="decimal" w:start="1"/><w:cols w:space="720"/></s>'):
        final_sect.append(frag)
    body.remove(final_sect); body.append(final_sect)
    tree.write(str(BUILD / "word/document.xml"), xml_declaration=True, encoding="UTF-8", standalone=True)

    patch_styles(BUILD / "word/styles.xml")

    # ---- footer with a PAGE field (format comes from each section's pgNumType)
    fpath = BUILD / "word/footer2.xml"
    f = fpath.read_text(encoding="utf8")
    page_p = ('<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
              '<w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
              '<w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:t>1</w:t></w:r>'
              '<w:r><w:rPr><w:sz w:val="24"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    f = re.sub(r"(<w:ftr[^>]*>).*(</w:ftr>)", lambda m: m.group(1) + page_p + m.group(2), f, flags=re.S)
    fpath.write_text(f, encoding="utf8")

    # ---- numbering: bullet and decimal lists
    npath = BUILD / "word/numbering.xml"
    nm = npath.read_text(encoding="utf8")
    def absnum(i, fmt, txt):
        return (f'<w:abstractNum w:abstractNumId="{i}"><w:multiLevelType w:val="hybridMultilevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/>'
                f'<w:numFmt w:val="{fmt}"/><w:lvlText w:val="{txt}"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
                '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:hint="default"/></w:rPr></w:lvl></w:abstractNum>')
    nums = '<w:num w:numId="90"><w:abstractNumId w:val="90"/></w:num>' + "".join(
        f'<w:num w:numId="{100 + k}"><w:abstractNumId w:val="91"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>' for k in range(1, 12))
    i = nm.index("<w:num ")
    nm = nm[:i] + absnum(90, "bullet", "•") + absnum(91, "decimal", "%1.") + nm[i:]
    nm = nm.replace("</w:numbering>", nums + "</w:numbering>")
    npath.write_text(nm, encoding="utf8")

    # ---- settings: refresh fields (page numbers) when the file is opened
    spath = BUILD / "word/settings.xml"
    st = spath.read_text(encoding="utf8")
    st = st.replace("<w:footnotePr>", '<w:updateFields w:val="true"/><w:footnotePr>', 1)
    spath.write_text(st, encoding="utf8")

    # ---- images, relationships, content types
    (BUILD / "word/media").mkdir(exist_ok=True)
    rtext = (BUILD / "word/_rels/document.xml.rels").read_text(encoding="utf8")
    add = ""
    for fname, rid in media:
        shutil.copy(FIG / fname, BUILD / "word/media" / fname)
        add += f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fname}"/>'
    (BUILD / "word/_rels/document.xml.rels").write_text(rtext.replace("</Relationships>", add + "</Relationships>"), encoding="utf8")
    ct = (BUILD / "[Content_Types].xml").read_text(encoding="utf8")
    if 'Extension="png"' not in ct:
        ct = ct.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1)
    (BUILD / "[Content_Types].xml").write_text(ct, encoding="utf8")

    # ---- document properties
    cpath = BUILD / "docProps/core.xml"
    cp = cpath.read_text(encoding="utf8")
    cp = cp.replace("<dc:creator>", f"<dc:title>{esc(RC.PRIMARY_TITLE)}</dc:title><dc:creator>", 1)
    cpath.write_text(cp, encoding="utf8")

    # ---- zip ([Content_Types].xml first, no folder entries)
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(BUILD / "[Content_Types].xml", "[Content_Types].xml")
        for p in sorted(BUILD.rglob("*")):
            if p.is_file() and p.name != "[Content_Types].xml":
                z.write(p, str(p.relative_to(BUILD)))
    print("Wrote", OUT, f"({OUT.stat().st_size / 1e6:.1f} MB)")
    print("Figures:", len(reg["figs"]), "| Tables:", len(reg["tbls"]), "| body pages (estimate):", pages["__after_ch5"], "+ refs/appendix")
    print("Estimated last page:", max(v for k, v in pages.items() if not k.startswith("bm_ch") and not k.startswith("__") and not k.startswith("bm_abs")))

if __name__ == "__main__":
    main()
