# Mindstream Architecture

## Overview

Mindstream is a mobile-first YouTube intelligence platform that ingests video content, processes transcripts, generates summaries, stores embeddings, and enables semantic search via RAG.

The system is designed to be:
- Cloud-agnostic
- Terraform-managed
- Cost-controlled
- Mobile-first
- Async and scalable

## High-Level Architecture

```text
Mobile App (Flutter: Android / iOS)
        ↓
Backend API (FastAPI)
        ↓
-------------------------------------------------
| Auth | Workspace | Sources | Videos | Chat API |
-------------------------------------------------
        ↓
Queue / Task Broker (Redis)
        ↓
Workers
-------------------------------------------------
| Discovery | Transcript | Summary | Embed |
| Insights  | Notifications            |
-------------------------------------------------
        ↓
Storage Layer
-------------------------------------------------
| PostgreSQL | Object Storage | Vector DB |
-------------------------------------------------
        ↓
AI Layer
-------------------------------------------------
| Embeddings | RAG Answer Model | Reranker |
-------------------------------------------------
```

## Core Components

### 1. Mobile App
Built in Flutter for Android and iOS from a single codebase.

Responsibilities:
- Google login
- Workspace management
- Source management
- Video/source visibility
- Insights screen
- Chat / ask questions
- Notification handling

### 2. Backend API
Built with FastAPI.

Responsibilities:
- Authentication and session handling
- Workspace CRUD
- Source CRUD
- Video listing
- Chat / RAG endpoint
- Insights retrieval
- Notification token registration
- Workspace control actions (pause/resume/delete)

### 3. Worker Layer
Runs asynchronous jobs outside the API request path.

Worker responsibilities:
- Discover recent videos
- Enforce source/workspace caps
- Fetch transcripts
- Summarize transcripts
- Create chunks + embeddings
- Generate insights
- Trigger notifications

### 4. Data Layer

#### PostgreSQL
Source of truth for:
- users
- devices
- workspaces
- sources
- videos
- transcripts metadata
- summaries metadata
- job records
- insights metadata
- notification preferences

#### Object Storage
Stores:
- raw transcript JSON
- generated artifacts
- future exports/reports

Must be abstracted behind a storage adapter so any cloud provider can be used.

#### Vector DB
Stores:
- transcript chunk embeddings
- summary embeddings

Used only for semantic retrieval, not as the system of record.

## RAG Architecture

### Query Flow

```text
User Question
    ↓
Validate workspace access
    ↓
Create query embedding
    ↓
Search summary embeddings in workspace
    ↓
Select candidate videos
    ↓
Search chunk embeddings in workspace
    ↓
Fallback chunk search if filtered retrieval is weak
    ↓
Merge + dedupe + rerank
    ↓
Build prompt
    ↓
Generate grounded answer
    ↓
Return answer + sources + timestamps
```

### RAG Rules
- Always scope retrieval to the active workspace
- Summary search guides retrieval, but does not hard-block fallback retrieval
- Sources are mandatory in responses
- If context is insufficient, respond honestly
- Keep context limited to avoid token overflow

## Processing Rules

### Source Limits
- Max 30 videos per source
- Only videos from last 90 days

### Workspace Limits
- Max indexed videos per workspace
- If workspace is at capacity, stop ingesting new videos
- Partial ingestion allowed if some slots remain

### Activity Rules
- New workspace gets a 24-hour grace period
- Active workspaces are synced automatically
- Inactive workspaces are auto-paused after 7 days without activity
- Returning user reactivates sync

## Notifications
Push notifications use Firebase Cloud Messaging.

Triggers:
- New insights available
- New videos processed (optional later)
- Processing issues (optional later)

## Multi-Cloud Strategy

Mindstream is designed for single-cloud launch and multi-cloud portability.

Principles:
- All infra is Terraform-managed
- App code must not depend directly on cloud SDKs in business logic
- Storage, secrets, and AI providers should be accessed through adapters
- Runtime should remain container-based

## Deployment Strategy

### V1
- Single primary cloud
- Containerized API
- Containerized worker
- PostgreSQL
- Redis
- Vector DB
- Object storage
- FCM integration

### Future
- Secondary cloud support
- Managed vector database
- Paid LLM fallback
- Advanced monitoring and autoscaling

## Design Principles
- Postgres is the source of truth
- Vector DB is for retrieval only
- Long-running work must be asynchronous
- Workspace is the primary isolation boundary
- Cost control is a first-class feature
