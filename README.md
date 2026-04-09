# Study Planner Telegram Bot

Telegram-first study planner for university students preparing for exams under time pressure.

## What it does

- creates a day-by-day study plan
- stores users, plans, sessions, materials, and progress in PostgreSQL
- accepts pasted text, PDF, DOCX, and images
- uses a hybrid generator:
  - deterministic schedule builder
  - local LLM refinement through an OpenAI-compatible Qwen API
- lets users mark sessions as completed or skipped in Telegram

## Architecture

- `client-telegram-bot/` — thin Telegram client built with aiogram
- `backend/` — FastAPI backend with all domain logic
- `postgres/` — persistent storage
- `qwen-code-api/` — local LLM endpoint

## Main flows

1. `/start` registers the Telegram user.
2. `New plan` asks for exam name, days left, and hours per day.
3. Backend creates the plan and generates study sessions.
4. `Upload materials` accepts text or files and regenerates the plan.
5. `Today` shows today's sessions.
6. `Progress` shows completion stats.

## Quick start

1. Copy `.env.example` to `.env`.
2. Set your Telegram bot token.
3. Make sure your local Qwen-compatible API is reachable.
4. Run:

```bash
docker compose up --build
```

Backend: `http://localhost:8000/health`

## Important notes

- OCR for images requires `tesseract` in the backend container. The current code has a safe fallback.
- The backend expects an OpenAI-compatible API at `LLM_API_BASE_URL`, for example `http://qwen-code-api:8080/v1`.
- The project is structured so a web client can be added later without changing backend domain logic.
