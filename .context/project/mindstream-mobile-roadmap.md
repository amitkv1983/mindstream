# Mindstream Mobile App - Local Development Roadmap

## 🎯 Objective

Build a fully functional mobile app (APK) that connects to a local FastAPI backend (Dockerized) and allows:

- Add YouTube channels
- Fetch videos
- Generate summaries
- Display results

This roadmap focuses ONLY on local development and APK testing.

---

# ✅ CURRENT STATUS (COMPLETED)

## Backend
- FastAPI backend implemented
- Dockerized backend working
- SQLite integrated with volume persistence
- APIs available:
  - GET /health
  - POST /channels
  - GET /channels/{id}/videos
  - POST /videos/{id}/summarize
  - GET /videos/{id}/summary

## Mobile
- Flutter app created
- APK builds successfully
- App installed on phone
- Backend connectivity working (via IP)
- Runtime backend URL configurable
- URL persistence implemented

## Infrastructure
- Docker Compose working
- Volume mapping for SQLite working
- End-to-end connectivity verified

---

# 🚀 PHASE 1 — STABILITY (COMPLETED)

✔ Backend connectivity  
✔ Docker persistence  
✔ Runtime config  
✔ Error handling (basic)  
✔ APK install  

---

# 🚀 PHASE 2 — CORE USER FLOW (NEXT)

## 🎯 Goal

Implement full user journey:

User → Add Channel → Fetch Videos → Select Video → Generate Summary → View Summary

---

## 📌 Step 2.1 — Add Channel UI

### UI Requirements
- Input field:
  - Channel URL or name
- Button:
  - "Add Channel"

### API
POST /channels

### Expected Response
- Channel ID returned

### Tasks
- Create screen or section
- Add API call
- Store returned channel_id in app state

---

## 📌 Step 2.2 — Fetch Videos

### API
GET /channels/{channel_id}/videos

### UI
- List of videos
- Each item shows:
  - Title
  - (optional) published date

### Tasks
- Create video list view
- Handle loading state
- Handle empty state

---

## 📌 Step 2.3 — Select Video

### UI
- Clickable list item
- Navigate or expand

### Tasks
- Store selected video_id

---

## 📌 Step 2.4 — Generate Summary

### API
POST /videos/{video_id}/summarize

### UI
- Button:
  - "Summarize"

### Tasks
- Show loading indicator
- Handle delay (this may take time)

---

## 📌 Step 2.5 — Display Summary

### API
GET /videos/{video_id}/summary

### UI
- Text view
- Scrollable

---

# 🚀 PHASE 3 — UX IMPROVEMENTS

## 🎯 Goal

Make app usable and clean

---

## Tasks

### 🔹 Loading States
- Show spinner for:
  - channel add
  - video fetch
  - summary generation

---

### 🔹 Error Handling
Replace raw errors with:
- "Cannot connect to backend"
- "Invalid channel"
- "Video not found"

---

### 🔹 Response Formatting
- Clean text display
- Avoid raw JSON

---

### 🔹 Empty States
- "No videos found"
- "No summary available"

---

# 🚀 PHASE 4 — DATA HANDLING

## 🎯 Goal

Improve usability

---

## Tasks

### 🔹 Cache last channel_id
- Store locally (optional)

### 🔹 Avoid duplicate calls
- If summary exists → fetch instead of regenerate

---

# 🚀 PHASE 5 — DEBUG & TESTING

## 🎯 Goal

Ensure system stability

---

## Tests

### Backend
- Restart Docker → data persists
- Invalid video_id → 404

---

### Mobile
- Wrong backend URL → error handled
- WiFi reconnect → works again
- App restart → URL persists

---

# 🚀 PHASE 6 — OPTIONAL (LATER)

## NOT REQUIRED FOR LOCAL MVP

---

### 🔹 Authentication
- Google login

---

### 🔹 Background Jobs
- Async summarization

---

### 🔹 Cloud Deployment
- AWS / OCI / GCP

---

### 🔹 Notifications
- Push notifications

---

# 🧠 DEVELOPMENT RULES

## DO NOT:
- Modify src/mindstream pipeline
- Introduce new frameworks
- Add auth yet
- Over-engineer

---

## ALWAYS:
- Keep API → service separation
- Reuse existing backend logic
- Test on real device

---

# 🧪 TEST FLOW (FINAL)

1. Start backend:
   docker-compose up

2. Open app

3. Enter backend URL:
   http://<laptop-ip>:8000

4. Add channel

5. Fetch videos

6. Select video

7. Generate summary

8. View result

---

# 🎯 SUCCESS CRITERIA

✔ Channel added  
✔ Videos displayed  
✔ Summary generated  
✔ Summary displayed  
✔ Works after backend restart  
✔ Works after app restart  

---

# 🔥 FINAL GOAL

A fully working local system:

Mobile APK  
→ FastAPI Backend (Docker)  
→ SQLite (persistent)  
→ Mindstream pipeline  
→ YouTube + AI summary  

---
