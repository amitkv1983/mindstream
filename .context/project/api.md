# Mindstream API

Base path:

```text
/api/v1
```

All protected routes require a bearer token.

## Auth

### POST /auth/google
Exchange Google ID token for app session token.

#### Request

```json
{
  "google_id_token": "string"
}
```

#### Response

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "amit@example.com",
    "name": "Amit Verma"
  }
}
```

## Me / Account

### GET /me
Get current user profile.

### Response

```json
{
  "id": "uuid",
  "email": "amit@example.com",
  "name": "Amit Verma",
  "created_at": "2026-03-19T10:00:00Z"
}
```

### DELETE /me
Request account deletion.

### Response

```json
{
  "message": "Account deletion requested"
}
```

## Workspaces

### GET /workspaces
List all workspaces for current user.

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "AI Research",
      "status": "active",
      "source_count": 3,
      "video_count": 42,
      "max_videos": 100,
      "last_sync_at": "2026-03-19T08:00:00Z",
      "last_active_at": "2026-03-19T09:00:00Z"
    }
  ]
}
```

### POST /workspaces
Create a workspace and optionally attach initial sources.

#### Request

```json
{
  "name": "AI Research",
  "sources": [
    "https://www.youtube.com/@lexfridman",
    "https://www.youtube.com/@karpathy"
  ]
}
```

#### Response

```json
{
  "id": "uuid",
  "name": "AI Research",
  "status": "syncing",
  "source_count": 2,
  "video_count": 0,
  "max_videos": 100,
  "job_id": "uuid"
}
```

### GET /workspaces/{workspace_id}
Get workspace detail.

#### Response

```json
{
  "id": "uuid",
  "name": "AI Research",
  "status": "active",
  "max_videos": 100,
  "video_count": 42,
  "source_count": 3,
  "last_sync_at": "2026-03-19T08:00:00Z",
  "last_active_at": "2026-03-19T09:00:00Z",
  "health": {
    "indexed_videos": 42,
    "failed_videos": 3,
    "missing_transcripts": 5
  }
}
```

### PATCH /workspaces/{workspace_id}
Update workspace metadata.

#### Request

```json
{
  "name": "AI Research Daily"
}
```

### POST /workspaces/{workspace_id}/pause
Pause background processing for workspace.

### POST /workspaces/{workspace_id}/resume
Resume background processing and queue refresh.

#### Response

```json
{
  "id": "uuid",
  "status": "syncing",
  "job_id": "uuid"
}
```

### DELETE /workspaces/{workspace_id}
Delete workspace and associated data.

## Sources

### GET /workspaces/{workspace_id}/sources
List workspace sources.

#### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Lex Fridman",
      "type": "channel",
      "source_url": "https://www.youtube.com/@lexfridman",
      "status": "active",
      "video_count": 12,
      "last_sync_at": "2026-03-19T08:00:00Z"
    }
  ]
}
```

### POST /workspaces/{workspace_id}/sources
Add source and queue source sync.

#### Request

```json
{
  "source_url": "https://www.youtube.com/@fireship"
}
```

#### Response

```json
{
  "id": "uuid",
  "name": "Fireship",
  "status": "syncing",
  "job_id": "uuid"
}
```

### DELETE /workspaces/{workspace_id}/sources/{source_id}
Remove source from future sync while preserving existing indexed data.

## Videos

### GET /workspaces/{workspace_id}/videos
List videos in workspace.

#### Query Params
- `status`
- `source_id`
- `limit`
- `cursor`

#### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "youtube_video_id": "abc123",
      "title": "GPT Explained",
      "channel_name": "Andrej Karpathy",
      "published_at": "2026-03-16T10:00:00Z",
      "duration_sec": 1800,
      "status": "indexed",
      "transcript_status": "available",
      "summary_status": "done"
    }
  ],
  "next_cursor": null
}
```

### GET /workspaces/{workspace_id}/videos/{video_id}
Get video detail.

#### Response

```json
{
  "id": "uuid",
  "youtube_video_id": "abc123",
  "title": "GPT Explained",
  "channel_name": "Andrej Karpathy",
  "published_at": "2026-03-16T10:00:00Z",
  "duration_sec": 1800,
  "status": "indexed",
  "transcript_status": "available",
  "summary_status": "done",
  "summary": {
    "topics": ["LLM training", "scaling laws"],
    "bullets": [
      "Scaling laws matter",
      "Data quality is critical"
    ],
    "notable_claims": [
      "Better data can outperform bigger models"
    ],
    "confidence": 0.83
  }
}
```

## Chat / Query

### POST /workspaces/{workspace_id}/chat
Ask a question against a workspace.

#### Request

```json
{
  "question": "What did Karpathy say about LLM training?"
}
```

#### Response

```json
{
  "answer": "Karpathy emphasized that LLM training depends heavily on data quality and predictable scaling behavior.",
  "bullets": [
    "Data quality matters as much as model scale",
    "Training cost rises sharply with scale"
  ],
  "sources": [
    {
      "video_id": "uuid",
      "youtube_video_id": "abc123",
      "title": "GPT Explained",
      "timestamp_sec": 750,
      "timestamp_label": "12:30",
      "url": "https://youtube.com/watch?v=abc123&t=750s"
    }
  ],
  "meta": {
    "workspace_id": "uuid",
    "fallback_used": true
  }
}
```

## Insights

### GET /workspaces/{workspace_id}/insights
Get latest insights for workspace.

#### Response

```json
{
  "workspace_id": "uuid",
  "updated_at": "2026-03-19T08:00:00Z",
  "what_is_new": [
    "GPT-5 rumors are gaining traction",
    "AI agents are moving toward autonomous workflows"
  ],
  "key_takeaways": [
    "Data quality is becoming more important than scale",
    "Open-source models continue to close the gap"
  ],
  "worth_your_attention": [
    {
      "video_id": "uuid",
      "youtube_video_id": "abc123",
      "title": "GPT Explained",
      "timestamp_sec": 750,
      "timestamp_label": "12:30",
      "url": "https://youtube.com/watch?v=abc123&t=750s",
      "note": "Karpathy discussed the relationship between data quality and model performance."
    }
  ]
}
```

## Notifications

### POST /notifications/devices
Register or update device token.

#### Request

```json
{
  "device_token": "string",
  "platform": "android"
}
```

### PATCH /notifications/preferences
Update notification preferences.

#### Request

```json
{
  "insight_notifications_enabled": true
}
```

## Jobs

### GET /jobs/{job_id}
Get async job status.

#### Response

```json
{
  "id": "uuid",
  "type": "workspace_initial_sync",
  "status": "running",
  "summary": {
    "discovered": 18,
    "indexed": 12,
    "failed": 2,
    "missing_transcripts": 4
  }
}
```

## Standard Error Shape

```json
{
  "error": {
    "code": "WORKSPACE_LIMIT_REACHED",
    "message": "This workspace has reached its indexing limit."
  }
}
```

## Standard Error Codes
- UNAUTHORIZED
- FORBIDDEN
- WORKSPACE_NOT_FOUND
- INVALID_SOURCE_URL
- WORKSPACE_LIMIT_REACHED
- SOURCE_ALREADY_EXISTS
- NO_INDEXED_DATA_YET
- RATE_LIMITED
- INTERNAL_ERROR
