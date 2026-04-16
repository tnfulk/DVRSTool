"""Documentation maintenance tests for salesperson-facing guides."""

from __future__ import annotations

import unittest
from pathlib import Path

from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
FULL_GUIDE = DOCS_DIR / "salesperson-user-guide.md"
QUICK_REFERENCE = DOCS_DIR / "salesperson-quick-reference.md"
FULL_GUIDE_PDF = DOCS_DIR / "salesperson-user-guide.pdf"
QUICK_REFERENCE_PDF = DOCS_DIR / "salesperson-quick-reference.pdf"
PDF_GENERATOR = REPO_ROOT / "tools" / "generate_sales_doc_pdfs.py"

TOOL_IMPACT_PATHS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "dvrs-web-app-design.md",
    REPO_ROOT / "dvrs_tool",
]
FRESHNESS_TOLERANCE_SECONDS = 1.0


def _latest_mtime(path: Path) -> float:
    if path.is_file():
        return path.stat().st_mtime
    return max(
        child.stat().st_mtime
        for child in path.rglob("*")
        if child.is_file() and "__pycache__" not in child.parts
    )


class SalesDocumentationTests(unittest.TestCase):
    def test_sales_guides_exist(self) -> None:
        self.assertTrue(FULL_GUIDE.exists(), f"Missing full sales guide: {FULL_GUIDE}")
        self.assertTrue(QUICK_REFERENCE.exists(), f"Missing sales quick reference: {QUICK_REFERENCE}")
        self.assertTrue(FULL_GUIDE_PDF.exists(), f"Missing full sales guide PDF: {FULL_GUIDE_PDF}")
        self.assertTrue(QUICK_REFERENCE_PDF.exists(), f"Missing sales quick reference PDF: {QUICK_REFERENCE_PDF}")

    def test_sales_guides_include_required_escalation_guidance(self) -> None:
        full_text = FULL_GUIDE.read_text(encoding="utf-8")
        quick_text = QUICK_REFERENCE.read_text(encoding="utf-8")

        for text, label in ((full_text, "full guide"), (quick_text, "quick reference")):
            self.assertIn("technically valid plan", text.lower(), f"{label} must address technically valid plan outcomes.")
            self.assertIn(
                "confirm that the information provided is accurate",
                text.lower(),
                f"{label} must tell the user to verify input accuracy first.",
            )
            self.assertIn(
                "motorola solutions presales engineering",
                text.lower(),
                f"{label} must direct the user to Motorola Solutions presales engineering.",
            )
            self.assertIn(
                "product management",
                text.lower(),
                f"{label} must mention DVRS product management involvement.",
            )
            self.assertIn(
                "development engineering",
                text.lower(),
                f"{label} must mention development engineering involvement.",
            )

    def test_sales_guides_are_not_older_than_tool_sources_they_track(self) -> None:
        latest_tool_change = max(_latest_mtime(path) for path in TOOL_IMPACT_PATHS)

        self.assertGreaterEqual(
            FULL_GUIDE.stat().st_mtime + FRESHNESS_TOLERANCE_SECONDS,
            latest_tool_change,
            "docs/salesperson-user-guide.md should be reviewed and updated during documentation passes when tool files change.",
        )
        self.assertGreaterEqual(
            QUICK_REFERENCE.stat().st_mtime + FRESHNESS_TOLERANCE_SECONDS,
            latest_tool_change,
            "docs/salesperson-quick-reference.md should be reviewed and updated during documentation passes when tool files change.",
        )

    def test_sales_pdfs_are_current_and_extractable(self) -> None:
        self.assertGreaterEqual(
            FULL_GUIDE_PDF.stat().st_mtime + FRESHNESS_TOLERANCE_SECONDS,
            max(FULL_GUIDE.stat().st_mtime, PDF_GENERATOR.stat().st_mtime),
            "docs/salesperson-user-guide.pdf should be regenerated after the markdown guide changes.",
        )
        self.assertGreaterEqual(
            QUICK_REFERENCE_PDF.stat().st_mtime + FRESHNESS_TOLERANCE_SECONDS,
            max(QUICK_REFERENCE.stat().st_mtime, PDF_GENERATOR.stat().st_mtime),
            "docs/salesperson-quick-reference.pdf should be regenerated after the markdown guide changes.",
        )

        full_reader = PdfReader(str(FULL_GUIDE_PDF))
        quick_reader = PdfReader(str(QUICK_REFERENCE_PDF))
        self.assertGreaterEqual(len(full_reader.pages), 2)
        self.assertGreaterEqual(len(quick_reader.pages), 1)

        full_text = "\n".join(page.extract_text() or "" for page in full_reader.pages).lower()
        quick_text = "\n".join(page.extract_text() or "" for page in quick_reader.pages).lower()

        self.assertIn("dvrs planner", full_text)
        self.assertIn("salesperson user guide", full_text)
        self.assertIn("motorola solutions presales engineering", full_text)

        self.assertIn("dvrs planner", quick_text)
        self.assertIn("sales quick reference", quick_text)
        self.assertIn("confirm that the information provided is accurate", quick_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
