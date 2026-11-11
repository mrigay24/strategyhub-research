"""
Convert the paper's Markdown subset to .docx (python-docx), embedding figures.

Handles: # / ## / ### headings, paragraphs, "- " bullets (with indented continuation),
pipe tables, ![caption](path) images, ---, **bold**, *italic*, `code`.
Image paths are resolved relative to the Markdown file.

Run:  ~/.venvs/strategyhub/bin/python scripts/md_to_docx.py docs/entropy_research/PAPER_DRAFT.md
      (writes PAPER_DRAFT.docx next to it; pass a second path to choose the output)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|(?<![\w*])\*(?!\s)[^*]+?\*(?![\w*]))")
INK2 = RGBColor(0x52, 0x51, 0x4E)


def add_inline(par, text: str, size: float | None = None, bold: bool = False, italic: bool = False):
    text = text.replace("\\|", "|")
    for part in TOKEN.split(text):
        if not part:
            continue
        b, i, code = bold, italic, False
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            add_inline(par, part[2:-2], size, True, italic)
            continue
        if part.startswith("`") and part.endswith("`"):
            part, code = part[1:-1], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            add_inline(par, part[1:-1], size, bold, True)
            continue
        r = par.add_run(part)
        r.bold, r.italic = b or None, i or None
        if code:
            r.font.name = "Menlo"
            r.font.size = Pt((size or 10.5) - 1.5)
        elif size:
            r.font.size = Pt(size)


def shade(cell, hexcolor: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def add_table(doc, rows: list[str]) -> None:
    cells = [[c.strip() for c in re.split(r"(?<!\\)\|", r.strip())[1:-1]] for r in rows]
    header, body = cells[0], [c for c in cells[2:]]
    ncol = len(header)
    t = doc.add_table(rows=1 + len(body), cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    size = 8 if ncol >= 7 else 8.5
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]
        c.paragraphs[0].text = ""
        add_inline(c.paragraphs[0], h, size, bold=True)
        shade(c, "EFEEEA")
    for i, r in enumerate(body, start=1):
        for j in range(ncol):
            c = t.rows[i].cells[j]
            add_inline(c.paragraphs[0], r[j] if j < len(r) else "", size)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.space_before = Pt(0)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def convert(md: Path, out: Path) -> None:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Inches(1))
    st = doc.styles
    st["Normal"].font.name = "Calibri"
    st["Normal"].font.size = Pt(10.5)
    st["Normal"].paragraph_format.space_after = Pt(6)
    st["Normal"].paragraph_format.line_spacing = 1.1
    for name, size in [("Title", 17), ("Heading 1", 13.5), ("Heading 2", 11.5)]:
        s = st[name]
        s.font.name, s.font.size, s.font.bold = "Calibri", Pt(size), True
        s.font.color.rgb = RGBColor(0x0B, 0x0B, 0x0B)
        s.paragraph_format.keep_with_next = True
        s.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        s.paragraph_format.space_after = Pt(4)

    lines = md.read_text().splitlines()
    i, buf = 0, []

    def flush():
        if buf:
            p = doc.add_paragraph()
            txt = " ".join(x.strip() for x in buf)
            caption = txt.startswith("*") and txt.endswith("*") and not txt.startswith("**")
            add_inline(p, txt, 9 if caption else None)
            if caption:
                for r in p.runs:
                    r.font.color.rgb = INK2
            buf.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith("<!--"):
            i += 1; continue
        if s == "---":
            flush(); i += 1; continue
        m = re.match(r"^(#{1,3}) (.*)", s)
        if m:
            flush()
            lvl = len(m.group(1))
            if lvl == 1:
                doc.add_paragraph(m.group(2), style="Title")
            else:
                h = doc.add_paragraph(style=f"Heading {lvl - 1}")
                add_inline(h, m.group(2))
            i += 1; continue
        m = re.match(r"^!\[(.*?)\]\((.*?)\)", s)
        if m:
            flush()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            p.add_run().add_picture(str((md.parent / m.group(2)).resolve()), width=Inches(6.3))
            i += 1; continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i]); i += 1
            add_table(doc, rows)
            continue
        if s.startswith("- "):
            flush()
            item = [s[2:]]
            i += 1
            while i < len(lines) and lines[i].startswith("  ") and not lines[i].strip().startswith("- ") \
                    and lines[i].strip():
                item.append(lines[i].strip()); i += 1
            indent = len(ln) - len(ln.lstrip())
            p = doc.add_paragraph(style="List Bullet 2" if indent >= 2 else "List Bullet")
            p.paragraph_format.space_after = Pt(2)
            add_inline(p, " ".join(item))
            continue
        buf.append(ln)
        i += 1
    flush()
    doc.save(out)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".docx")
    convert(src, dst)
    print(f"wrote {dst}")
