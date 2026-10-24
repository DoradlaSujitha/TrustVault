# TrustVault — Secure Document Sharing

A hackathon prototype for document sharing with roles, per-document permissions, and an audit trail.

## Features
- Admin, owner, viewer roles; Argon2 password hashes and JWT authentication
- Upload, search/list, download, edit metadata, and soft-delete documents
- Owners grant/revoke per-document `read` or `edit` access to named users
- API-level authorization checks; denied access attempts are audited
- Admin-only audit log and hash-chain linkage verification
- FastAPI Swagger UI and Streamlit frontend
- SQLite by default (no Docker or PostgreSQL installation required); PostgreSQL supported with `DATABASE_URL`

> **Prototype, not production-certified.** Before handling real sensitive data, add HTTPS, secret management, rate limiting, malware scanning, database migrations, persistent private object storage, backups, and security review. A database administrator who can rewrite every audit row can recompute this prototype's hash chain; use external signed checkpoints for stronger integrity.

## Run on Windows PowerShell
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m backend.seed
uvicorn backend.main:app --reload
```
Open http://127.0.0.1:8000/docs. In a second terminal:
```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```
Streamlit runs at http://localhost:8501. If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and retry.

## Demo accounts (local only)
| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | ChangeMe-Admin-123! |
| Owner | owner@example.com | ChangeMe-Owner-123! |
| Viewer | viewer@example.com | ChangeMe-Viewer-123! |

These public demo credentials are for local testing only. Change them before public deployment. Set `SEED_*` environment variables before running the seed script to use custom credentials. Never commit `.env`.

## Tests
```powershell
pytest -q
```

Re-run the test suite in your own environment before submission and record the actual result. Do not claim tests passed unless you have verified the result yourself.

## Database
Default local database: `DATABASE_URL=sqlite:///./trustvault.db`. PostgreSQL example: `postgresql+psycopg://postgres:URL_ENCODED_PASSWORD@localhost:5432/trustvault`. Create the database first and URL-encode special characters in passwords.

## Deployment notes
The included `render.yaml` defines a FastAPI API, Streamlit UI, and PostgreSQL database. First push this repository to GitHub, then in Render choose **New → Blueprint**, select the repository, and review the three resources before applying. Set strong, unique `SEED_*_PASSWORD` values when prompted; do not use an empty password. After deployment, verify the API root and `/docs`, then open the Streamlit UI and test login, upload, grant, revoke, denied download, and admin audit in a private browser. The configured service names are expected to use `https://trustvault-api.onrender.com` and `https://trustvault-ui.onrender.com`; record the actual URLs Render assigns. Render free services may sleep, free database availability/retention can change, and local file storage may be ephemeral; this configuration is a hackathon demo setup, not production storage. The app is not considered deployed until these checks succeed.

## API
`POST /auth/login`, `GET /auth/me`, `POST /documents`, `GET /documents`, `GET /documents/{id}`, `GET /documents/{id}/download`, `PATCH /documents/{id}`, `DELETE /documents/{id}`, `POST /documents/{id}/permissions`, `DELETE /documents/{id}/permissions/{user_id}`, `GET /admin/audit`, `GET /admin/audit/verify`.

## Submission checklist
- [ ] Run tests; fix any failures
- [ ] Replace public demo credentials and JWT secret
- [ ] Test denied access, grant, revoke, edit, delete, and audit
- [ ] Configure persistent private storage for deployment
- [ ] Review `PROMPTS.md`; ensure every entry matches actual work and has a real commit link
- [ ] Push to your own public GitHub repository with meaningful commit history
