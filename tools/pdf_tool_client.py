import base64
import json

from mcp import Client


async def request_pdf_report(server_url, report):
    async with Client(server_url) as client:
        result = await client.call_tool(
            "build_business_analysis_pdf",
            {"report": report},
        )
    payload = result.structured_content or {}
    if isinstance(payload.get("result"), dict):
        payload = payload["result"]
    if not payload.get("pdf_base64"):
        for block in result.content:
            text = getattr(block, "text", None)
            if not text:
                continue
            try:
                candidate = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate.get("result"), dict):
                candidate = candidate["result"]
            if candidate.get("pdf_base64"):
                payload = candidate
                break
    if not payload.get("pdf_base64"):
        raise ValueError("The PDF service returned no document data.")
    return {
        "filename": payload.get("filename", "business-analysis-report.pdf"),
        "mime_type": payload.get("mime_type", "application/pdf"),
        "pdf_bytes": base64.b64decode(payload["pdf_base64"], validate=True),
    }
