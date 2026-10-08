"""Assemble a locked Book Genesis manuscript and export validated book formats.

This is deliberately a small library with a thin command line wrapper.  It
does not score, proofread, or revise a book.  It assembles the canonical
chapter files and produces delivery artifacts after the host has decided that
the manuscript is ready for production. Optional DOCX/PDF proof dependencies
are imported only when requested.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import tempfile
import unicodedata
import uuid
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


class ExportError(ValueError):
    """Raised when the source manuscript or delivery target is unsafe."""


@dataclass(frozen=True)
class Chapter:
    number: int
    path: Path
    title: str
    body: str
    sha256: str


@dataclass(frozen=True)
class BookMetadata:
    title: str
    author: str
    language: str
    slug: str


_CHAPTER_RE = re.compile(r"^chapter-(\d+)\.md$", re.IGNORECASE)
_SCENE_BREAKS = {"* * *", "***", "---", "— — —"}
_CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
_OPF_NS = "http://www.idpf.org/2007/opf"
_DC_NS = "http://purl.org/dc/elements/1.1/"
_EPUB_NS = "http://www.idpf.org/2007/ops"
_XHTML_NS = "http://www.w3.org/1999/xhtml"
_XML_INVALID_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_WINDOWS_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
_COMPLETE_PIPELINE_FILES = [
    *(f"artifacts/{number:02d}-{name}.md" for number, name in [
        (0, "brief"),
        (1, "market-map"),
        (2, "story-engine"),
        (3, "characters"),
        (4, "theme"),
        (5, "voice"),
        (6, "emotional-curve"),
        (7, "outline"),
        (8, "opening-strategy"),
        (9, "continuity-ledger"),
        (10, "adversarial-audit"),
        (11, "genesis-score"),
        (12, "editorial-package"),
        (13, "positioning"),
    ]),
    "ASSUMPTIONS.md",
    "RUN_REPORT.md",
    "PROJECT_STATE.yaml",
    "evaluations/panel-chapter-01.md",
    "evaluations/proofread.md",
    "evaluations/revision-loop.md",
    "evaluations/revision-plan.md",
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower()).strip("-")
    if not slug:
        raise ExportError("title does not produce a usable delivery slug")
    return slug


def _validate_slug(value: str) -> str:
    """Accept only a simple delivery filename component.

    The slug is interpolated into several staged output filenames.  Keeping it
    to a small ASCII filename grammar prevents an API caller from redirecting
    an artifact through a separator, dot segment, or Windows device name.
    """

    if (
        not value
        or len(value) > 80
        or value in {".", ".."}
        or Path(value).name != value
        or Path(value).is_absolute()
        or "/" in value
        or "\\" in value
        or not _SAFE_SLUG_RE.fullmatch(value)
        or value.casefold() in _WINDOWS_RESERVED_NAMES
    ):
        raise ExportError("slug must be a simple lowercase filename component")
    return value


def _normalise_language(value: str) -> str:
    language = value.strip().replace("_", "-")
    if not language:
        raise ExportError("language is required")
    aliases = {"en": "en-US", "pt": "pt-BR", "es": "es-ES"}
    return aliases.get(language.lower(), language)


def _require_metadata(title: str, author: str, language: str, slug: str | None) -> BookMetadata:
    title = title.strip()
    author = author.strip()
    if not title:
        raise ExportError("title is required")
    if not author:
        raise ExportError("author is required; do not invent one")
    safe_slug = _validate_slug(slug) if slug is not None else _validate_slug(_slugify(title))
    return BookMetadata(title, author, _normalise_language(language), safe_slug)


def discover_chapters(chapters_dir: str | Path) -> list[Chapter]:
    """Read canonical ``chapter-NN.md`` files and reject unsafe numbering."""

    root = Path(chapters_dir)
    if not root.is_dir():
        raise ExportError(f"chapter directory does not exist: {root}")
    files = sorted(root.glob("*.md"), key=lambda path: path.name.casefold())
    if not files:
        raise ExportError(f"no chapter files found in {root}")

    parsed: dict[int, Path] = {}
    for path in files:
        match = _CHAPTER_RE.fullmatch(path.name)
        if not match:
            raise ExportError(f"non-canonical markdown file in chapter directory: {path.name}")
        number = int(match.group(1))
        if number in parsed:
            raise ExportError(f"duplicate chapter number {number}: {parsed[number].name} and {path.name}")
        parsed[number] = path

    numbers = sorted(parsed)
    expected = list(range(1, numbers[-1] + 1))
    if numbers != expected:
        missing = sorted(set(expected) - set(numbers))
        raise ExportError(f"chapter numbering has gaps; missing: {', '.join(f'{n:02d}' for n in missing)}")

    chapters: list[Chapter] = []
    for number in numbers:
        path = parsed[number]
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        if _XML_INVALID_RE.search(text):
            raise ExportError(f"{path.name} contains XML-invalid control characters")
        lines = text.splitlines()
        if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
            raise ExportError(f"{path.name} must start with one level-1 heading")
        if any(line.startswith("# ") for line in lines[1:]):
            raise ExportError(f"{path.name} contains more than one level-1 heading")
        title = lines[0][2:].strip()
        body = "\n".join(lines[1:]).strip()
        if not body:
            raise ExportError(f"{path.name} has no prose after its heading")
        chapters.append(Chapter(number, path, title, body + "\n", _sha256_bytes(raw)))
    return chapters


def _inline_xhtml(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", value)
    value = re.sub(r"(?<![\w])_([^_\n]+?)_(?![\w])", r"<em>\1</em>", value)
    return value


def markdown_body_to_xhtml(body: str) -> str:
    """Convert the small Markdown subset used by chapters to book XHTML."""

    blocks: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            text = " ".join(line.strip() for line in paragraph).strip()
            if text:
                blocks.append(f"<p>{_inline_xhtml(text)}</p>")
            paragraph.clear()

    for line in body.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
        elif stripped in _SCENE_BREAKS:
            flush()
            blocks.append('<hr class="scene-break" />')
        else:
            paragraph.append(line)
    flush()
    return "\n".join(blocks)


def _markdown_blocks(body: str) -> list[tuple[str, str]]:
    """Return prose blocks and scene breaks from the supported Markdown subset."""

    blocks: list[tuple[str, str]] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            text = " ".join(line.strip() for line in paragraph).strip()
            if text:
                blocks.append(("paragraph", text))
            paragraph.clear()

    for line in body.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
        elif stripped in _SCENE_BREAKS:
            flush()
            blocks.append(("scene", "* * *"))
        else:
            paragraph.append(line)
    flush()
    return blocks


_INLINE_RE = re.compile(
    r"\*\*(.+?)\*\*|(?<!\*)\*([^*\n]+?)\*(?!\*)|(?<![\w])_([^_\n]+?)_(?![\w])"
)


def _inline_spans(text: str) -> list[tuple[str, str]]:
    """Tokenize bold and italic spans without changing prose text."""

    spans: list[tuple[str, str]] = []
    cursor = 0
    for match in _INLINE_RE.finditer(text):
        if match.start() > cursor:
            spans.append(("plain", text[cursor:match.start()]))
        if match.group(1) is not None:
            spans.append(("bold", match.group(1)))
        else:
            spans.append(("italic", match.group(2) or match.group(3) or ""))
        cursor = match.end()
    if cursor < len(text):
        spans.append(("plain", text[cursor:]))
    return spans


def _write_docx(path: Path, chapters: list[Chapter], metadata: BookMetadata) -> None:
    """Write a reader-proof DOCX using the installed python-docx package."""

    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches, Pt
    except ImportError as exc:
        raise ExportError("DOCX requested but python-docx is not installed") from exc

    document = Document()
    section = document.sections[0]
    section.page_width = Inches(5.5)
    section.page_height = Inches(8.5)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    normal = document.styles["Normal"]
    normal.font.name = "Georgia"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Georgia")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    title_style = document.styles["Title"]
    title_style.font.name = "Georgia"
    title_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Georgia")
    title_style.font.size = Pt(24)
    title_style.font.bold = True
    heading = document.styles["Heading 1"]
    heading.font.name = "Georgia"
    heading._element.rPr.rFonts.set(qn("w:eastAsia"), "Georgia")
    heading.font.size = Pt(18)
    heading.font.bold = True

    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(180)
    title.add_run(metadata.title)
    author = document.add_paragraph()
    author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author.paragraph_format.space_before = Pt(18)
    author.add_run(metadata.author)
    document.add_page_break()

    for chapter_index, chapter in enumerate(chapters):
        heading_paragraph = document.add_paragraph(style="Heading 1")
        heading_paragraph.paragraph_format.page_break_before = chapter_index > 0
        heading_paragraph.add_run(chapter.title)
        for kind, text in _markdown_blocks(chapter.body):
            if kind == "scene":
                scene = document.add_paragraph()
                scene.alignment = WD_ALIGN_PARAGRAPH.CENTER
                scene.paragraph_format.space_before = Pt(8)
                scene.paragraph_format.space_after = Pt(8)
                scene.add_run(text)
                continue
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.first_line_indent = Inches(0.25)
            for span_kind, value in _inline_spans(text):
                run = paragraph.add_run(value)
                run.bold = span_kind == "bold"
                run.italic = span_kind == "italic"

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run()
    run.font.name = "Georgia"
    run.font.size = Pt(9)
    run._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Georgia")
    run.add_text("Page ")
    field_begin = OxmlElement("w:fldChar")
    field_begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    field_end = OxmlElement("w:fldChar")
    field_end.set(qn("w:fldCharType"), "end")
    run._r.append(field_begin)
    run._r.append(instruction)
    run._r.append(field_end)
    path.parent.mkdir(parents=True, exist_ok=True)
    document.core_properties.title = metadata.title
    document.core_properties.author = metadata.author
    document.save(path)


def _prose_tokens(text: str) -> list[str]:
    """Normalize prose for fidelity checks while tolerating layout artifacts."""

    text = re.sub(r"\*\*|[*_]", "", text)
    text = "\n".join(line for line in text.splitlines() if line.strip() not in _SCENE_BREAKS)
    return re.findall(r"[\w]+", text.casefold(), flags=re.UNICODE)


def _contains_in_order(actual: list[str], expected: list[str]) -> bool:
    if not expected:
        return True
    expected_index = 0
    for token in actual:
        if token == expected[expected_index]:
            expected_index += 1
            if expected_index == len(expected):
                return True
    return False


def _expected_prose_tokens(chapters: list[Chapter]) -> list[str]:
    expected: list[str] = []
    for chapter in chapters:
        expected.extend(_prose_tokens(chapter.title))
        expected.extend(_prose_tokens(chapter.body))
    return expected


def validate_docx(path: Path, expected_chapters: int | list[Chapter]) -> dict[str, int | str]:
    """Reopen the DOCX and verify its chapter headings and nonempty package."""

    try:
        from docx import Document
    except ImportError as exc:
        raise ExportError("DOCX requested but python-docx is not installed") from exc
    try:
        document = Document(path)
        headings = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.style.name == "Heading 1"
        ]
    except Exception as exc:
        raise ExportError(f"invalid DOCX: {exc}") from exc
    chapters = expected_chapters if isinstance(expected_chapters, list) else None
    chapter_count = len(chapters) if chapters is not None else expected_chapters
    if len(headings) != chapter_count:
        raise ExportError(f"DOCX has {len(headings)} chapter headings; expected {chapter_count}")
    if not any(paragraph.text.strip() for paragraph in document.paragraphs):
        raise ExportError("DOCX contains no readable text")
    if chapters is not None:
        actual = _prose_tokens("\n".join(paragraph.text for paragraph in document.paragraphs))
        if not _contains_in_order(actual, _expected_prose_tokens(chapters)):
            raise ExportError("DOCX text does not preserve the complete source chapter stream")
    return {"chapters": len(headings), "status": "passed"}


def _find_serif_font() -> tuple[str, str, str, str, str, str, str, str]:
    candidates = [
        (
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "georgia.ttf",
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "georgiab.ttf",
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "georgiai.ttf",
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "georgiaz.ttf",
            "BookGenesisGeorgia", "BookGenesisGeorgia-Bold", "BookGenesisGeorgia-Italic", "BookGenesisGeorgia-BoldItalic",
        ),
        (
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "times.ttf",
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "timesbd.ttf",
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "timesi.ttf",
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "timesbi.ttf",
            "BookGenesisTimes", "BookGenesisTimes-Bold", "BookGenesisTimes-Italic", "BookGenesisTimes-BoldItalic",
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"),
            "BookGenesisSerif", "BookGenesisSerif-Bold", "BookGenesisSerif-Italic", "BookGenesisSerif-BoldItalic",
        ),
        (
            Path("/System/Library/Fonts/Times New Roman.ttf"),
            Path("/System/Library/Fonts/Times New Roman Bold.ttf"),
            Path("/System/Library/Fonts/Times New Roman Italic.ttf"),
            Path("/System/Library/Fonts/Times New Roman Bold Italic.ttf"),
            "BookGenesisTimes", "BookGenesisTimes-Bold", "BookGenesisTimes-Italic", "BookGenesisTimes-BoldItalic",
        ),
    ]
    for path, bold_path, italic_path, bold_italic_path, regular_name, bold_name, italic_name, bold_italic_name in candidates:
        if path.is_file():
            paths_and_names = (
                (bold_path, bold_name), (italic_path, italic_name), (bold_italic_path, bold_italic_name),
            )
            resolved = [
                (str(variant_path), variant_name if variant_path.is_file() else regular_name)
                for variant_path, variant_name in paths_and_names
            ]
            return (str(path), resolved[0][0], resolved[1][0], resolved[2][0], regular_name, resolved[0][1], resolved[1][1], resolved[2][1])
    raise ExportError("PDF requested but no accessible serif TrueType font was found")


def _write_pdf(path: Path, chapters: list[Chapter], metadata: BookMetadata) -> None:
    """Write a 5.5 x 8.5 inch reading proof PDF with a registered serif font."""

    try:
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch as inch_unit
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise ExportError("PDF requested but reportlab is not installed") from exc

    font_path, bold_font_path, italic_font_path, bold_italic_font_path, regular_name, bold_name, italic_name, bold_italic_name = _find_serif_font()
    try:
        pdfmetrics.registerFont(TTFont(regular_name, font_path))
        if bold_name != regular_name:
            pdfmetrics.registerFont(TTFont(bold_name, bold_font_path))
        if italic_name != regular_name:
            pdfmetrics.registerFont(TTFont(italic_name, italic_font_path))
        if bold_italic_name != regular_name:
            pdfmetrics.registerFont(TTFont(bold_italic_name, bold_italic_font_path))
        pdfmetrics.registerFontFamily(regular_name, normal=regular_name, bold=bold_name, italic=italic_name, boldItalic=bold_italic_name)
    except Exception as exc:
        raise ExportError(f"PDF requested but the serif font could not be embedded: {exc}") from exc

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "BookBody", parent=styles["BodyText"], fontName=regular_name, fontSize=10.5,
        leading=14, firstLineIndent=18, spaceAfter=6, alignment=0,
    )
    scene_style = ParagraphStyle(
        "BookScene", parent=body_style, firstLineIndent=0, alignment=TA_CENTER,
        spaceBefore=8, spaceAfter=8,
    )
    chapter_style = ParagraphStyle(
        "BookChapter", parent=styles["Heading1"], fontName=regular_name,
        fontSize=17, leading=21, spaceAfter=20, pageBreakBefore=False,
    )
    title_style = ParagraphStyle(
        "BookTitle", parent=styles["Title"], fontName=regular_name,
        fontSize=23, leading=28, alignment=TA_CENTER, spaceAfter=18,
    )
    author_style = ParagraphStyle(
        "BookAuthor", parent=body_style, firstLineIndent=0, alignment=TA_CENTER,
    )

    def page_number(canvas, document) -> None:
        canvas.saveState()
        canvas.setFont(regular_name, 8.5)
        canvas.drawCentredString(2.75 * inch_unit, 0.4 * inch_unit, f"{document.page}")
        canvas.restoreState()

    story = [Spacer(1, 2.15 * inch_unit), Paragraph(html.escape(metadata.title), title_style), Paragraph(html.escape(metadata.author), author_style), PageBreak()]
    for chapter_index, chapter in enumerate(chapters):
        if chapter_index:
            story.append(PageBreak())
        story.append(Paragraph(html.escape(chapter.title), chapter_style))
        for kind, text in _markdown_blocks(chapter.body):
            if kind == "scene":
                story.append(Paragraph("* * *", scene_style))
            else:
                story.append(Paragraph(_inline_xhtml(text), body_style))

    path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(path), pagesize=(5.5 * inch_unit, 8.5 * inch_unit),
        leftMargin=0.8 * inch_unit, rightMargin=0.8 * inch_unit,
        topMargin=0.7 * inch_unit, bottomMargin=0.65 * inch_unit,
        title=metadata.title, author=metadata.author,
    )
    document.build(story, onFirstPage=page_number, onLaterPages=page_number)


def validate_pdf(path: Path, expected_chapters: int | list[Chapter]) -> dict[str, int | str]:
    """Reopen the reading proof and confirm pages and chapter text are present."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExportError("PDF requested but pypdf is not installed for validation") from exc
    try:
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise ExportError(f"invalid PDF: {exc}") from exc
    chapters = expected_chapters if isinstance(expected_chapters, list) else None
    chapter_count = len(chapters) if chapters is not None else expected_chapters
    if len(reader.pages) < chapter_count + 1:
        raise ExportError(f"PDF has {len(reader.pages)} pages; expected at least {chapter_count + 1}")
    actual_tokens = _prose_tokens(text)
    if not actual_tokens:
        raise ExportError("PDF contains no readable prose")
    if chapters is not None and not _contains_in_order(actual_tokens, _expected_prose_tokens(chapters)):
        raise ExportError("PDF text does not preserve the complete source chapter stream")
    return {"chapters": chapter_count, "pages": len(reader.pages), "text_bytes": len(text.encode("utf-8")), "status": "passed"}


def assemble_manuscript(chapters: Iterable[Chapter], metadata: BookMetadata) -> str:
    """Create the canonical plain Markdown delivery manuscript."""

    chapter_list = list(chapters)
    lines = [
        "---",
        f"title: {json.dumps(metadata.title, ensure_ascii=False)}",
        f"author: {json.dumps(metadata.author, ensure_ascii=False)}",
        f"lang: {metadata.language}",
        "---",
        "",
    ]
    for index, chapter in enumerate(chapter_list):
        if index:
            lines.append("")
        lines.extend([f"# {chapter.title}", "", chapter.body.rstrip()])
    return "\n".join(lines) + "\n"


def count_prose_words(chapter: Chapter) -> int:
    """Count source prose deterministically for the export receipt.

    The count excludes the chapter's level-one heading, frontmatter (which is
    not part of ``Chapter.body``), blank lines, and standalone scene/formatting
    separator lines. Every other line is split on whitespace; Markdown markers
    and punctuation remain attached to their surrounding token.
    """

    count = 0
    for line in chapter.body.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        stripped = line.strip()
        if not stripped or stripped in _SCENE_BREAKS or stripped.startswith("# "):
            continue
        count += len(stripped.split())
    return count


def word_count_receipt(chapters: list[Chapter]) -> dict[str, object]:
    per_chapter = [
        {"number": chapter.number, "words": count_prose_words(chapter)}
        for chapter in chapters
    ]
    return {
        "method": "whitespace_split_prose_v1",
        "excludes": ["level-one headings", "frontmatter", "blank lines", "standalone scene/formatting separators"],
        "chapters": per_chapter,
        "total": sum(item["words"] for item in per_chapter),
    }


def _complete_pipeline_preflight(
    book_root: Path,
    chapters: list[Chapter],
    *,
    expected_chapters: int | None,
    min_words: int | None,
    max_words: int | None,
) -> None:
    """Require saved pipeline evidence before a host labels delivery complete."""

    missing = []
    for relative in _COMPLETE_PIPELINE_FILES:
        path = book_root / relative
        try:
            present = path.is_file() and bool(path.read_text(encoding="utf-8-sig").strip())
        except (OSError, UnicodeError):
            present = False
        if not present:
            missing.append(relative)
    if missing:
        raise ExportError("complete pipeline preflight missing or empty evidence: " + ", ".join(missing))
    _assert_count_contract(
        chapters,
        expected_chapters=expected_chapters,
        min_words=min_words,
        max_words=max_words,
    )


def _assert_count_contract(
    chapters: list[Chapter],
    *,
    expected_chapters: int | None,
    min_words: int | None,
    max_words: int | None,
) -> None:
    actual_chapters = len(chapters)
    if expected_chapters is not None and actual_chapters != expected_chapters:
        raise ExportError(
            f"complete pipeline preflight expected {expected_chapters} chapters but found {actual_chapters}"
        )
    counts = word_count_receipt(chapters)
    total_words = int(counts["total"])
    if min_words is not None and total_words < min_words:
        raise ExportError(
            f"complete pipeline preflight word count {total_words} is below min_words {min_words}"
        )
    if max_words is not None and total_words > max_words:
        raise ExportError(
            f"complete pipeline preflight word count {total_words} is above max_words {max_words}"
        )


def _xhtml_page(title: str, content: str, language: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<html xmlns="{_XHTML_NS}" lang="{html.escape(language)}" xml:lang="{html.escape(language)}">\n'
        "<head><meta charset=\"utf-8\" /><title>"
        f"{html.escape(title)}"
        "</title><link rel=\"stylesheet\" type=\"text/css\" href=\"../styles.css\" /></head>\n"
        f"<body><h1>{html.escape(title)}</h1>\n{content}\n</body></html>\n"
    )


def _opf_xml(metadata: BookMetadata, chapters: list[Chapter], modified: str) -> bytes:
    ET.register_namespace("", _OPF_NS)
    ET.register_namespace("dc", _DC_NS)
    package = ET.Element(f"{{{_OPF_NS}}}package", {"version": "3.0", "unique-identifier": "book-id"})
    metadata_node = ET.SubElement(package, f"{{{_OPF_NS}}}metadata")
    ET.SubElement(metadata_node, f"{{{_DC_NS}}}identifier", {"id": "book-id"}).text = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, metadata.slug)}"
    ET.SubElement(metadata_node, f"{{{_DC_NS}}}title").text = metadata.title
    ET.SubElement(metadata_node, f"{{{_DC_NS}}}creator").text = metadata.author
    ET.SubElement(metadata_node, f"{{{_DC_NS}}}language").text = metadata.language
    ET.SubElement(metadata_node, f"{{{_OPF_NS}}}meta", {"property": "dcterms:modified"}).text = modified
    manifest = ET.SubElement(package, f"{{{_OPF_NS}}}manifest")
    ET.SubElement(manifest, f"{{{_OPF_NS}}}item", {"id": "nav", "href": "nav.xhtml", "media-type": "application/xhtml+xml", "properties": "nav"})
    ET.SubElement(manifest, f"{{{_OPF_NS}}}item", {"id": "css", "href": "styles.css", "media-type": "text/css"})
    ET.SubElement(manifest, f"{{{_OPF_NS}}}item", {"id": "title-page", "href": "titlepage.xhtml", "media-type": "application/xhtml+xml"})
    spine = ET.SubElement(package, f"{{{_OPF_NS}}}spine")
    ET.SubElement(spine, f"{{{_OPF_NS}}}itemref", {"idref": "title-page"})
    for chapter in chapters:
        item_id = f"chapter-{chapter.number:02d}"
        href = f"text/{item_id}.xhtml"
        ET.SubElement(manifest, f"{{{_OPF_NS}}}item", {"id": item_id, "href": href, "media-type": "application/xhtml+xml"})
        ET.SubElement(spine, f"{{{_OPF_NS}}}itemref", {"idref": item_id})
    return ET.tostring(package, encoding="utf-8", xml_declaration=True)


def _nav_xhtml(metadata: BookMetadata, chapters: list[Chapter]) -> str:
    entries = "\n".join(
        f'<li><a href="text/chapter-{chapter.number:02d}.xhtml">{html.escape(chapter.title)}</a></li>'
        for chapter in chapters
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<html xmlns="{_XHTML_NS}" xmlns:epub="{_EPUB_NS}" lang="{html.escape(metadata.language)}">\n'
        f"<head><title>{html.escape(metadata.title)} — Contents</title></head>\n"
        f'<body><nav epub:type="toc" id="toc"><h1>Contents</h1><ol>{entries}</ol></nav></body></html>\n'
    )


def _title_page_xhtml(metadata: BookMetadata) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<html xmlns="{_XHTML_NS}" lang="{html.escape(metadata.language)}">\n'
        f"<head><title>{html.escape(metadata.title)}</title></head>\n"
        f'<body class="titlepage"><h1>{html.escape(metadata.title)}</h1><p>{html.escape(metadata.author)}</p></body></html>\n'
    )


def write_epub(path: Path, chapters: list[Chapter], metadata: BookMetadata) -> None:
    """Write an EPUB3 package with a generated navigation document."""

    modified = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    css = (
        "p { margin: 0; text-indent: 1.25em; widows: 2; orphans: 2; }\n"
        "h1 { margin: 3em 0 2em; text-indent: 0; page-break-before: always; }\n"
        "h1 + p, hr + p { text-indent: 0; }\n"
        "hr.scene-break { width: 30%; margin: 1.5em auto; border: 0; border-top: 1px solid; }\n"
        ".titlepage { text-align: center; margin-top: 30%; }\n"
        ".titlepage p { text-indent: 0; margin-top: 1em; }\n"
    )
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<container version="1.0" xmlns="{_CONTAINER_NS}"><rootfiles>'
        '<rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>'
        "</rootfiles></container>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("EPUB/content.opf", _opf_xml(metadata, chapters, modified))
        archive.writestr("EPUB/nav.xhtml", _nav_xhtml(metadata, chapters))
        archive.writestr("EPUB/styles.css", css)
        archive.writestr("EPUB/titlepage.xhtml", _title_page_xhtml(metadata))
        for chapter in chapters:
            filename = f"EPUB/text/chapter-{chapter.number:02d}.xhtml"
            archive.writestr(filename, _xhtml_page(chapter.title, markdown_body_to_xhtml(chapter.body), metadata.language))


def validate_epub(path: Path, expected_chapters: int) -> dict[str, int | str]:
    """Validate the package structure, spine and generated table of contents."""

    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if names[0] != "mimetype" or archive.read("mimetype") != b"application/epub+zip":
                raise ExportError("EPUB mimetype must be the first uncompressed entry")
            if len(names) != len(set(names)):
                raise ExportError("EPUB contains duplicate archive entries")
            xhtml_names = [name for name in names if name.lower().endswith((".xhtml", ".html"))]
            for name in xhtml_names:
                try:
                    ET.fromstring(archive.read(name))
                except (ET.ParseError, UnicodeDecodeError) as exc:
                    raise ExportError(f"EPUB XHTML is not well-formed: {name}: {exc}") from exc
            root = ET.fromstring(archive.read("META-INF/container.xml"))
            rootfile = root.find(f".//{{{_CONTAINER_NS}}}rootfile")
            if rootfile is None or rootfile.get("full-path") != "EPUB/content.opf":
                raise ExportError("EPUB container does not point to EPUB/content.opf")
            opf = ET.fromstring(archive.read("EPUB/content.opf"))
            manifest = {
                item.get("id"): item.get("href")
                for item in opf.findall(f"{{{_OPF_NS}}}manifest/{{{_OPF_NS}}}item")
            }
            spine_ids = [item.get("idref") for item in opf.findall(f"{{{_OPF_NS}}}spine/{{{_OPF_NS}}}itemref")]
            chapter_ids = [item_id for item_id in spine_ids if item_id and item_id.startswith("chapter-")]
            if len(chapter_ids) != expected_chapters:
                raise ExportError(f"EPUB spine has {len(chapter_ids)} chapters; expected {expected_chapters}")
            for item_id in chapter_ids:
                href = manifest.get(item_id)
                if not href or f"EPUB/{href}" not in names:
                    raise ExportError(f"EPUB spine item is missing: {item_id}")
            nav = ET.fromstring(archive.read("EPUB/nav.xhtml"))
            links = nav.findall(f".//{{{_XHTML_NS}}}a")
            chapter_links = [link for link in links if (link.get("href") or "").startswith("text/chapter-")]
            if len(chapter_links) != expected_chapters:
                raise ExportError(f"EPUB table of contents has {len(chapter_links)} chapters; expected {expected_chapters}")
            return {"chapters": len(chapter_ids), "toc_entries": len(chapter_links), "zip_entries": len(names), "status": "passed"}
    except zipfile.BadZipFile as exc:
        raise ExportError(f"invalid EPUB zip: {exc}") from exc


def _metadata_from_project(book_dir: Path) -> tuple[str, str, str]:
    state = book_dir / "PROJECT_STATE.yaml"
    if not state.is_file():
        raise ExportError("metadata is missing; provide --title, --author and --language")
    text = state.read_text(encoding="utf-8")

    def field(name: str) -> str:
        match = re.search(rf"^\s+{re.escape(name)}:\s*[\"']?([^\"'\n#]+?)[\"']?\s*(?:#.*)?$", text, re.MULTILINE)
        return match.group(1).strip() if match else ""

    title = field("title")
    language = field("language")
    author = ""
    assumptions = book_dir / "ASSUMPTIONS.md"
    if assumptions.is_file():
        match = re.search(r"^\s*(?:author|author name|nome do autor)\s*:\s*(.+?)\s*$", assumptions.read_text(encoding="utf-8"), re.IGNORECASE | re.MULTILINE)
        if match:
            author = match.group(1).strip().strip("*`")
    if not (title and language and author):
        raise ExportError("metadata is incomplete; provide --title, --author and --language (author is never inferred)")
    return title, author, language


def _write_export_notes(path: Path, metadata: BookMetadata, chapters: list[Chapter], output_names: list[str]) -> None:
    source_range = f"chapter-{chapters[0].number:02d}.md to chapter-{chapters[-1].number:02d}.md"
    word_counts = word_count_receipt(chapters)
    output_lines = ["- manuscript.md: created and validated"]
    output_lines.extend(
        f"- {name}: created and validated" + (" as a reading-proof PDF" if name.endswith(".pdf") else "")
        for name in output_names
        if name != "manuscript.md"
    )
    path.write_text(
        "\n".join(
            [
                f"# Export: {metadata.title}",
                f"Author: {metadata.author}. Language: {metadata.language}. Chapters: {source_range} ({len(chapters)} files).",
                "",
                "## Status",
                *output_lines,
                f"- word count: {word_counts['total']} prose words (receipt method: {word_counts['method']})",
                "- export-receipt.json: created with source and output hashes",
                "- quality gates: not assessed by this helper; no publication-readiness claim",
                "",
                "## Validation",
                "The source chapter order, heading shape, generated packages and text-preservation checks were checked before and after promotion while the cooperative book lock was held.",
                "",
                "## Before publishing",
                "Open the EPUB, DOCX and PDF proof in their readers and run platform validators where applicable. The PDF is a reading proof, not print-certified. The lock protects cooperating Book Genesis writers; a process that ignores it can still race after the final check. Confirm the proofread, final score, package, human decision and any cover requirements separately.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _approved_delivery_target(book_root: Path, delivery_dir: str | Path) -> Path:
    """Resolve the only delivery location this helper is allowed to replace."""

    root = book_root.resolve()
    approved = (root / "delivery").resolve()
    requested = Path(delivery_dir)
    candidate = requested if requested.is_absolute() else root / requested
    target = candidate.resolve()
    if target != approved:
        raise ExportError("delivery_dir must resolve to book_dir/delivery")
    return target


def _assert_sources_unchanged(chapters_dir: Path, initial: list[Chapter]) -> None:
    """Fail before promotion if any chapter was added, removed, or edited."""

    current = discover_chapters(chapters_dir)
    initial_signature = [(item.number, item.path.name, item.title, item.sha256) for item in initial]
    current_signature = [(item.number, item.path.name, item.title, item.sha256) for item in current]
    if current_signature != initial_signature:
        raise ExportError("source chapter set changed during export; nothing was promoted")


@contextmanager
def _book_lock(book_root: Path):
    """Hold the cooperative single-writer lock for the whole export transaction.

    The promotion helper uses the same ``.book-genesis-write.lock`` file in the
    canonical chapter directory. This prevents cooperating writers from
    changing chapter bytes between source verification and delivery promotion.
    A non-cooperating external writer can still race after the last check; the
    post-promotion check detects the ordinary case and restores the previous
    delivery when one exists.
    """

    lock_path = book_root / "manuscript" / "chapters" / ".book-genesis-write.lock"
    descriptor: int | None = None
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
    except FileExistsError as exc:
        raise ExportError(f"book is locked by another writer: {lock_path}") from exc
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        lock_path.unlink(missing_ok=True)
        raise
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def _export_book_locked(
    book_dir: str | Path,
    delivery_dir: str | Path,
    *,
    title: str,
    author: str,
    language: str,
    slug: str | None = None,
    overwrite: bool = False,
    docx: bool = False,
    pdf: bool = False,
    require_complete_pipeline: bool = False,
    expected_chapters: int | None = None,
    min_words: int | None = None,
    max_words: int | None = None,
) -> dict[str, object]:
    """Export a canonical chapter set while the cooperative lock is held."""

    metadata = _require_metadata(title, author, language, slug)
    book_root = Path(book_dir).resolve()
    chapters_dir = book_root / "manuscript" / "chapters"
    chapters = discover_chapters(chapters_dir)
    if any(value is not None and value < 0 for value in (expected_chapters, min_words, max_words)):
        raise ExportError("complete pipeline count assertions must be non-negative")
    if expected_chapters == 0:
        raise ExportError("complete pipeline expected_chapters must be greater than zero")
    if min_words is not None and max_words is not None and min_words > max_words:
        raise ExportError("complete pipeline min_words cannot exceed max_words")
    if require_complete_pipeline:
        _complete_pipeline_preflight(
            book_root,
            chapters,
            expected_chapters=expected_chapters,
            min_words=min_words,
            max_words=max_words,
        )
    elif any(value is not None for value in (expected_chapters, min_words, max_words)):
        _assert_count_contract(
            chapters,
            expected_chapters=expected_chapters,
            min_words=min_words,
            max_words=max_words,
        )
    if not chapters_dir.resolve().is_relative_to(book_root):
        raise ExportError("chapter directory must be inside book_dir")
    target = _approved_delivery_target(book_root, delivery_dir)
    if target.exists() and not target.is_dir():
        raise ExportError(f"delivery target is not a directory: {target}")
    if target.exists() and any(target.iterdir()) and not overwrite:
        raise ExportError(f"delivery directory is not empty; pass overwrite=True deliberately: {target}")

    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=parent))
    backup: Path | None = None
    promoted = False
    manuscript_name = "manuscript.md"
    epub_name = f"{metadata.slug}.epub"
    output_names = [manuscript_name, epub_name]
    word_counts = word_count_receipt(chapters)
    try:
        manuscript_path = stage / manuscript_name
        manuscript_path.write_text(assemble_manuscript(chapters, metadata), encoding="utf-8", newline="\n")
        epub_path = stage / epub_name
        write_epub(epub_path, chapters, metadata)
        validation = validate_epub(epub_path, len(chapters))
        optional_validation: dict[str, dict[str, int | str]] = {}
        optional_paths: dict[str, Path] = {}
        if docx:
            docx_name = f"{metadata.slug}.docx"
            docx_path = stage / docx_name
            _write_docx(docx_path, chapters, metadata)
            optional_validation["docx"] = validate_docx(docx_path, chapters)
            optional_paths["docx"] = docx_path
            output_names.append(docx_name)
        if pdf:
            pdf_name = f"{metadata.slug}.pdf"
            pdf_path = stage / pdf_name
            _write_pdf(pdf_path, chapters, metadata)
            optional_validation["pdf"] = validate_pdf(pdf_path, chapters)
            optional_paths["pdf"] = pdf_path
            output_names.append(pdf_name)
        notes_path = stage / "EXPORT.md"
        _write_export_notes(notes_path, metadata, chapters, output_names)
        output_hashes = {
            manuscript_name: {"sha256": _sha256_file(manuscript_path)},
            epub_name: {"sha256": _sha256_file(epub_path)},
        }
        for format_name, optional_path in optional_paths.items():
            output_hashes[optional_path.name] = {"sha256": _sha256_file(optional_path), "format": format_name}
        receipt = {
            "schema_version": 1,
            "title": metadata.title,
            "author": metadata.author,
            "language": metadata.language,
            "slug": metadata.slug,
            "chapter_count": len(chapters),
            "word_count": word_counts,
            "source_chapters": [
                {"number": chapter.number, "path": chapter.path.name, "title": chapter.title, "sha256": chapter.sha256}
                for chapter in chapters
            ],
            "outputs": output_hashes,
            "validation": {"status": validation["status"], "epub": validation, **optional_validation},
            "quality": {"status": "not_assessed", "quality_gate_passed": False},
        }
        (stage / "export-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        _assert_sources_unchanged(chapters_dir, chapters)

        if target.exists():
            if any(target.iterdir()):
                backup = parent / f".{target.name}.backup-{uuid.uuid4().hex}"
                target.rename(backup)
            else:
                target.rmdir()
        stage.rename(target)
        promoted = True
        # Verify again after the atomic directory replacement. This closes the
        # ordinary stale-export window between the pre-promotion check and the
        # rename; the cooperative lock protects writers using the same protocol.
        _assert_sources_unchanged(chapters_dir, chapters)
        if backup is not None:
            _assert_sources_unchanged(chapters_dir, chapters)
            shutil.rmtree(backup, ignore_errors=True)
        result: dict[str, object] = {
            "delivery_dir": str(target),
            "manuscript": str(target / manuscript_name),
            "epub": str(target / epub_name),
            "receipt": str(target / "export-receipt.json"),
            "chapter_count": len(chapters),
            "word_count": word_counts,
            "validation": {"status": validation["status"], "epub": validation, **optional_validation},
        }
        if docx:
            result["docx"] = str(target / f"{metadata.slug}.docx")
        if pdf:
            result["pdf"] = str(target / f"{metadata.slug}.pdf")
        return result
    except Exception:
        if promoted and target.exists():
            shutil.rmtree(target, ignore_errors=True)
        if backup is not None and backup.exists() and not target.exists():
            backup.rename(target)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if backup is not None and backup.exists() and promoted:
            shutil.rmtree(backup, ignore_errors=True)


def export_book(
    book_dir: str | Path,
    delivery_dir: str | Path,
    *,
    title: str,
    author: str,
    language: str,
    slug: str | None = None,
    overwrite: bool = False,
    docx: bool = False,
    pdf: bool = False,
    require_complete_pipeline: bool = False,
    expected_chapters: int | None = None,
    min_words: int | None = None,
    max_words: int | None = None,
) -> dict[str, object]:
    """Export while holding the cooperative book-wide writer lock."""

    book_root = Path(book_dir).resolve()
    with _book_lock(book_root):
        return _export_book_locked(
            book_root,
            delivery_dir,
            title=title,
            author=author,
            language=language,
            slug=slug,
            overwrite=overwrite,
            docx=docx,
            pdf=pdf,
            require_complete_pipeline=require_complete_pipeline,
            expected_chapters=expected_chapters,
            min_words=min_words,
            max_words=max_words,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble canonical chapters and export validated book formats.")
    parser.add_argument("--book-dir", default=".")
    parser.add_argument("--delivery-dir", default="delivery")
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--language")
    parser.add_argument("--slug")
    parser.add_argument("--overwrite", action="store_true", help="replace a non-empty delivery directory deliberately")
    parser.add_argument("--docx", action="store_true", help="also create and validate a DOCX reading proof")
    parser.add_argument("--pdf", action="store_true", help="also create and validate a 5.5 x 8.5 inch PDF reading proof")
    parser.add_argument("--require-complete-pipeline", action="store_true", help="require canonical pipeline evidence before delivery")
    parser.add_argument("--expected-chapters", type=int, help="assert the approved complete-book chapter count")
    parser.add_argument("--min-words", type=int, help="assert the approved minimum prose word count")
    parser.add_argument("--max-words", type=int, help="assert the approved maximum prose word count")
    args = parser.parse_args(argv)
    try:
        if args.title and args.author and args.language:
            title, author, language = args.title, args.author, args.language
        else:
            title, author, language = _metadata_from_project(Path(args.book_dir))
        result = export_book(
            args.book_dir,
            args.delivery_dir,
            title=title,
            author=author,
            language=language,
            slug=args.slug,
            overwrite=args.overwrite,
            docx=args.docx,
            pdf=args.pdf,
            require_complete_pipeline=args.require_complete_pipeline,
            expected_chapters=args.expected_chapters,
            min_words=args.min_words,
            max_words=args.max_words,
        )
    except ExportError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
