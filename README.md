# Visit Finland DataHub Accommodation Assistant

This application prepares an evidence-grounded Visit Finland DataHub
Accommodation record from one or more company website URLs and optional
PDF/DOCX documents. It produces reviewable JSON, Excel, and Markdown artifacts;
it does not submit data to Visit Finland DataHub.

The application has one workflow: a continuous Claude Agent SDK session with
seven typed tools. Claude makes semantic decisions such as link selection,
product scope, extraction, conflict handling, repair, and report prose.
Deterministic Python code owns retrieval boundaries, file paths, validation,
artifact generation, and execution budgets.

## Architecture

```text
Next.js frontend (port 3000)
        |
        | HTTP + SSE
        v
FastAPI service (port 8010)
        |
        v
Claude Agent SDK runner
        |
        | seven typed in-process tools
        v
Stored evidence + deterministic validation
        |
        v
JSON + canonical JSON + Excel + review report
```

The seven agent tools are `load_skill`, `prepare_sources`,
`read_context_page`, `fetch_selected_pages`, `record_scope`, `submit_extraction`, and
`finalize_outputs`. Generic shell, filesystem, search, and web-fetch tools
are unavailable to the agent.

Important components:

| Path | Responsibility |
| --- | --- |
| `app/api.py` | FastAPI runs, uploads, polling, SSE, artifacts, cancellation, approval, and deletion |
| `app/main.py` | CLI entry point and Foundry preflight |
| `app/runner.py` | Stable production runner entry point |
| `app/runner_optimized.py` | Typed-tool Claude Agent SDK session |
| `app/agent_tools.py` | Tool contracts, budgets, evidence packaging, validation, and finalization |
| `app/finalize.py` | Terminal classification and artifact promotion |
| `visit-finland-datahub-accommodation/SKILL.md` | Authoritative agent workflow and invariants |
| `visit-finland-datahub-accommodation/scripts/` | Deterministic parsing, retrieval, validation, canonicalization, and export |
| `frontend/` | Next.js user interface |
| `runs/` | Isolated request workspaces and generated artifacts |

## Workflow and limits

The runner loads the Skill, validates inputs, parses documents, retrieves seed
pages, and exposes the complete evidence and ranked same-site link inventory
through sequential context pages. Scope and extraction are blocked until all
currently queued pages have been delivered. The runner then records one
product-scope decision, validates a complete extraction with at most one
repair, and finalizes the artifact set.

Current limits are 10 seed URLs, 20 selected links on the primary retrieval
call, five on the recovery call, 25 selected links and 25 stored pages per run,
two expansion calls, five concurrent requests, 15 seconds per request, 60
seconds per retrieval stage, and 5 MiB per fetched page. Parsed evidence is
split losslessly into chunks of at most 44,000 characters and packed into
context pages below a 52,000-character serialized-response guard. Up to
2,400,000 serialized context characters may be queued per run; a larger input
fails explicitly instead of being silently truncated. All discovered
candidate links are available through the same pagination mechanism.
Uploads are limited to 10 PDF/DOCX files, 20 MiB each, and 50 MiB total.

Retrieval is static HTTP only. It does not execute JavaScript, access
authenticated pages, or perform an exhaustive crawl.

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
    `-- run-manifest.json
```

Successful artifacts are promoted to `output/`. Intermediate and diagnostic
files remain under `work/`.

## Prerequisites

- Python 3.12 or a compatible Python 3 version
- Bun and a Node.js version supported by Next.js 16
- Claude Code CLI on `PATH`
- Access to the configured Claude model through Microsoft Foundry

Install dependencies:

```powershell
cd C:\Users\h02317\Tools and apps\VisitFinland
python -m pip install -r requirements.txt

cd frontend
bun install
```

## Environment

Create or update `.env` in the repository root:

```dotenv
CLAUDE_CODE_USE_FOUNDRY=1
ANTHROPIC_FOUNDRY_RESOURCE=<your-resource-name>
ANTHROPIC_FOUNDRY_API_KEY=<your-api-key>
ANTHROPIC_MODEL=claude-sonnet-5
MAX_CONCURRENT_RUNS=2
```

Never commit the real API key. Optimized execution and nested-session support
are application defaults; no workflow or nested-session environment variables
are required.

The frontend uses `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010
```

## Run the application

Use two terminals. Do not use Uvicorn `--reload` on this Windows setup; its
child process can fail before the runner starts.

Backend:

```powershell
cd C:\Users\h02317\Tools and apps\VisitFinland

# Optional connectivity check
python -m app.main --preflight

python -m uvicorn app.api:app --host 127.0.0.1 --port 8010
```

Frontend:

```powershell
cd C:\Users\h02317\Tools and apps\VisitFinland\frontend
bun dev
```

Open <http://localhost:3000>. API documentation is at
<http://127.0.0.1:8010/docs>.

The CLI can run without the frontend:

```powershell
python -m app.main --website-url "https://example-hotel.fi"
```

Repeat `--website-url` and `--document` to provide multiple inputs.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/runs` | Start a run |
| `GET` | `/runs` | List runs |
| `GET` | `/runs/{run_id}` | Poll status and artifacts |
| `GET` | `/runs/{run_id}/events` | Stream durable progress using SSE |
| `POST` | `/runs/{run_id}/cancel` | Cancel a queued or active run |
| `GET` | `/runs/{run_id}/artifacts/{name}` | Download an allowed artifact |
| `POST` | `/runs/{run_id}/approve` | Save a curator-edited approved record |
| `DELETE` | `/runs/{run_id}` | Delete a run workspace |

Terminal statuses are `completed`, `scope_ambiguous`,
`no_usable_sources`, `validation_failed`, `execution_failed`,
`input_invalid`, `cancelled`, and `interrupted`.

## Tests

```powershell
cd C:\Users\h02317\Tools and apps\VisitFinland
python -m pytest

cd frontend
bun run typecheck
bun run lint
bun run build
```

Ordinary tests use fixtures and mocks. Live Foundry or website checks are
explicit and are not part of the default test suite.

## Security and limitations

- Every run uses an isolated workspace.
- Python owns all agent-accessible paths, subprocess arguments, and writes.
- Source text is untrusted and cannot alter instructions or policies.
- URL validation blocks unsupported schemes, private/loopback/link-local/
  metadata targets, disallowed domains, and unsafe redirects.
- External links may be stored as literal values but external content is not
  fetched or cited.
- Artifact downloads use a fixed allowlist.
- Credentials are never put in prompts or run artifacts.
- Accommodation is the only supported product type.
- PDF OCR is detected but not performed.
- No general web search, browser rendering, duplicate search, or automatic
  DataHub submission is performed.
