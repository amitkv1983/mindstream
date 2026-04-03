# Mindstream

> React-first YouTube Channel Monitoring and Transcript Intelligence Platform

## Status

This repository is being rebuilt as a React-first application platform following the architecture described in [`.context/project/idea-react-ingestion-platform.md`](.context/project/idea-react-ingestion-platform.md).

**Current phase:** `Idea → Approved` *(governance-tracked via `space_framework`)*

---

## Target Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | React (TypeScript) |
| Backend API | FastAPI (Python 3.10+) |
| Worker | Background job processor (Python) |
| Database | PostgreSQL |
| Vector Search | pgvector / Chroma |

### Key Capabilities (Planned)

1. **Monitored Channels** — register YouTube channels; discover only new videos on each run
2. **Single Video Ingestion** — submit one video URL for immediate processing
3. **Batch Ingestion** — paste or upload multiple URLs for bulk onboarding
4. **Transcript Viewer** — browse transcripts with timestamps and segment-level visibility
5. **Summaries and Retrieval** — RAG-ready indexing over processed content

---

## Repository Layout

```
.context/          # Project governance documents (ADRs, sprint plans, decisions)
.github/           # GitHub workflows, issue templates, PR template, CODEOWNERS
POC/P_01/          # Archived proof-of-concept (Streamlit/Python — reference only)
```

---

## Governance

All work follows the [`space_framework`](https://github.com/nsin08/space_framework) SDLC:

- State machine: `Idea → Approved → Ready → In Progress → In Review → Done → Released`
- Stories must be `state:ready` before implementation begins
- PRs must link to exactly one story (`Closes #<id>`)
- Only CODEOWNER [@amitkv1983](https://github.com/amitkv1983) merges PRs
- All enforcement is automated via `.github/workflows/`

See [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for full agent and contributor guidance.

---

## Reference Implementation

The previous Streamlit-based CLI proof-of-concept is archived at [`POC/P_01/`](POC/P_01/).  
It demonstrates the core ingestion, transcript, summarization, and clustering logic that will be selectively reused in the new platform.

---

## Contributors

| Role | GitHub |
|------|--------|
| CODEOWNER / Requester | [@amitkv1983](https://github.com/amitkv1983) |
| Tech Lead / PM | [@nsin08](https://github.com/nsin08) |
