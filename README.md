# Ollama Network Chat (Gemma 4)

Local multi-user chat app for Ollama with a FastAPI backend, React frontend, and Postgres persistence.

## What this app does

- Lets users register and log in.
- Keeps each user's chats and messages isolated.
- Stores chat sessions and message history in Postgres.
- Proxies chat requests from backend to Ollama's OpenAI-compatible API.
- Uses async chat jobs queue with Celery + Redis so long LLM calls do not block request handling.
- Uses pgvector embeddings for semantic context retrieval (recent + relevant history).

## Architecture (plain text)

```
Browser -> Frontend container (React + Nginx, :3000)
        -> Nginx proxy /api -> Backend container (FastAPI, :8000)
        -> Postgres container (db:5432)
        -> Redis container (broker)

Worker (Celery) -> Postgres + Redis + Host Ollama
Backend -> Redis (enqueue job) + Postgres (status/messages)
```

## Prerequisites

- Docker + Docker Compose
- Ollama installed and running on macOS host
- Gemma model pulled in Ollama

## Ollama setup on Mac

1. Install/start Ollama on host.
2. Pull model:

```bash
ollama pull gemma4:latest
ollama pull nomic-embed-text
```

3. Optional quick check on host:

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma4:latest",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Important: Ollama runs on host, not in Docker.

On macOS, GUI apps do not always inherit shell exports from `.zshrc`/`.bashrc`. If you need Ollama reachable beyond localhost, prefer configuring `OLLAMA_HOST` with a LaunchAgent-based setup instead of relying only on shell `export`.

## Run

1. Copy env file:

```bash
cp .env.example .env
```

2. Build and start:

```bash
docker-compose up --build
```

## URLs

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend health: [http://localhost:8000/health](http://localhost:8000/health)
- Frontend-proxied health: [http://localhost:3000/health](http://localhost:3000/health)

## Access From Other Devices (hosts file)

If router DNS is unavailable, use hosts entries on client devices.

Example hosts entry on each client device:

`192.168.1.50 macmini`

Then open:

- [http://macmini:3000](http://macmini:3000)
- [http://macmini:3000/health](http://macmini:3000/health)

Notes:

- Replace `192.168.1.50` with your Mac mini LAN IP.
- Keep frontend mapped to port `3000` in `docker-compose.yml`.

## Default development flow

- Edit backend/frontend code.
- Rebuild if dependencies or Dockerfile changed:

```bash
docker-compose up --build
```

- Stop stack:

```bash
docker-compose down
```

## Troubleshooting

- Ollama reachable on host but not from backend container:
  - Verify `OLLAMA_BASE_URL=http://host.docker.internal:11434`
  - Confirm Ollama is listening on expected interface.
- `host.docker.internal` issues:
  - Confirm Docker Desktop is running normally on macOS.
  - `docker-compose.yml` includes `extra_hosts` mapping for backend.
- Model not found:
  - Run `ollama pull gemma4:latest` on host.
- Ollama connection refused:
  - Ensure Ollama process is running and bound correctly.
- DB migration issues:
  - Check backend logs; startup script runs `alembic upgrade head`.
- CORS errors:
  - UI now calls backend through frontend nginx proxy (`/api`), so browser CORS is normally not needed for chat UI.
  - If you call backend directly from a browser origin, adjust `BACKEND_CORS_ORIGINS` in `.env`.
- Long responses timeout:
  - Increase `OLLAMA_TIMEOUT` in `.env` (default is `300`).
- Queue unavailable:
  - Ensure `redis` and `worker` services are healthy (`docker compose ps`).
  - Verify `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in `.env`.
- Embedding model issues:
  - Ensure `OLLAMA_EMBEDDING_MODEL` is available in Ollama (`ollama pull nomic-embed-text`).
