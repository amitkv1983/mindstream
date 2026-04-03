# Mindstream Mobile - Implementation Checklist

This checklist is derived from:

- [mindstream-mobile-roadmap.md](/d:/AI/mindstream/.context/project/mindstream-mobile-roadmap.md)

It reflects the current repository state and is meant to be the working checklist for completing the local Mindstream mobile system step by step.

---

## Status Legend

- `[x]` Done
- `[-]` Partial
- `[ ]` Not started

---

## 1. Backend Foundation

- `[x]` FastAPI backend created
- `[x]` Dockerized backend created
- `[x]` SQLite persistence added
- `[x]` Docker volume persistence wired
- `[x]` Auto-create DB tables on startup
- `[x]` Health endpoint implemented
- `[x]` Channel creation endpoint implemented
- `[x]` Channel videos endpoint implemented
- `[x]` Video summarize endpoint implemented
- `[x]` Video summary retrieval endpoint implemented
- `[x]` Invalid `video_id` validation added
- `[x]` Basic backend logging added for:
  - channel created
  - video fetched
  - summary generated

Relevant files:

- [backend/app/main.py](/d:/AI/mindstream/backend/app/main.py)
- [backend/app/api/health.py](/d:/AI/mindstream/backend/app/api/health.py)
- [backend/app/api/channels.py](/d:/AI/mindstream/backend/app/api/channels.py)
- [backend/app/api/videos.py](/d:/AI/mindstream/backend/app/api/videos.py)
- [backend/app/api/summaries.py](/d:/AI/mindstream/backend/app/api/summaries.py)
- [backend/app/db/models.py](/d:/AI/mindstream/backend/app/db/models.py)
- [backend/app/db/session.py](/d:/AI/mindstream/backend/app/db/session.py)

---

## 2. Infrastructure / Local Dev

- `[x]` Root `docker-compose.yml` includes backend service
- `[x]` Backend data persisted to `./backend/data`
- `[x]` Backend healthcheck added in Compose
- `[x]` `.dockerignore` added
- `[x]` `.gitignore` updated for backend DB artifacts
- `[x]` Local backend reachable from mobile over LAN
- `[x]` Backend `/health` verified from mobile device

Relevant files:

- [docker-compose.yml](/d:/AI/mindstream/docker-compose.yml)
- [.dockerignore](/d:/AI/mindstream/.dockerignore)
- [.gitignore](/d:/AI/mindstream/.gitignore)
- [backend/.env](/d:/AI/mindstream/backend/.env)

---

## 3. Mobile Foundation

- `[x]` Flutter app folder created
- `[x]` HTTP dependency added
- `[x]` Runtime-editable backend URL config added
- `[x]` Backend URL persistence added with `shared_preferences`
- `[x]` Health API client implemented
- `[x]` Basic test screen implemented
- `[x]` Loading indicator implemented for health check
- `[x]` User-friendly health error messages added
- `[x]` Android internet permission added
- `[x]` Android cleartext HTTP enabled
- `[x]` APK build path reached successfully
- `[x]` APK installed on physical device
- `[x]` End-to-end health check working on phone

Relevant files:

- [mindstream_mobile/pubspec.yaml](/d:/AI/mindstream/mindstream_mobile/pubspec.yaml)
- [mindstream_mobile/lib/config.dart](/d:/AI/mindstream/mindstream_mobile/lib/config.dart)
- [mindstream_mobile/lib/services/api_service.dart](/d:/AI/mindstream/mindstream_mobile/lib/services/api_service.dart)
- [mindstream_mobile/lib/main.dart](/d:/AI/mindstream/mindstream_mobile/lib/main.dart)
- [mindstream_mobile/android/app/src/main/AndroidManifest.xml](/d:/AI/mindstream/mindstream_mobile/android/app/src/main/AndroidManifest.xml)

---

## 4. Phase 2 - Core User Flow

Goal:

User -> Add Channel -> Fetch Videos -> Select Video -> Generate Summary -> View Summary

### 4.1 Add Channel

- `[x]` Add channel input field in mobile UI
- `[x]` Add "Add Channel" action/button
- `[x]` Add API call for `POST /channels`
- `[x]` Parse returned `channel_id`
- `[x]` Store active `channel_id` in app state
- `[x]` Show success state after adding channel
- `[x]` Show "invalid channel" or backend error state

Backend already available:

- [backend/app/api/channels.py](/d:/AI/mindstream/backend/app/api/channels.py)

### 4.2 Fetch Videos

- `[x]` Add API call for `GET /channels/{channel_id}/videos`
- `[x]` Create video list UI
- `[x]` Render:
  - title
  - optional published date
- `[x]` Add loading state for video fetch
- `[x]` Add empty state: "No videos found"
- `[x]` Add error state for fetch failures

Backend already available:

- [backend/app/api/channels.py](/d:/AI/mindstream/backend/app/api/channels.py)

### 4.3 Select Video

- `[ ]` Make video list items tappable
- `[ ]` Store selected `video_id`
- `[ ]` Highlight active selection in UI

### 4.4 Generate Summary

- `[ ]` Add API call for `POST /videos/{video_id}/summarize`
- `[ ]` Add "Summarize" button
- `[ ]` Add loading state during summary generation
- `[ ]` Handle long-running request gracefully
- `[ ]` Show backend errors cleanly

Backend already available:

- [backend/app/api/videos.py](/d:/AI/mindstream/backend/app/api/videos.py)

### 4.5 Display Summary

- `[ ]` Add API call for `GET /videos/{video_id}/summary`
- `[ ]` Add summary display container/view
- `[ ]` Make summary view scrollable
- `[ ]` Add empty state: "No summary available"
- `[ ]` Format summary for readability

Backend already available:

- [backend/app/api/summaries.py](/d:/AI/mindstream/backend/app/api/summaries.py)

---

## 5. UX Improvements

- `[-]` Loading states implemented
  - `[x]` Health check loading
  - `[ ]` Channel add loading
  - `[ ]` Video fetch loading
  - `[ ]` Summary generation loading

- `[-]` Error handling implemented
  - `[x]` Health check errors improved
  - `[ ]` Channel add errors improved
  - `[ ]` Video fetch errors improved
  - `[ ]` Summary errors improved

- `[-]` Response formatting implemented
  - `[x]` Health response formatted
  - `[ ]` Channel creation response formatting
  - `[ ]` Video list formatting
  - `[ ]` Summary formatting

- `[ ]` Empty states added for:
  - no videos found
  - no summary available

---

## 6. Data Handling

- `[x]` Backend URL persisted locally
- `[ ]` Cache last `channel_id`
- `[ ]` Cache selected `video_id` if useful
- `[ ]` Avoid duplicate summary generation
- `[ ]` If summary already exists, fetch summary before regenerate

---

## 7. Validation / Testing

### Backend

- `[-]` Restart Docker -> data persists
  - `[x]` persistence implemented
  - `[ ]` explicit restart test still to be confirmed

- `[x]` Invalid `video_id` returns 404

### Mobile

- `[x]` Wrong backend URL -> error handled
- `[ ]` Wi-Fi reconnect -> verify app works again
- `[x]` App restart -> backend URL persists
- `[x]` Physical device connectivity verified
- `[ ]` Full flow test from channel add to summary display

---

## 8. Recommended Next Execution Order

Work through these in order:

1. `[ ]` Build Add Channel UI and API call
2. `[x]` Build Fetch Videos UI and list rendering
3. `[ ]` Add video selection state
4. `[ ]` Build Summarize action
5. `[ ]` Build Summary display UI
6. `[ ]` Add channel/video/summary loading and empty states
7. `[ ]` Add summary re-fetch vs regenerate logic
8. `[ ]` Run full end-to-end mobile validation

---

## 9. Definition of Local MVP

The local MVP is complete when all of these are true:

- `[ ]` User can enter backend URL
- `[ ]` User can add a channel from the mobile app
- `[ ]` User can fetch and view videos
- `[ ]` User can select a video
- `[ ]` User can generate a summary
- `[ ]` User can view the generated summary
- `[ ]` Backend still works after Docker restart
- `[ ]` Mobile app still works after app restart

---

## 10. Notes

- Do not modify `src/mindstream`
- Keep API -> service separation intact
- Keep Flutter UI simple
- Prefer completing one vertical slice at a time
