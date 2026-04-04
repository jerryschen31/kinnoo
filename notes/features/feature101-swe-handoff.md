# Feature 101 — SWE Handoff: Dockerfile and docker-compose

## Context
Create production Dockerfile and docker-compose.yml for local development. The server runs as a FastAPI app via Uvicorn.

## Files to Create
- `Dockerfile` (at project root) — Production multi-stage build
- `docker-compose.yml` — Local development setup
- `.dockerignore` — Exclude unnecessary files from build context

## Dockerfile Design
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY server/requirements.txt .  # or requirements.txt if shared
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY server/ ./server/
COPY src/ ./src/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "server.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose.yml
```yaml
services:
  server:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data  # persistent auth store
    environment:
      - KINNOO_ENV=dev
      - JWT_SECRET=dev-secret
      - SESSION_SECRET=dev-session-secret
      # S3 config for local dev (localstack or real)
```

## .dockerignore
```
__pycache__/
*.pyc
*.egg-info/
scratch/
notes/
tests/
outputs/
.git/
*.kno
env/
.env
```

## Implementation Notes
- Final image should be under 200MB
- Non-root user is critical for production security
- Health check uses /health endpoint (from feature89)
- Server entry: `uvicorn server.app:create_app --factory`
- May need to determine if `requirements.txt` is shared or server has its own

## Testing
- `docker build -t kinnoo-server .` succeeds
- `docker run kinnoo-server` starts and responds on :8000
- Health check passes
- Image runs as non-root user

## Dependencies
- feature89 (/health endpoint must exist)

## Acceptance Criteria Summary
1. Multi-stage Dockerfile, non-root user, health check
2. Image under 200MB
3. docker-compose.yml for local dev
4. `docker compose up` → server at localhost:8000
