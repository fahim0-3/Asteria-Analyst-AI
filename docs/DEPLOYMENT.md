# Deployment

For local demos, use SQLite and Vite. `docker compose up --build` uses PostgreSQL, named metadata/upload/export volumes, health-gated startup, Alembic, FastAPI, and nginx.

For Render, Railway, Fly.io, DigitalOcean, or AWS: deploy frontend as static assets/CDN, backend as a private container service, and PostgreSQL as managed storage; replace local upload volumes with S3-compatible object storage; put exports behind signed URLs; store JWT/database/LLM secrets in the platform secret manager; enforce TLS; run migrations as a release command; use a dedicated least-privilege DB role; add workers for profiles/reports; set CPU/memory/query limits; and configure logs, metrics, alerts, backups, and retention. Never rely on an ephemeral container filesystem for customer uploads.

