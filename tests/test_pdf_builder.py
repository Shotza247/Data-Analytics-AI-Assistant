import unittest

from pdf_builder import _add_privacy_summary, _add_usage_summary, build_analysis_pdf


class RecordingPDF:
    def __init__(self):
        self.sections = []
        self.body = []
        self.cells = []

    def section_title(self, text):
        self.sections.append(text)

    def body_text(self, text):
        self.body.append(text)

    def set_font(self, *args, **kwargs):
        pass

    def set_fill_color(self, *args, **kwargs):
        pass

    def set_text_color(self, *args, **kwargs):
        pass

    def cell(self, width, height, text, **kwargs):
        self.cells.append(text)

    def ln(self, *args, **kwargs):
        pass


class PDFBuilderTest(unittest.TestCase):
    def test_builds_pdf_from_sanitized_report_payload(self):
        report = {
            "title": "Regional Performance Review",
            "industry": "Retail",
            "business_goal": "Prioritize regional investment",
            "usage_summary": {
                "model": "gpt-4o",
                "request_limit": 10,
                "requests_used": 3,
                "requests_remaining": 7,
                "input_tokens": 2400,
                "output_tokens": 600,
                "total_tokens": 3000,
                "estimated_cost_usd": 0.012,
            },
            "analyses": [
                {
                    "question": "Which region is strongest?",
                    "interpretation": (
                        "The northern region leads revenue and should receive priority.\n\n"
                        "Validate margin, capacity, and the customer\u2019s response before "
                        "reallocating spend \u2014 then monitor the result."
                    ),
                    "images": [],
                    "tables": [
                        {"columns": ["Region", "Revenue"], "rows": [["North", 1200]]}
                    ],
                    "notes": ["Results reflect the uploaded period only."],
                }
            ],
        }

        pdf_bytes, filename = build_analysis_pdf(report)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertEqual(filename, "regional-performance-review.pdf")

    def test_replaces_unicode_not_supported_by_builtin_pdf_fonts(self):
        report = {
            "title": "Executive \u201cGrowth\u201d Review",
            "focus": "Protect margin \u2014 then scale",
            "analyses": [
                {
                    "question": "What\u2019s changing?",
                    "interpretation": "Revenue improved\u2026 but causation is not established.",
                }
            ],
        }

        pdf_bytes, _ = build_analysis_pdf(report)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_renders_complete_session_usage_summary(self):
        pdf = RecordingPDF()
        usage = {
            "model": "gpt-4o",
            "request_limit": 10,
            "requests_used": 4,
            "requests_remaining": 6,
            "input_tokens": 8077,
            "output_tokens": 923,
            "total_tokens": 9000,
            "estimated_cost_usd": 0.0294225,
        }

        _add_usage_summary(pdf, usage)

        self.assertEqual(pdf.sections, ["Session Usage"])
        self.assertIn("Requests used", pdf.cells)
        self.assertIn("4 of 10", pdf.cells)
        self.assertIn("Requests remaining", pdf.cells)
        self.assertIn("8,077", pdf.cells)
        self.assertIn("923", pdf.cells)
        self.assertIn("9,000", pdf.cells)
        self.assertIn("USD 0.029423", pdf.cells)
        self.assertIn("gpt-4o", pdf.cells)
        self.assertIn("may differ from provider billing", "\n".join(pdf.body))

    def test_renders_privacy_protection_summary_without_sensitive_values(self):
        pdf = RecordingPDF()
        privacy = {
            "rows": 100,
            "columns": 8,
            "memory_mb": 0.25,
            "protected_columns": 2,
            "analysis_columns": 6,
            "findings": [
                {"column": "email", "type": "PII", "detected_by": "column name"},
                {"column": "credit_score", "type": "SPI", "detected_by": "column name"},
            ],
        }

        _add_privacy_summary(pdf, privacy)

        self.assertEqual(pdf.sections, ["Privacy Protection"])
        self.assertIn("email", pdf.cells)
        self.assertIn("credit_score", pdf.cells)
        self.assertIn("PII/SPI values are not included", "\n".join(pdf.body))


if __name__ == "__main__":
    unittest.main()
