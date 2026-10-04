# MarkItDown Web

Stateless single-page web app wrapping [microsoft/markitdown](https://github.com/microsoft/markitdown)
(pinned to 0.1.8, `[all]` extras). Drop a file, preview the Markdown, copy it, or download it as `.md`.

## Run

    docker compose up --build        # http://localhost:8080

## No persistence

Uploads are read into memory, converted from a `BytesIO`, returned as JSON, and discarded.
The container runs read-only with a RAM `tmpfs` at `/tmp`, as a non-root user, with all capabilities dropped.
Logs contain method, route, status and duration only. No URL input, plugins, LLM or Azure services are enabled.

## Develop

    cd backend && pip install -r requirements-dev.txt && pytest && uvicorn app.main:app --port 8080
    cd frontend && npm install && npm run dev   # proxies /api to :8080

Config (env): `MAX_UPLOAD_MB` (25), `CONVERT_TIMEOUT_S` (60), `CONVERT_WORKERS` (2).
