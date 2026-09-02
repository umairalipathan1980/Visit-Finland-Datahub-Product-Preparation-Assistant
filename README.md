# Visit Finland DataHub Product Preparation Assistant

## Introduction

This application prepares evidence-grounded product records for the Visit Finland DataHub.

It currently supports Accommodation and Shops and produces reviewable JSON, Excel, Markdown, and source-reference artifacts. It does not submit records automatically.

The user selects a product type, such as Accommodation or Shops, and supplies one or more URLs with optional PDF or DOCX files. The tool analyzes the sources, combines their evidence, determines the product scope—such as the specific accommodation or shop represented—using predefined scope schemas, performs structured extraction against the selected schema, validates the record, and prepares outputs for entry into the Visit Finland DataHub, now operated by Business Finland.

## Architecture

| Component | Responsibility |
| --- | --- |
| `frontend/` | Next.js interface for starting, monitoring, reviewing, and approving runs |
| `app/api.py` | FastAPI service for runs, events, artifacts, approval, and deletion |
| `app/runner_optimized.py` | Claude Agent SDK workflow |
| `app/agent_tools.py` | Typed tools, evidence pagination, budgets, and finalization |
| `visit-finland-datahub-accommodation/SKILL.md` | Workflow instructions and extraction rules |
| `visit-finland-datahub-accommodation/scripts/` | Retrieval, parsing, validation, and export |
| `runs/` | Isolated run workspaces and output artifacts |

## Workflow diagram

```mermaid
flowchart TD
    A([Start preparation]) --> B[Load workflow instructions]
    B --> C[Validate request]
    C --> D[Parse uploaded documents]
    D --> E[Fetch seed pages]
    E --> F[Read seed evidence pages]
    F --> G[Select relevant same-site pages]
    G --> H[Fetch selected pages]
    H --> I[Read selected evidence pages]
    I --> J{Recovery fetch required?}
    J -->|Yes| G
    J -->|No| K[Determine product scope]
    K --> L[Record scope decision]
    L --> M[Construct every schema field]
    M --> N[Validate extraction]
    N --> O{Extraction valid?}
    O -->|No| P[Repair reported defects]
    P --> Q[Resubmit extraction]
    Q --> N
    O -->|Yes| R[Write review report]
    R --> S[Build canonical JSON]
    S --> T[Export Excel]
    T --> U[Build source references]
    U --> V[Verify and promote outputs]
    V --> W([Review and approve record])
```

## Workflow steps

- Start preparation
- Load workflow instructions
- Validate request
- Parse uploaded documents
- Fetch seed pages
- Read seed evidence pages
- Select relevant same-site pages
- Fetch selected pages
- Read selected evidence pages
- Perform a recovery fetch, if required
- Determine product scope
- Record the scope decision
- Construct every schema field
- Validate extraction
- Repair reported defects, if required
- Resubmit repaired extraction
- Write the review report
- Build canonical JSON
- Export Excel
- Build source references
- Verify and promote outputs
- Review and approve the record

## Request workspace

```text
runs/<run-id>/
|-- input/
|   |-- request.json
|   `-- documents/
|-- work/
|   |-- source-manifest.json
|   |-- parsed-documents.json
|   |-- fetched-pages.json
|   |-- context-delivery.json
|   |-- pages/
|   |-- scope-decision.json
|   |-- extraction-draft.json
|   `-- staging-output/
`-- output/
    |-- result.json
    |-- canonical-product.json
    |-- result.xlsx
    |-- review-report.md
    |-- sources.json
    |-- run-manifest.json
    |-- scope-decision.json
    `-- approved-product.json
```

Output files are created only when applicable. Successful runs promote verified artifacts to `output/` and remove transient source content. `sources.json` contains sanitized metadata for cited websites and uploaded documents.

## Prerequisites

- Python 3.12 or compatible Python 3
- Bun and a Node.js version supported by Next.js 16
- Claude Code CLI available on `PATH`
- Microsoft Foundry access for the configured Claude model

Install dependencies:

```powershell
cd "C:\Users\h02317\Tools and apps\VisitFinland"
python -m pip install -r requirements.txt

cd frontend
bun install
```

## Environment

Create `.env` in the repository root:

```dotenv
CLAUDE_CODE_USE_FOUNDRY=1
ANTHROPIC_FOUNDRY_RESOURCE=<your-resource-name>
ANTHROPIC_FOUNDRY_API_KEY=<your-api-key>
ANTHROPIC_MODEL=claude-sonnet-5
MAX_CONCURRENT_RUNS=2
API_TIMEOUT_MS=600000
CLAUDE_CODE_MAX_RETRIES=2
DISABLE_TELEMETRY=1
```

Create `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010
```

Optimized workflow mode and nested Claude sessions are application defaults. Do not commit credentials.

## Run the application

Backend:

```powershell
cd "C:\Users\h02317\Tools and apps\VisitFinland"
python -m app.main --preflight
python -m uvicorn app.api:app --host 127.0.0.1 --port 8010
```

Frontend, in a second terminal:

```powershell
cd "C:\Users\h02317\Tools and apps\VisitFinland\frontend"
bun dev
```

Open <http://localhost:3000>. API documentation is available at <http://127.0.0.1:8010/docs>.

CLI:

```powershell
python -m app.main --website-url "https://example-hotel.fi"
```

Repeat `--website-url` and `--document` for multiple inputs. Avoid Uvicorn `--reload` on Windows.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/runs` | Start a run |
| `GET` | `/runs` | List runs |
| `GET` | `/runs/{run_id}` | Get status and artifacts |
| `GET` | `/runs/{run_id}/events` | Stream progress with SSE |
| `POST` | `/runs/{run_id}/cancel` | Cancel a run |
| `GET` | `/runs/{run_id}/artifacts/{name}` | Download an artifact |
| `POST` | `/runs/{run_id}/approve` | Save an approved record |
| `DELETE` | `/runs/{run_id}` | Delete a run |

Terminal statuses: `completed`, `scope_ambiguous`, `no_usable_sources`, `validation_failed`, `execution_failed`, `input_invalid`, `cancelled`, and `interrupted`.

## Test

```powershell
cd "C:\Users\h02317\Tools and apps\VisitFinland"
python -m pytest

cd frontend
bun run typecheck
bun run lint
bun run build
```

Default tests use fixtures and mocks; they do not call live websites or Foundry.

## Security and limitations

- Each run uses an isolated workspace and fixed artifact allowlist.
- Python controls agent-accessible paths, subprocess arguments, and file writes.
- Source content is untrusted and cannot override workflow instructions.
- URL validation blocks unsupported schemes, private networks, metadata targets, disallowed domains, and unsafe redirects.
- Retrieval uses static HTTP; it does not render JavaScript or access authenticated pages.
- The workflow supports Accommodation and Shops only.
- A run accepts up to 10 seed URLs, 25 selected or stored pages, and two expansion calls.
- Evidence uses lossless 44,000-character chunks, 52,000-character tool responses, and a 2,400,000-character run limit.
- Uploads are limited to 10 PDF or DOCX files, 20 MiB each, and 50 MiB total.
- OCR detection is supported; OCR processing is not.
- Image retrieval, general web search, exhaustive crawling, duplicate search, and automatic DataHub submission are not implemented.
- External links may be stored as values, but external content is not fetched or cited.
- Credentials are never included in prompts or artifacts.
