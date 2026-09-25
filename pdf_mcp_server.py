import base64

from mcp.server.mcpserver import MCPServer

from pdf_builder import build_analysis_pdf


mcp = MCPServer(
    "Business Analysis PDF Builder",
    instructions=(
        "Build stakeholder-ready PDF reports from approved, sanitized analysis outputs. "
        "The tool never needs raw uploaded datasets."
    ),
)


@mcp.tool()
def build_business_analysis_pdf(report: dict) -> dict:
    """Build a PDF from user-approved questions, interpretations, charts, and result tables."""
    pdf_bytes, filename = build_analysis_pdf(report)
    return {
        "filename": filename,
        "mime_type": "application/pdf",
        "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
