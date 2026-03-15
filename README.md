# Mindstream Milestone-1 POC

CLI-only proof-of-concept pipeline that:
- reads YouTube channel/video inputs,
- discovers recent videos,
- fetches transcripts,
- creates per-video structured summaries,
- produces one aggregated JSON intelligence report.

## Setup

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

## Configure channels

Edit `configs/channels.txt` with one URL per line. Supported inputs:
- `https://www.youtube.com/@handle`
- `https://www.youtube.com/channel/<id>`
- `https://www.youtube.com/c/<custom>`
- direct video URL (`watch?v=`) to bypass discovery

Example:

```txt
https://www.youtube.com/@GoogleDevelopers
https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Run

```bash
python -m mindstream.cli.run_report --channels configs/channels.txt
```

Optional flags:
- `--max-per-channel` (default `2`)
- `--max-videos` (default `10`)
- `--cadence-minutes` (default `360`)
- `--window-hours` (default `24`)

## Optional OpenAI usage

If `OPENAI_API_KEY` is set in environment (or `.env`), the OpenAI summarizer is used.
Without it, pipeline uses a deterministic local mock summarizer so it still runs end-to-end.

## Transcript availability notes

YouTube transcripts may be unavailable for some videos due to disabled captions, region/language limits, or API issues.
Those videos are skipped for summarization, recorded as missing in raw artifacts, and included in run metadata.

## Output locations

- raw records: `data/raw/<video_id>.json`
- per-video summaries: `data/per_video/<video_id>.json`
- aggregated report: `data/reports/<timestamp>.json`

## Docker note

Mindstream uses the Python src-layout structure.
The container sets `PYTHONPATH=/app/src` so imports resolve correctly.

## Docker usage

Build and run with Docker Compose:

```bash
docker compose run --build mindstream
```
## Running Mindstream UI

```bash
docker compose up --build
```

Open browser:

`http://localhost:8501`

## Running with Ollama

```bash
docker compose up --build
```

Open browser:

`http://localhost:8501`

The stack now includes:

- `mindstream` -> application + UI
- `ollama` -> local LLM runtime

To download a model inside the Ollama container:

```bash
docker exec -it ollama ollama pull llama3
```

or

```bash
docker exec -it ollama ollama pull mistral
```

Recommended models:

- Summarization: `llama3`
- Embeddings: `nomic-embed-text`

## Vector Database

Mindstream now uses Chroma to store transcript chunks and embeddings.

Services:

- `mindstream`
- `ollama`
- `chroma`

Start system:

```bash
docker compose up --build
```

Chroma API available at:

`http://localhost:8000`

## Vector Storage

Mindstream stores transcript embeddings in monthly Chroma collections.

Example:

- `mindstream_2026_03`
- `mindstream_2026_04`

This prevents collections from growing too large and allows easier data retention management.
