# SNAC-v2 Release Notes

Date: 2026-03-12
Branch: master

## Commits Included

- `f8068720` - chore(snac): checkpoint current cockpit brain and continuity setup
- `45e42472` - fix(hardening): remove unsafe power eval and harden compose/nginx/ui paths

## Highlights

- Added a full project checkpoint for the current SNAC-v2 backend, cockpit UI, infrastructure, and planning docs.
- Applied production hardening fixes for calculator safety, Docker Compose reliability/security, Nginx service routing, and UI path portability.

## Security and Reliability Fixes

### Backend

- Removed exponentiation (`**`) support from safe arithmetic evaluation in `backend/main.py` to reduce CPU-exhaustion risk from crafted expressions.

### Docker Compose

- Replaced weak default PostgreSQL password fallback with required environment variable validation.
- Added `restart: unless-stopped` for core services:
  - `db`
  - `redis`
  - `qdrant`

### Nginx

- Replaced hardcoded host IP upstreams with Docker service-name upstreams:
  - `backend:8000`
  - `frontend:80`

### Cockpit UI

- Replaced hardcoded Windows paths in Project Vault with environment-configurable root path:
  - `VITE_PROJECT_ROOT` (default: `/workspace`)
- Paths are now composed from `PROJECT_ROOT`, improving portability across environments.

### TLS Prep

- Added `nginx/ssl/.gitkeep` so the SSL volume mount path exists by default.

## Notes

- CORS configuration already uses explicit origin parsing (`CORS_ALLOW_ORIGINS`) and is not wildcard by default.
- OpenAI client initialization is already guarded by API key presence.
- PostgreSQL remains optional in current architecture (Redis/Qdrant-backed runtime); evaluate DB wiring if long-term persistent relational storage is required.

## Recommended Next Steps

1. Configure remote and push commits + tag.
2. Set required secrets in `.env`, especially `POSTGRES_PASSWORD`.
3. Run deployment preflight and then `docker compose up -d --build` on target host.
