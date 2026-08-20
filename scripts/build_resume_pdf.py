#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    PageBreak,
)


def md_inline_to_rl(text: str) -> str:
    # Minimal Markdown -> ReportLab inline markup.
    # Bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Collapse double spaces used for MD hard-breaks.
    text = text.replace("  ", " ")
    return text.strip()


def build_story(md: str):
    styles = getSampleStyleSheet()

    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=12.5,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )
    h3 = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        spaceBefore=8,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
        spaceAfter=4,
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        spaceAfter=3,
    )

    story = []
    bullet_buf: list[str] = []
    para_buf: list[str] = []

    def flush_paragraph(style=body):
        nonlocal para_buf
        if not para_buf:
            return
        text = "<br/>".join(md_inline_to_rl(x) for x in para_buf if x.strip())
        if text:
            story.append(Paragraph(text, style))
        para_buf = []

    def flush_bullets():
        nonlocal bullet_buf
        if not bullet_buf:
            return
        items = []
        for b in bullet_buf:
            items.append(ListItem(Paragraph(md_inline_to_rl(b), body), leftIndent=10))
        story.append(
            ListFlowable(
                items,
                bulletType="bullet",
                start="bullet",
                leftIndent=14,
                bulletFontSize=8,
                bulletOffsetY=1,
            )
        )
        bullet_buf = []

    for raw in md.splitlines():
        line = raw.rstrip("\n")

        if line.strip() == "":
            flush_bullets()
            flush_paragraph()
            story.append(Spacer(1, 6))
            continue

        if line.strip() == "---":
            flush_bullets()
            flush_paragraph()
            story.append(PageBreak())
            continue

        if line.startswith("## "):
            flush_bullets()
            flush_paragraph()
            story.append(Paragraph(md_inline_to_rl(line[3:]), h2))
            continue

        if line.startswith("### "):
            flush_bullets()
            flush_paragraph()
            story.append(Paragraph(md_inline_to_rl(line[4:]), h3))
            continue

        if line.startswith("# "):
            flush_bullets()
            flush_paragraph()
            story.append(Paragraph(md_inline_to_rl(line[2:]), h1))
            continue

        if line.startswith("- "):
            flush_paragraph()
            bullet_buf.append(line[2:])
            continue

        # Default: paragraph text (support manual line breaks)
        flush_bullets()
        para_buf.append(line)

    flush_bullets()
    flush_paragraph(small if len(" ".join(para_buf)) < 40 else body)
    return story


def main():
    if len(sys.argv) < 3:
        print("Usage: build_resume_pdf.py <input.md> <output.pdf>", file=sys.stderr)
        raise SystemExit(2)

    md_path = Path(sys.argv[1]).expanduser().resolve()
    out_path = Path(sys.argv[2]).expanduser().resolve()

    md = md_path.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Currículo - Henrique dos Reis Rocha",
        author="Henrique dos Reis Rocha",
    )
    story = build_story(md)
    doc.build(story)


if __name__ == "__main__":
    main()

