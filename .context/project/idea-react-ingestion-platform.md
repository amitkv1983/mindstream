# Idea: Mindstream React-Based YouTube Monitoring and Transcript Intelligence Platform

## Status

- Current state: `Idea`
- Intended framework path: `Idea -> Approved -> Ready -> In Progress -> In Review -> Done -> Released`
- Framework alignment: drafted to support decomposition into architecture, stories, and acceptance criteria under `space_framework`

## Source Template

This document is based on the issue template at:

- `.github/ISSUE_TEMPLATE/01-idea.md`

It is intentionally expanded into a durable project artifact so it can later be translated into:

- approval-ready issue content
- architecture and ADR documents
- implementation-ready requirements
- backlog stories with measurable acceptance criteria

---

# 💡 Idea: Build a React-First Mindstream Platform for YouTube Channel Monitoring, Video Ingestion, and Transcript Intelligence

## Business Problem

Mindstream started as a proof-of-concept for discovering YouTube videos, fetching transcripts, summarizing content, and generating reports. That proof-of-concept demonstrates the core technical feasibility, but it is not yet structured as a production-ready product.

The current repository has three key limitations for the intended product direction:

1. The user experience is centered around Streamlit, which is useful for demos but not ideal for a scalable, maintainable product UI with robust channel management, transcript browsing, user workflows, and future multi-user capabilities.
2. The system does not yet provide proper first-class management of channels, videos, pipeline runs, and transcript viewing. Several workflows still depend on ad hoc text input and file-based persistence.
3. The architecture mixes proof-of-concept concerns with emerging product concerns, which makes it harder to evolve into a maintainable application with clear separation between frontend, backend API, and background processing.

The users who would benefit from solving this problem include:

- operators who want to continuously monitor selected YouTube channels
- analysts who want to inspect new videos and read transcripts quickly
- decision-makers who need summarized intelligence from batches of videos
- future product users who may need project-based organization, search, and retrieval over transcripts

Without a stronger architecture, Mindstream risks becoming harder to evolve, harder to test, and slower to convert from prototype into a real application.

## Proposed Solution

Create a React-first version of Mindstream as a proper application platform, while preserving and selectively reusing the useful ingestion concepts from the current repository.

The proposed product should support three primary ingestion modes:

1. Monitored channels
   - users can register YouTube channels as managed assets
   - the system can discover new videos on demand and later on a schedule
   - only newly discovered videos are processed

2. Single video ingestion
   - users can submit one YouTube video URL for immediate processing
   - useful for ad hoc investigations and manual intake

3. Batch ingestion
   - users can submit multiple video or channel URLs through pasted input or uploaded files
   - useful for bulk onboarding and analyst workflows

The proposed product should also support first-class content management:

- channel management with add/edit/enable/disable/status operations
- video inventory with discovery status, transcript status, and summary status
- transcript viewer with timestamps and segment-level visibility
- summaries and retrieval-ready indexing for downstream RAG or reporting workflows

From an architecture perspective, the recommended direction is to move toward:

- React frontend instead of Streamlit
- API-backed application architecture instead of UI-coupled orchestration
- persistent structured storage for channels, videos, transcripts, and runs
- background processing for ingestion and enrichment stages

The most likely target architecture is:

- frontend: React application
- backend: API service for domain operations
- worker: background job processor for discovery, transcript fetch, chunking, summarization, embedding, and indexing
- persistence: relational database as source of truth
- retrieval: vector search integrated with the persistence strategy or a clearly bounded vector subsystem

## Product Goals

The product should enable a user to:

1. Register and manage YouTube channels that are monitored over time.
2. Run a pipeline that discovers only new videos since the last successful run.
3. Ingest one-off videos without requiring them to belong to a saved monitored channel.
4. Upload batches of custom source files and process them consistently.
5. Browse channels, videos, transcripts, and processing status in a structured UI.
6. View transcript content in a readable way with metadata and timestamps.
7. Search and ask questions over processed content in future phases.

## Non-Goals for Initial Delivery

To keep the first implementation focused, the following should not be part of the first release unless explicitly approved later:

- multi-tenant enterprise permissions
- billing and subscription management
- automated publishing to external channels
- complex human-in-the-loop editorial workflows
- mobile applications
- full content moderation platform features

## Success Criteria

The initiative will be considered successful when the following are true:

1. A user can add, edit, enable, disable, and list monitored YouTube channels through the application without direct file edits.
2. A pipeline run can process monitored channels and ingest only newly discovered videos, with video-level statuses persisted and visible in the UI.
3. A user can ingest a single YouTube video URL and a batch input file through the product UI, and both paths produce the same persisted video and transcript records.
4. A user can open any processed video and view transcript content, metadata, and summary in a dedicated transcript-view experience.
5. The architecture clearly separates frontend, API, and background processing responsibilities, with defined contracts that support future scaling and testing.
6. The implementation is decomposed into approval-ready stories with measurable acceptance criteria and traceable evidence mapping per the framework.

## Business Value

- Impact: High
- Urgency: High
- Effort estimate: Large

### Why This Matters

This work converts Mindstream from a proof-of-concept into a product foundation. The value is not only in better UI, but in making the system governable, extendable, and credible for continued investment.

Expected value includes:

- faster analyst workflows through managed discovery and transcript visibility
- less manual effort through recurring channel monitoring and deduped ingestion
- higher implementation confidence through clear architecture boundaries
- easier future extension into search, RAG, reporting, and collaboration features
- better alignment with a governed SDLC using `space_framework`

## Stakeholders

- Requester: @amitkv1983
- Approver: @nsin08
- Sponsor: @amitkv1983
- Technical owner candidate: Architect or Tech Lead to be confirmed during `Approved -> Ready`
- Implementation roles likely involved:
  - Architect
  - Implementer
  - Reviewer

## Architectural Direction

### Decision Framing

This idea should be treated as both a product idea and an architecture reset decision.

The key architectural question is:

Should Mindstream continue evolving inside the current Streamlit-first repository, or should the team create a new React-first product codebase and selectively port proven ingestion logic?

### Recommended Direction

Recommendation: create a new React-first product codebase and treat the current repository as a reference implementation plus migration source.

### Rationale

The current repository is valuable as a working proof-of-concept, but it is not an ideal long-term host for the intended product because:

- the UI architecture is Streamlit-centric
- the current orchestration is coupled to session-state-driven interaction
- the persistence strategy is still transitional
- product concepts such as channels, videos, runs, and transcript views are not yet modeled as first-class application entities
- future needs such as richer frontend UX, API contracts, and worker-based orchestration fit a different system shape

### Reuse Strategy

The following assets are strong candidates for reuse after cleanup:

- YouTube source parsing and discovery logic
- transcript retrieval logic
- chunking approach
- summarization patterns
- retrieval concepts

The following areas should likely be re-designed rather than directly carried over:

- Streamlit UI
- UI-led orchestration logic
- current CLI entrypoint
- mixed file-based persistence patterns
- loosely connected report-generation flows

## Proposed Target Architecture

### System Components

1. Web frontend
   - React-based UI
   - channel management
   - ingestion controls
   - video library
   - transcript viewer
   - future search and chat surfaces

2. API service
   - owns domain entities and validation
   - exposes endpoints for channels, videos, transcripts, runs, and ingestion requests
   - returns durable state for frontend rendering

3. Worker service
   - performs discovery
   - fetches transcripts
   - chunks and summarizes transcript content
   - generates embeddings
   - updates status and run records

4. Persistence layer
   - relational source of truth for business entities
   - vector storage strategy aligned with search and RAG goals
   - artifact storage for raw transcript payloads if needed

### Candidate Technology Direction

The exact stack should be validated during architecture work, but the leading direction is:

- frontend: React with a production-ready framework such as Next.js
- API: Python backend such as FastAPI, to maximize reuse of Python ingestion logic
- worker: Python background worker
- database: PostgreSQL
- vector strategy: `pgvector` or an explicitly justified separate vector subsystem
- queueing: Redis-backed job queue or equivalent

This should become an ADR during the `Approved -> Ready` phase rather than being treated as implicitly final from this idea alone.

## Core Domain Model

The future implementation should likely define first-class entities such as:

- Channel
  - source URL
  - canonical YouTube channel ID
  - title
  - active/inactive status
  - last checked time
  - project association

- Video
  - canonical YouTube video ID
  - title
  - channel reference when applicable
  - discovery source
  - published date
  - processing statuses

- Transcript
  - raw transcript payload
  - normalized full text
  - language if known
  - transcript availability state

- TranscriptChunk
  - chunk text
  - order index
  - timestamps
  - embedding

- VideoSummary
  - summary text
  - extracted bullets
  - topics
  - embedding if needed

- PipelineRun
  - trigger source
  - started/finished timestamps
  - outcome status
  - error details
  - per-stage counters

## Key User Workflows

### Workflow A: Monitor Channels

1. User adds one or more YouTube channels.
2. User marks channels active for monitoring.
3. User runs monitor-now.
4. System discovers videos for active channels.
5. System filters out already processed or already known videos.
6. System ingests only new videos.
7. User sees run status and new content in the library.

### Workflow B: Ingest Single Video

1. User pastes a single YouTube video URL.
2. System validates and normalizes the URL.
3. System creates a pipeline run for a one-off video ingest.
4. Transcript, summary, and statuses are persisted.
5. User can open the transcript viewer for that video.

### Workflow C: Ingest Batch File

1. User uploads a file containing multiple URLs.
2. System parses and validates each line.
3. System creates a batch ingest run.
4. Each valid source is normalized into channels or videos.
5. User sees per-item results, failures, and final statuses.

### Workflow D: View Transcript

1. User opens a processed video from the library.
2. User sees video metadata, transcript state, and summary state.
3. User reads transcript segments with timestamps.
4. User can inspect chunks, summary, and future search context.

## Scope Boundaries for Phase 1

Phase 1 should focus on the smallest useful product foundation:

- React frontend with essential management views
- channel registry
- video registry
- monitored channel discovery
- single video ingest
- batch URL/file ingest
- transcript persistence
- transcript viewer
- summary generation and status display

Phase 1 may defer:

- advanced semantic search UX
- cross-video intelligence reports
- scheduler automation beyond basic monitor-now
- team collaboration features
- role-based access control beyond minimal internal use

## Risks and Open Questions

### Risks

- architecture churn if the new system starts before the target domain model is aligned
- ingestion instability due to transcript availability limits and YouTube-side variability
- premature overinvestment in AI summarization before the ingestion and management foundation is stable
- complexity creep if reporting, chat, and channel management are all built at once

### Open Questions

1. Should the first release support authentication, or remain single-operator/internal-only?
2. Should vectors live in the primary database or remain in a separate vector store?
3. Should the first release include scheduled monitoring, or only manual monitor-now runs?
4. What level of transcript fidelity is required in the viewer: raw segments only, normalized full text, or both?
5. Does the team want a migration path from current `data/` artifacts into the new platform, or a fresh start?

These should be resolved during the `Approved -> Ready` phase and captured in ADRs or story prerequisites.

## Delivery Recommendation

This idea should not move directly into implementation. It should first produce the following governed artifacts:

1. Approval decision on repository strategy
   - continue in current repo versus create a new repo

2. Architecture brief or ADR set
   - frontend framework
   - backend architecture
   - worker model
   - persistence strategy

3. Initial epic decomposition
   - channel management
   - ingestion API and worker pipeline
   - video library
   - transcript viewer
   - run tracking

4. Story set with acceptance criteria
   - suitable for `state:ready`

## Suggested Epic Breakdown

- Epic 1: Product foundation and architecture setup
- Epic 2: Channel registry and monitoring workflows
- Epic 3: Single-video and batch ingestion
- Epic 4: Video library and transcript viewer
- Epic 5: Summaries, indexing, and retrieval foundation

## Additional Context

Relevant references:

- Current repository: `mindstream`
- Idea template: `.github/ISSUE_TEMPLATE/01-idea.md`
- Governance instructions: `.github/copilot-instructions.md`
- Framework repository: `https://github.com/nsin08/space_framework`

Framework cues used in this draft:

- enforced state machine
- separation of idea, approval, ready, and implementation work
- human approval gates
- later evidence mapping through story and PR workflows

## Ready-for-Translation Notes

This document is ready to be translated into:

- a GitHub Idea issue
- one or more ADRs
- an architecture decision on repo strategy
- epics and stories with measurable acceptance criteria

It is not yet a `Ready` implementation artifact. Approval and architecture clarification are still required.

---

**Next Step:** Seek client or sponsor decision on whether to create a new React-first codebase or explicitly continue in the existing repository, then convert that decision into approved architecture work under the framework.
