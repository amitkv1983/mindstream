# Mindstream Roadmap

## Product Goal

Mindstream is a mobile-first AI product that watches YouTube for the user, keeps selected workspaces up to date, generates insights, and answers questions with grounded sources.

## Phase 0 — POC (Completed)

Completed outcomes:
- Proved end-to-end feasibility
- Tested transcript ingestion
- Tested summarization
- Tested embeddings
- Tested RAG chat behavior
- Validated the product concept

POC artifacts are not the production system.

## Phase 1 — Foundation

Goal:
- establish production repo structure
- setup backend, mobile, and infra foundations

Deliverables:
- backend skeleton
- Flutter app skeleton
- Docker-based local dev
- Terraform skeleton
- environment config strategy
- lightweight project governance docs

## Phase 2 — Auth + Workspaces

Goal:
- user login and workspace lifecycle

Deliverables:
- Google login
- session token handling
- create/list/get workspaces
- workspace settings basics
- workspace status support

Success state:
- user can sign in and create a workspace

## Phase 3 — Sources + Discovery

Goal:
- attach YouTube sources and discover candidate videos

Deliverables:
- add/remove source APIs
- YouTube source normalization
- recent video discovery
- enforce 30 videos / 90 days rule
- enforce workspace video cap
- persist source/video metadata

Success state:
- workspace shows sources and discovered videos

## Phase 4 — Async Processing Pipeline

Goal:
- process videos into indexed knowledge

Deliverables:
- queue + worker setup
- transcript fetch worker
- transcript object storage
- summary generation
- chunk generation
- embeddings storage
- idempotent processing
- retry handling

Success state:
- discovered videos move to indexed state

## Phase 5 — RAG Chat

Goal:
- deliver the core product experience

Deliverables:
- workspace-scoped query API
- summary-first retrieval
- filtered chunk retrieval
- fallback retrieval
- reranking
- answer generation
- source + timestamp output

Success state:
- user can ask a question and get a grounded answer with sources

## Phase 6 — Insights + Notifications

Goal:
- make the product proactive

Deliverables:
- insights generation from recent summaries
- “What’s New”, “Key Takeaways”, “Worth Your Attention”
- FCM device registration
- notification preferences
- insights-ready notification flow

Success state:
- user gets notified when fresh insight value exists

## Phase 7 — Sources, Videos, and Workspace Controls

Goal:
- transparency, trust, and operational control

Deliverables:
- source list UI/API
- video list UI/API
- per-video status visibility
- workspace limits visibility
- pause/resume workspace
- auto-pause after inactivity
- account safety actions

Success state:
- user can understand what data exists and what the system is doing

## Phase 8 — Stability and Launch Readiness

Goal:
- make the app launch-safe

Deliverables:
- polish key UX flows
- loading and empty states
- better error messaging
- observability basics
- privacy policy
- delete account flow
- store listing assets

Success state:
- app is ready for Play Store submission

## Operating Constraints

### Workspace Limits
- max videos per workspace
- hard stop when full
- partial ingestion allowed while slots remain

### Source Limits
- max 30 videos per source
- only last 90 days of content

### Activity Rules
- new workspace grace period: 24 hours
- active window: 7 days
- inactive workspaces auto-pause

### Cost Rules
- prefer Ollama/local or self-hosted generation in V1
- avoid reprocessing existing videos
- cache and reuse transcript/embedding artifacts

## Launch Definition of V1

Mindstream V1 is achieved when:
- user can sign in
- user can create a workspace
- user can add sources
- background processing indexes content automatically
- user can ask questions and get grounded answers with sources
- user can see insights
- user can receive notifications
- app is deployable and Play Store ready

## Post-V1 Priorities

- stronger reranking
- improved insight quality
- advanced trust features (source snippets)
- better analytics/monitoring
- multi-cloud deployment validation
- paid LLM fallback
- monetization and subscription controls
