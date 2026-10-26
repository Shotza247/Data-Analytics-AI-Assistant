import base64
import io
import re
from datetime import datetime, timezone

from fpdf import FPDF


SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9_-]+")
TEXT_REPLACEMENTS = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
        "\u2026": "...",
    }
)


def _pdf_text(value):
    return str(value or "").translate(TEXT_REPLACEMENTS).encode("latin-1", "replace").decode("latin-1")


class AnalysisPDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.report_title = _pdf_text(title)
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(16, 16, 16)

    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(23, 50, 77)
        self.cell(0, 8, self.report_title, align="C")
        self.ln(11)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(95, 103, 115)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

    def section_title(self, text):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(23, 50, 77)
        self.multi_cell(0, 8, _pdf_text(text))
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(39, 52, 68)
        self.multi_cell(0, 6, _pdf_text(text))
        self.ln(2)


def _safe_filename(title):
    stem = SAFE_FILENAME_RE.sub("-", title.strip()).strip("-").lower()
    return f"{stem or 'business-analysis-report'}.pdf"


def _add_table(pdf, table):
    columns = [str(column) for column in table.get("columns", [])][:8]
    rows = table.get("rows", [])[:10]
    if not columns or not rows:
        return

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(23, 50, 77)
    pdf.set_text_color(255, 255, 255)
    width = min(38, 178 / len(columns))
    for column in columns:
        pdf.cell(width, 7, _pdf_text(column)[:22], border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(39, 52, 68)
    for row in rows:
        for value in list(row)[: len(columns)]:
            pdf.cell(width, 7, _pdf_text(value)[:22], border=1)
        pdf.ln()
    pdf.ln(3)


def _add_summary_table(pdf, rows):
    label_width = 58
    value_width = 120
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(232, 238, 244)
        pdf.set_text_color(23, 50, 77)
        pdf.cell(label_width, 8, _pdf_text(label), border=1, fill=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(39, 52, 68)
        pdf.cell(value_width, 8, _pdf_text(value)[:75], border=1)
        pdf.ln()
    pdf.ln(3)


def _add_privacy_summary(pdf, privacy):
    if not privacy:
        return

    findings = privacy.get("findings", [])
    pdf.section_title("Privacy Protection")
    _add_summary_table(
        pdf,
        [
            ("Dataset", f"{privacy.get('rows', 0):,} rows x {privacy.get('columns', 0):,} columns"),
            ("Memory usage", f"{privacy.get('memory_mb', 0):.2f} MB"),
            ("Protected columns", privacy.get("protected_columns", 0)),
            ("Analysis columns", privacy.get("analysis_columns", 0)),
            ("Protection status", "Sensitive values masked before AI access"),
        ],
    )
    if findings:
        _add_table(
            pdf,
            {
                "columns": ["Column", "Type", "Detected by"],
                "rows": [
                    [item.get("column", ""), item.get("type", ""), item.get("detected_by", "")]
                    for item in findings
                ],
            },
        )
        pdf.body_text(
            "PII/SPI values are not included in this report. Masked columns remain usable only "
            "for anonymous counts, grouping, and pattern analysis."
        )
    else:
        pdf.body_text("No likely PII or SPI columns were detected during the upload privacy scan.")


def _add_usage_summary(pdf, usage):
    if not usage:
        return

    estimated_cost = usage.get("estimated_cost_usd")
    cost_text = "Unavailable for the configured model"
    if estimated_cost is not None:
        cost_text = f"USD {estimated_cost:.6f}"

    pdf.section_title("Session Usage")
    _add_summary_table(
        pdf,
        [
            (
                "Requests used",
                f"{usage.get('requests_used', 0)} of {usage.get('request_limit', 0)}",
            ),
            ("Requests remaining", usage.get("requests_remaining", 0)),
            ("Input tokens", f"{usage.get('input_tokens', 0):,}"),
            ("Output tokens", f"{usage.get('output_tokens', 0):,}"),
            ("Total tokens", f"{usage.get('total_tokens', 0):,}"),
            ("Estimated token cost", cost_text),
            ("Pricing model", usage.get("model") or "Not configured"),
        ],
    )
    pdf.body_text(
        "The token cost is an application estimate and may differ from provider billing."
    )


def build_analysis_pdf(report):
    title = report.get("title") or "Business Analysis Report"
    pdf = AnalysisPDF(title)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(23, 50, 77)
    pdf.multi_cell(0, 12, _pdf_text(title), align="C")
    pdf.ln(4)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.section_title("Report Overview")
    _add_summary_table(
        pdf,
        [
            ("Industry", report.get("industry") or "Not specified"),
            ("Business goal", report.get("business_goal") or "Not specified"),
            ("Report focus", report.get("focus") or "Business decision support"),
            ("Generated", generated_at),
        ],
    )
    _add_privacy_summary(pdf, report.get("privacy_summary"))
    _add_usage_summary(pdf, report.get("usage_summary"))

    for index, item in enumerate(report.get("analyses", []), start=1):
        pdf.add_page()
        pdf.section_title(f"Analysis {index}: Business Question")
        pdf.body_text(item.get("question"))
        pdf.section_title("Stakeholder Interpretation")
        pdf.body_text(item.get("interpretation"))

        for encoded_image in item.get("images", []):
            try:
                image_bytes = base64.b64decode(encoded_image, validate=True)
                image_stream = io.BytesIO(image_bytes)
                pdf.image(image_stream, w=178)
                pdf.ln(4)
            except Exception:
                pdf.body_text("A chart image could not be included in this report.")

        for table in item.get("tables", []):
            pdf.section_title("Supporting Results")
            _add_table(pdf, table)

        notes = item.get("notes", [])
        if notes:
            pdf.section_title("Caveats")
            for note in notes:
                pdf.body_text(note)

    output = pdf.output()
    return bytes(output), _safe_filename(title)
