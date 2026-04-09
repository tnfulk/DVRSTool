"""Small PDF export helper for DVRS ordering summaries."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from textwrap import wrap

from .models import CalculationResponse, FrequencyRange


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN = 42


def build_ordering_summary_pdf(response: CalculationResponse) -> bytes:
    """Return a lightweight one-page PDF for the recommended ordering summary."""

    lines: list[str] = []

    def text(x: float, y: float, value: str, size: int = 9, bold: bool = False) -> None:
        font = "F2" if bold else "F1"
        lines.append(f"BT /{font} {size} Tf {x:.2f} {y:.2f} Td ({_escape_pdf_text(value)}) Tj ET")

    def rule(x1: float, y1: float, x2: float, y2: float, width: float = 0.8) -> None:
        lines.append(f"{width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def box(x: float, y: float, width: float, height: float) -> None:
        lines.append(f"0.8 w {x:.2f} {y:.2f} {width:.2f} {height:.2f} re S")

    def wrapped_text(x: float, y: float, value: str, width: int = 92, size: int = 8) -> float:
        current_y = y
        for item in wrap(value, width=width) or [""]:
            text(x, current_y, item, size=size)
            current_y -= 11
        return current_y

    request = response.request
    system = response.system_summary
    ordering = response.ordering_summary
    recommended_plan = next(
        (
            plan
            for plan in response.plan_results
            if plan.proposed_dvrs_tx_range == ordering.proposed_dvrs_tx_range
            and plan.proposed_dvrs_rx_range == ordering.proposed_dvrs_rx_range
        ),
        response.plan_results[0] if response.plan_results else None,
    )

    y = 748
    text(MARGIN, y, "DVRS/VRX1000 SUPPLEMENTAL ORDERING FORM", size=14, bold=True)
    text(500, y, "Draft", size=10, bold=True)
    y -= 18
    text(MARGIN, y, f"Generated: {date.today().isoformat()}    Country: {request.country.value}", size=9)
    y -= 14
    rule(MARGIN, y, PAGE_WIDTH - MARGIN, y)

    y -= 24
    text(MARGIN, y, "1. Agency Name:", bold=True)
    rule(135, y - 2, 345, y - 2)
    text(360, y, "2. Date (YY/MM/DD):", bold=True)
    rule(468, y - 2, PAGE_WIDTH - MARGIN, y - 2)
    y -= 26
    text(MARGIN, y, "3. DVRS/VRX Order Code:", bold=True)
    rule(178, y - 2, 345, y - 2)
    text(360, y, "4. Selected DVR/VRX Configuration:", bold=True)
    text(512, y, recommended_plan.display_name if recommended_plan else "No recommended plan", size=8)
    y -= 28
    text(MARGIN, y, "5. Suitcase or Cabinet DVR Power Requirement:", bold=True)
    rule(280, y - 2, PAGE_WIDTH - MARGIN, y - 2)

    y -= 30
    text(MARGIN, y, "6. Specify DVR/VRX Frequencies", size=11, bold=True)
    y -= 14
    box(MARGIN, y - 70, PAGE_WIDTH - (MARGIN * 2), 78)
    rows = [
        ("Lowest DVR/VRX Transmit (MHz)", ordering.proposed_dvrs_tx_range, "low"),
        ("Highest DVR/VRX Transmit (MHz)", ordering.proposed_dvrs_tx_range, "high"),
        ("Lowest DVR Receive (MHz)", ordering.proposed_dvrs_rx_range, "low"),
        ("Highest DVR Receive (MHz)", ordering.proposed_dvrs_rx_range, "high"),
    ]
    row_y = y - 12
    for label, freq_range, edge in rows:
        text(MARGIN + 10, row_y, label)
        text(310, row_y, _range_edge(freq_range, edge), bold=True)
        rule(300, row_y - 2, PAGE_WIDTH - MARGIN - 10, row_y - 2)
        row_y -= 17

    y -= 104
    text(MARGIN, y, "7. Specify Trunked / System Frequencies", size=11, bold=True)
    y -= 14
    box(MARGIN, y - 96, PAGE_WIDTH - (MARGIN * 2), 104)
    text(298, y - 2, "700/800 MHz", bold=True)
    text(388, y - 2, "VHF", bold=True)
    text(456, y - 2, "UHF", bold=True)
    rule(285, y - 8, 285, y - 96)
    rule(375, y - 8, 375, y - 96)
    rule(445, y - 8, 445, y - 96)
    band_column = _band_column(system.detected_band.value)
    table_rows = [
        ("Band enabled in MSU?", "Yes"),
        ("DVRS/VRX1000 used with this band?", "Yes"),
        ("Lowest Mobile Radio Transmit (MHz)", f"{system.system_rx_range.low_mhz:.4f}"),
        ("Highest Mobile Radio Transmit (MHz)", f"{system.system_rx_range.high_mhz:.4f}"),
        ("Lowest Mobile Radio Receive (MHz)", _range_edge(system.system_tx_range, "low")),
        ("Highest Mobile Radio Receive (MHz)", _range_edge(system.system_tx_range, "high")),
    ]
    row_y = y - 22
    for label, value in table_rows:
        text(MARGIN + 10, row_y, label)
        text(band_column, row_y, value, bold=True)
        row_y -= 13

    y -= 130
    text(MARGIN, y, "8. Mobile Radio Type:", bold=True)
    rule(150, y - 2, 286, y - 2)
    text(304, y, "9. Control Head Type:", bold=True)
    rule(420, y - 2, PAGE_WIDTH - MARGIN, y - 2)
    y -= 24
    text(MARGIN, y, "10. MSU Antenna Type:", bold=True)
    rule(164, y - 2, PAGE_WIDTH - MARGIN, y - 2)

    y -= 28
    text(MARGIN, y, "Special Notes:", bold=True)
    notes = _notes_for_export(response)
    y = wrapped_text(MARGIN + 10, y - 16, notes, width=106, size=8)

    y = max(y - 8, 66)
    text(MARGIN, y, "NOTE:", bold=True)
    y = wrapped_text(
        MARGIN + 42,
        y,
        "Before placing your order, follow up with Futurecom so the proper frequency plan can be identified and approved. This draft is a planning aid, not a licensing approval.",
        width=90,
        size=8,
    )
    y -= 4
    text(MARGIN, y, "Please email the completed form to sales@futurecom.com", size=8, bold=True)

    return _write_pdf("\n".join(lines))


def _notes_for_export(response: CalculationResponse) -> str:
    summary_notes = list(response.ordering_summary.notes)
    for plan in response.plan_results:
        if plan.proposed_dvrs_tx_range == response.ordering_summary.proposed_dvrs_tx_range:
            summary_notes.extend(plan.warnings)
            summary_notes.extend(plan.regulatory_reasons)
            break
    if not summary_notes:
        summary_notes.append("No recommended standard plan was produced.")
    return " ".join(summary_notes)


def _range_edge(freq_range: FrequencyRange | None, edge: str) -> str:
    if freq_range is None:
        return ""
    value = freq_range.low_mhz if edge == "low" else freq_range.high_mhz
    return f"{value:.4f}"


def _band_column(band: str) -> int:
    if "700" in band or "800" in band:
        return 318
    if "VHF" in band:
        return 394
    return 466


def _escape_pdf_text(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_pdf(content: str) -> bytes:
    stream = content.encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

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
