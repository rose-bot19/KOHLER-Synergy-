from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT / "prompts"
OUTPUT = ROOT / "KOHLER_Synergy_Prompts.pdf"

prompt_files = [
    "system_prompt.txt",
    "intent_router.txt",
    "response_strategy.txt",
    "manager.txt",
    "worker.txt",
    "synthesizer.txt",
    "verification.txt",
    "document_classifier.txt",
    "memory_extraction.txt",
    "response_formatter.txt",
]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="TitleCenter",
    parent=styles["Title"],
    alignment=TA_CENTER,
    spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="PromptHeading",
    parent=styles["Heading1"],
    spaceBefore=6,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="PromptBody",
    parent=styles["BodyText"],
    fontName="Courier",
    fontSize=7.4,
    leading=9.5,
    spaceAfter=3,
))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(
        A4[0] - 18 * mm,
        10 * mm,
        f"KOHLER Synergy | Page {doc.page}"
    )
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=15 * mm,
    leftMargin=15 * mm,
    topMargin=15 * mm,
    bottomMargin=16 * mm,
)

story = [
    Paragraph("KOHLER Synergy - Prompt & Workflow Documentation", styles["TitleCenter"]),
    Paragraph(
        "This document is generated directly from the repository's prompt files. "
        "The modular prompt architecture separates core behavior, intent routing, response strategy, "
        "orchestration, verification, document classification, memory and output formatting.",
        styles["BodyText"],
    ),
    Spacer(1, 8),
    Paragraph("Workflow overview", styles["Heading1"]),
    Paragraph(
        "User request -> intent understanding -> retrieval/tool selection -> action policy -> execution/approval "
        "-> evidence verification -> adaptive response -> selective memory.",
        styles["BodyText"],
    ),
    Spacer(1, 10),
]

for index, filename in enumerate(prompt_files):
    path = PROMPTS_DIR / filename
    story.append(Paragraph(filename, styles["PromptHeading"]))

    if path.exists():
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip() == "":
                story.append(Spacer(1, 2))
            else:
                story.append(Paragraph(escape(line), styles["PromptBody"]))
    else:
        story.append(Paragraph("[Prompt file not found in the repository at generation time.]", styles["BodyText"]))

    if index != len(prompt_files) - 1:
        story.append(PageBreak())


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"Created: {OUTPUT}")
