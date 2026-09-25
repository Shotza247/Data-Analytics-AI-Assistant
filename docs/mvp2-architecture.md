# MVP2 Architecture

This document is the versioned source of truth for the MVP2 workflow. It complements the shared Mermaid workspace linked from the README and should be updated whenever the application boundary or export contract changes.

## Privacy-Safe Analysis And Report Flow

```mermaid
flowchart LR
    User[User] --> Upload[Upload CSV]
    Upload --> Scan[Detect likely PII/SPI]
    Scan --> Mask[Mask protected values in session]
    Mask --> Summary[Data Summary\nPreview and privacy table]
    Mask --> Context[Privacy-safe dataframe\nBusiness context and chat]
    Context --> OpenAI[OpenAI analysis request]
    OpenAI --> Execute[Execute generated analysis\nTables and charts]
    Execute --> Grounded[Second-pass grounded\nstakeholder interpretation]
    Grounded --> Chat[Insights conversation]
    Grounded --> ExportIntent{User asks\nfor PDF?}
    ExportIntent -->|No| Chat
    ExportIntent -->|Yes| Consent[Show export disclosure\nand request approval]
    Consent -->|Cancel| Chat
    Consent -->|Approve| Payload[Sanitized report payload\nNo raw CSV or protected values]
    Payload --> MCP[PDF MCP service\nStreamable HTTP]
    MCP --> PDF[Download stakeholder PDF]

    classDef sensitive fill:#fce8e6,stroke:#b3261e,color:#5f0000;
    class Upload,Scan sensitive;
```

## PDF Export Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant S as Streamlit app
    participant O as OpenAI
    participant M as PDF MCP service

    U->>S: Ask to create a PDF report
    S->>O: Analysis request with typed export tool
    O-->>S: request_pdf_report(title, focus)
    S-->>U: Explain report data boundary and ask approval
    alt User approves
        S->>S: Build sanitized report payload
        Note over S: Questions, interpretations, charts, capped tables,<br/>privacy metadata, and session usage only
        S->>M: build_business_analysis_pdf(report)
        M-->>S: PDF bytes and filename
        S-->>U: Download PDF report
    else User cancels
        S-->>U: Keep analysis in the chat session
    end
```

## Report Contents

The first page contains a structured report overview, privacy-protection summary, detected PII/SPI column metadata, and session usage. The remaining pages contain business questions, grounded stakeholder interpretations, charts, capped result tables, and caveats. The report records only metadata about protected columns, never original or masked sensitive values.

## Deployment Boundary

The bundled local service runs at `http://localhost:8000/mcp` for development. Production deployment must terminate TLS, expose an authenticated HTTPS `/mcp` endpoint, and set `PDF_MCP_URL` in Streamlit configuration. The Streamable HTTP transport keeps the service deployable without a local stdio dependency.
