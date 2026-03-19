# Mindstream Schema

## Storage Model

Mindstream uses three storage systems:

- **PostgreSQL**: source of truth and relational state
- **Vector DB**: semantic retrieval index
- **Object Storage**: raw artifacts and large blobs

## PostgreSQL Tables

### users

| field | type | notes |
|---|---|---|
| id | UUID PK | user id |
| email | TEXT UNIQUE | Google-auth email |
| name | TEXT | display name |
| created_at | TIMESTAMP | account creation |
| last_login_at | TIMESTAMP | last login |

### devices

| field | type | notes |
|---|---|---|
| id | UUID PK | device row id |
| user_id | UUID FK -> users.id | owner |
| device_token | TEXT | FCM/APNS token |
| platform | TEXT | android / ios |
| created_at | TIMESTAMP | registration time |
| updated_at | TIMESTAMP | token refresh time |

### workspaces

| field | type | notes |
|---|---|---|
| id | UUID PK | workspace id |
| user_id | UUID FK -> users.id | owner |
| name | TEXT | workspace name |
| status | TEXT | active / syncing / paused / partial / error / deleted |
| max_videos | INT | workspace cap |
| max_sources | INT | source cap |
| current_video_count | INT | indexed videos |
| current_source_count | INT | attached sources |
| last_active_at | TIMESTAMP | used for auto-pause |
| last_sync_at | TIMESTAMP | latest successful sync |
| created_at | TIMESTAMP | created time |
| updated_at | TIMESTAMP | updated time |

### sources

| field | type | notes |
|---|---|---|
| id | UUID PK | source id |
| workspace_id | UUID FK -> workspaces.id | workspace |
| type | TEXT | channel / video |
| source_url | TEXT | original URL |
| canonical_source_id | TEXT | normalized source id |
| title | TEXT | source display title |
| status | TEXT | active / syncing / failed / removed |
| last_sync_at | TIMESTAMP | last source sync |
| consecutive_failures | INT | retry control |
| created_at | TIMESTAMP | added time |
| updated_at | TIMESTAMP | updated time |

### videos

| field | type | notes |
|---|---|---|
| id | UUID PK | internal video row id |
| workspace_id | UUID FK -> workspaces.id | workspace scope |
| source_id | UUID FK -> sources.id | source |
| youtube_video_id | TEXT | external video id |
| title | TEXT | video title |
| channel_name | TEXT | display channel |
| published_at | TIMESTAMP | publish date |
| duration_sec | INT | duration |
| status | TEXT | discovered / processing / indexed / failed |
| transcript_status | TEXT | pending / available / missing / error |
| summary_status | TEXT | pending / done / error |
| processing_retry_count | INT | worker retry count |
| created_at | TIMESTAMP | created time |
| updated_at | TIMESTAMP | updated time |

### transcripts

| field | type | notes |
|---|---|---|
| id | UUID PK | transcript row id |
| video_id | UUID FK -> videos.id | video |
| storage_path | TEXT | object storage path |
| segment_count | INT | number of segments |
| language | TEXT | if available |
| created_at | TIMESTAMP | stored time |

### summaries

| field | type | notes |
|---|---|---|
| id | UUID PK | summary row id |
| video_id | UUID FK -> videos.id | video |
| topics | JSONB | extracted topics |
| bullets | JSONB | concise bullets |
| notable_claims | JSONB | claims / highlights |
| confidence | FLOAT | optional confidence |
| created_at | TIMESTAMP | generated time |
| updated_at | TIMESTAMP | updated time |

### vector_metadata

| field | type | notes |
|---|---|---|
| id | UUID PK | metadata row id |
| workspace_id | UUID FK -> workspaces.id | retrieval scope |
| video_id | UUID FK -> videos.id | owning video |
| embedding_kind | TEXT | chunk / summary |
| external_vector_id | TEXT | vector DB id |
| chunk_index | INT | sequence index |
| start_time | FLOAT | start seconds |
| end_time | FLOAT | end seconds |
| speaker | TEXT | optional speaker label |
| text_preview | TEXT | preview text |
| created_at | TIMESTAMP | created time |

### insights

| field | type | notes |
|---|---|---|
| id | UUID PK | insight row id |
| workspace_id | UUID FK -> workspaces.id | workspace |
| insight_type | TEXT | daily / sync |
| what_is_new | JSONB | list of new developments |
| key_takeaways | JSONB | list of takeaways |
| worth_your_attention | JSONB | list of notable moments |
| generated_at | TIMESTAMP | generation time |

### notifications

| field | type | notes |
|---|---|---|
| id | UUID PK | notification row id |
| user_id | UUID FK -> users.id | user |
| workspace_id | UUID FK -> workspaces.id | related workspace |
| type | TEXT | insights_ready / processing_issue / etc |
| payload | JSONB | structured payload |
| sent_at | TIMESTAMP | send time |
| created_at | TIMESTAMP | creation time |

### notification_preferences

| field | type | notes |
|---|---|---|
| user_id | UUID PK FK -> users.id | user |
| insight_notifications_enabled | BOOLEAN | on/off |
| updated_at | TIMESTAMP | preference update |

### jobs

| field | type | notes |
|---|---|---|
| id | UUID PK | job id |
| workspace_id | UUID FK -> workspaces.id | workspace scope |
| source_id | UUID NULL FK -> sources.id | optional source scope |
| video_id | UUID NULL FK -> videos.id | optional video scope |
| job_type | TEXT | workspace_initial_sync / workspace_incremental_sync / transcript_fetch / summarize / embed / insights / notify |
| status | TEXT | pending / running / completed / failed |
| payload | JSONB | job context |
| summary | JSONB | counts/results |
| error_message | TEXT | failure message |
| created_at | TIMESTAMP | queued time |
| started_at | TIMESTAMP | actual start |
| completed_at | TIMESTAMP | completion time |

## Vector DB Metadata

### Chunk Embeddings

```json
{
  "workspace_id": "uuid",
  "video_id": "uuid",
  "youtube_video_id": "abc123",
  "video_title": "GPT Explained",
  "channel_name": "Andrej Karpathy",
  "chunk_index": 3,
  "start_time": 750.0,
  "end_time": 810.0,
  "speaker": "Andrej Karpathy"
}
```

### Summary Embeddings

```json
{
  "workspace_id": "uuid",
  "video_id": "uuid",
  "youtube_video_id": "abc123",
  "video_title": "GPT Explained",
  "channel_name": "Andrej Karpathy"
}
```

## Object Storage Layout

```text
workspaces/{workspace_id}/
  transcripts/{youtube_video_id}.json
  artifacts/{artifact_name}.json
  exports/{export_name}.json
```

## Critical Rules

1. PostgreSQL is the system of record
2. Full transcripts are not stored inline in relational tables
3. Embeddings are not stored in PostgreSQL
4. Every major object must be workspace-scoped
5. Video processing must be idempotent
6. Vector metadata bridge must exist for trust, source display, and retrieval debugging
