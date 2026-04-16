"""Generate styled PDF versions of the salesperson-facing DVRS documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from textwrap import wrap


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN_X = 54
MARGIN_TOP = 72
MARGIN_BOTTOM = 54
BODY_WIDTH = PAGE_WIDTH - (MARGIN_X * 2)
NAVY = (0.05, 0.15, 0.27)
BLUE = (0.0, 0.43, 0.69)
LIGHT_BLUE = (0.87, 0.93, 0.97)
STEEL = (0.70, 0.77, 0.83)
TEXT = (0.12, 0.12, 0.12)
MUTED = (0.40, 0.46, 0.52)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


@dataclass
class Block:
    kind: str
    text: str
    indent: int = 0


class PdfCanvas:
    def __init__(self) -> None:
        self.pages: list[str] = []
        self._commands: list[str] = []

    def new_page(self) -> None:
        if self._commands:
            self.pages.append("\n".join(self._commands))
        self._commands = []

    def text(self, x: float, y: float, value: str, size: int = 10, bold: bool = False, color: tuple[float, float, float] = TEXT) -> None:
        font = "F2" if bold else "F1"
        r, g, b = color
        self._commands.append(
            f"BT /{font} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x:.2f} {y:.2f} Tm ({_escape_pdf_text(value)}) Tj ET"
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, width: float = 1.0, color: tuple[float, float, float] = BLUE) -> None:
        r, g, b = color
        self._commands.append(
            f"q {r:.3f} {g:.3f} {b:.3f} RG {width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S Q"
        )

    def fill_rect(self, x: float, y: float, width: float, height: float, color: tuple[float, float, float]) -> None:
        r, g, b = color
        self._commands.append(
            f"q {r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} {width:.2f} {height:.2f} re f Q"
        )

    def stroke_rect(self, x: float, y: float, width: float, height: float, line_width: float = 0.8, color: tuple[float, float, float] = BLUE) -> None:
        r, g, b = color
        self._commands.append(
            f"q {r:.3f} {g:.3f} {b:.3f} RG {line_width:.2f} w {x:.2f} {y:.2f} {width:.2f} {height:.2f} re S Q"
        )

    def finish(self) -> bytes:
        if self._commands:
            self.pages.append("\n".join(self._commands))
            self._commands = []
        return _write_pdf(self.pages)


def parse_markdown_blocks(text: str) -> tuple[str, list[Block]]:
    lines = text.splitlines()
    title = ""
    blocks: list[Block] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(Block("paragraph", " ".join(item.strip() for item in paragraph if item.strip())))
            paragraph = []

    for line in lines:
        stripped = line.strip()
        if line.startswith("# "):
            flush_paragraph()
            title = stripped[2:].strip()
            continue
        if not stripped:
            flush_paragraph()
            continue
        if line.startswith("## "):
            flush_paragraph()
            blocks.append(Block("section", stripped[3:].strip()))
            continue
        if line.startswith("### "):
            flush_paragraph()
            blocks.append(Block("subsection", stripped[4:].strip()))
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            indent = max((len(line) - len(line.lstrip(" "))) // 2, 0)
            blocks.append(Block("bullet", stripped[2:].strip(), indent=indent))
            continue
        if _is_numbered_item(stripped):
            flush_paragraph()
            marker, content = stripped.split(" ", 1)
            blocks.append(Block("numbered", f"{marker} {content.strip()}"))
            continue
        paragraph.append(stripped)

    flush_paragraph()
    return title, blocks


def render_document(markdown_path: Path, pdf_path: Path, subtitle: str, include_toc: bool) -> None:
    title, blocks = parse_markdown_blocks(markdown_path.read_text(encoding="utf-8"))
    canvas = PdfCanvas()
    canvas.new_page()
    _draw_cover_page(canvas, title, subtitle, markdown_path)
    if include_toc:
        canvas.new_page()
        _draw_toc_page(canvas, blocks)
    _draw_content_pages(canvas, title, subtitle, blocks)
    pdf_path.write_bytes(canvas.finish())


def _draw_cover_page(canvas: PdfCanvas, title: str, subtitle: str, source_path: Path) -> None:
    canvas.fill_rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, NAVY)
    canvas.fill_rect(0, 180, PAGE_WIDTH, 18, BLUE)
    canvas.fill_rect(PAGE_WIDTH - 118, 0, 118, PAGE_HEIGHT, (0.03, 0.10, 0.19))
    canvas.fill_rect(MARGIN_X, 148, 160, 6, LIGHT_BLUE)
    canvas.stroke_rect(MARGIN_X, 520, 158, 88, line_width=1.0, color=STEEL)
    canvas.text(MARGIN_X, 650, "DVRS Planner", size=34, bold=True, color=(1, 1, 1))
    canvas.text(MARGIN_X, 612, subtitle, size=22, bold=True, color=(1, 1, 1))
    canvas.text(MARGIN_X, 575, "Motorola Solutions sales documentation", size=12, color=LIGHT_BLUE)
    canvas.text(MARGIN_X + 12, 586, "Ordering guide style companion", size=10, color=LIGHT_BLUE)
    canvas.text(MARGIN_X + 12, 572, "For salesperson use", size=10, color=LIGHT_BLUE)
    canvas.text(MARGIN_X + 12, 552, "Revision", size=10, bold=True, color=(1, 1, 1))
    canvas.text(MARGIN_X + 74, 552, _date_label(source_path), size=10, color=(1, 1, 1))
    canvas.text(MARGIN_X + 12, 534, "Document", size=10, bold=True, color=(1, 1, 1))
    canvas.text(MARGIN_X + 74, 534, source_path.stem, size=10, color=(1, 1, 1))
    canvas.text(MARGIN_X, 130, f"Source document: {source_path.name}", size=10, color=(1, 1, 1))
    canvas.text(MARGIN_X, 112, f"Revision generated from repo state: {_date_label(source_path)}", size=10, color=(1, 1, 1))
    canvas.text(MARGIN_X, 76, title, size=12, color=LIGHT_BLUE)
    canvas.text(PAGE_WIDTH - 86, 710, "Motorola", size=12, bold=True, color=(1, 1, 1))
    canvas.text(PAGE_WIDTH - 100, 694, "Solutions", size=12, bold=True, color=(1, 1, 1))


def _draw_toc_page(canvas: PdfCanvas, blocks: list[Block]) -> None:
    y = PAGE_HEIGHT - MARGIN_TOP
    _draw_page_header(canvas, "Table of Contents", "Sales Documentation")
    y -= 34
    sections = [block.text for block in blocks if block.kind == "section"]
    for index, section in enumerate(sections, start=1):
        if y < MARGIN_BOTTOM + 30:
            canvas.new_page()
            _draw_page_header(canvas, "Table of Contents", "Sales Documentation")
            y = PAGE_HEIGHT - MARGIN_TOP - 34
        canvas.fill_rect(MARGIN_X, y - 8, 18, 18, BLUE)
        canvas.text(MARGIN_X + 5, y - 3, str(index), size=9, bold=True, color=(1, 1, 1))
        for line in _wrap_text(section, size=11, width=BODY_WIDTH - 36):
            canvas.text(MARGIN_X + 28, y - 2, line, size=11)
            y -= 15
        y -= 6
    canvas.text(MARGIN_X, 90, "These PDFs are generated from the maintained markdown guides in this repository.", size=10, color=MUTED)


def _draw_content_pages(canvas: PdfCanvas, title: str, subtitle: str, blocks: list[Block]) -> None:
    canvas.new_page()
    page_number = 1
    y = _draw_page_frame(canvas, title, subtitle, page_number)

    for block in blocks:
        block_height = _estimate_block_height(block)
        if y - block_height < MARGIN_BOTTOM:
            page_number += 1
            canvas.new_page()
            y = _draw_page_frame(canvas, title, subtitle, page_number)

        if block.kind == "section":
            canvas.fill_rect(MARGIN_X, y - 8, BODY_WIDTH, 20, LIGHT_BLUE)
            canvas.text(MARGIN_X + 8, y - 2, block.text, size=13, bold=True, color=NAVY)
            y -= 28
        elif block.kind == "subsection":
            canvas.text(MARGIN_X, y, block.text, size=11, bold=True, color=BLUE)
            canvas.line(MARGIN_X, y - 4, MARGIN_X + 140, y - 4, width=1.2, color=BLUE)
            y -= 20
        elif block.kind == "paragraph":
            for line in _wrap_text(block.text, size=10, width=BODY_WIDTH):
                canvas.text(MARGIN_X, y, line, size=10)
                y -= 14
            y -= 6
        elif block.kind == "bullet":
            text_x = MARGIN_X + 18 + (block.indent * 14)
            canvas.fill_rect(text_x - 10, y - 3, 4, 4, BLUE)
            for i, line in enumerate(_wrap_text(block.text, size=10, width=BODY_WIDTH - (text_x - MARGIN_X))):
                canvas.text(text_x, y, line, size=10)
                y -= 14
            y -= 2
        elif block.kind == "numbered":
            marker, content = block.text.split(" ", 1)
            canvas.text(MARGIN_X, y, marker, size=10, bold=True, color=BLUE)
            for line in _wrap_text(content, size=10, width=BODY_WIDTH - 24):
                canvas.text(MARGIN_X + 24, y, line, size=10)
                y -= 14
            y -= 2


def _draw_page_header(canvas: PdfCanvas, left_title: str, right_title: str) -> None:
    canvas.fill_rect(0, PAGE_HEIGHT - 48, PAGE_WIDTH, 48, NAVY)
    canvas.text(MARGIN_X, PAGE_HEIGHT - 30, left_title, size=20, bold=True, color=(1, 1, 1))
    canvas.text(PAGE_WIDTH - 220, PAGE_HEIGHT - 28, right_title, size=10, color=LIGHT_BLUE)
    canvas.text(PAGE_WIDTH - 110, PAGE_HEIGHT - 42, "DVRS Planner", size=8, bold=True, color=STEEL)


def _draw_page_frame(canvas: PdfCanvas, title: str, subtitle: str, page_number: int) -> float:
    _draw_page_header(canvas, title, subtitle)
    canvas.line(MARGIN_X, PAGE_HEIGHT - 62, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 62, width=1.2, color=BLUE)
    canvas.line(MARGIN_X, 42, PAGE_WIDTH - MARGIN_X, 42, width=0.8, color=STEEL)
    canvas.text(MARGIN_X, 28, "Motorola Solutions DVRS Planner", size=9, color=MUTED)
    canvas.text(PAGE_WIDTH - 90, 28, f"Page {page_number}", size=9, color=MUTED)
    return PAGE_HEIGHT - MARGIN_TOP - 10


def _estimate_block_height(block: Block) -> float:
    if block.kind == "section":
        return 34
    if block.kind == "subsection":
        return 26
    if block.kind == "paragraph":
        return (14 * len(_wrap_text(block.text, size=10, width=BODY_WIDTH))) + 8
    if block.kind == "bullet":
        available_width = BODY_WIDTH - (18 + (block.indent * 14))
        return (14 * len(_wrap_text(block.text, size=10, width=available_width))) + 6
    if block.kind == "numbered":
        return (14 * len(_wrap_text(block.text, size=10, width=BODY_WIDTH - 24))) + 6
    return 20


def _wrap_text(text: str, size: int, width: float) -> list[str]:
    normalized = _normalize_text(text)
    chars_per_line = max(int(width / (size * 0.53)), 12)
    return wrap(normalized, width=chars_per_line, break_long_words=False, break_on_hyphens=False) or [normalized]


def _normalize_text(text: str) -> str:
    return (
        text.replace("`", "")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
    )


def _is_numbered_item(text: str) -> bool:
    parts = text.split(" ", 1)
    return len(parts) == 2 and parts[0].endswith(".") and parts[0][:-1].isdigit()


def _date_label(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def _escape_pdf_text(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _write_pdf(page_contents: list[str]) -> bytes:
    page_streams = [content.encode("latin-1", errors="replace") for content in page_contents]
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")

    kids = " ".join(f"{3 + index} 0 R" for index in range(len(page_streams)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_streams)} >>".encode("ascii"))

    font_object_id = 3 + len(page_streams)
    bold_font_object_id = font_object_id + 1
    first_stream_object_id = bold_font_object_id + 1

    for index in range(len(page_streams)):
        stream_id = first_stream_object_id + index
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_object_id} 0 R /F2 {bold_font_object_id} 0 R >> >> "
                f"/Contents {stream_id} 0 R >>"
            ).encode("ascii")
        )

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    for stream in page_streams:
        objects.append(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode("ascii"))
        buffer.write(obj)
        buffer.write(b"\nendobj\n")
    xref_offset = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    buffer.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return buffer.getvalue()


def main() -> int:
    render_document(
        DOCS_DIR / "salesperson-user-guide.md",
        DOCS_DIR / "salesperson-user-guide.pdf",
        "Salesperson User Guide",
        include_toc=True,
    )
    render_document(
        DOCS_DIR / "salesperson-quick-reference.md",
        DOCS_DIR / "salesperson-quick-reference.pdf",
        "Sales Quick Reference",
        include_toc=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
