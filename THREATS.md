# TrustVault Threat Model

## Assets and trust boundaries
Assets: document bytes/metadata, credentials/tokens, permission grants, and audit events. Boundaries: client-to-API, API-to-database, API-to-private-file storage, and deployment configuration/secrets.

| Threat | Prototype mitigation | Residual risk |
|---|---|---|
| Unauthenticated requests | JWT bearer authentication | Add rate limiting and HTTPS in deployment |
| Unauthorized download | API checks owner or explicit document grant | Test all new endpoints |
| Read-only user changes/deletes | Edit permission checked by API | UI is not a security boundary |
| Revoked user accesses again | Grant row deleted; next request denied | Previously downloaded bytes cannot be recalled |
| Filename path traversal | Server-generated UUID storage name | Malware scanning and richer validation needed |
| Oversized upload | Upload size cap | Configure reverse-proxy limits too |
| Invalid PDF/PNG signature | Basic signature checks | Not a full parser/scanner |
| Audit row manipulation | Hash-linked records and verification endpoint | Privileged DB attacker can rewrite/recompute all rows; external checkpoints needed |
| Password guessing/token theft | Argon2 and expiring JWT | Rate limiting, HTTPS, secure token storage, revocation list needed |
| Data loss | Local database and file storage | Backups and persistent private object storage needed |

## Authorization policy
- Owners can read/download, edit metadata, soft-delete, and manage grants for their documents.
- `read` grantees can view metadata and download; `edit` grantees can also edit metadata and soft-delete.
- Admin can view audit logs, but does not automatically bypass document content permissions.
- No public static file links are exposed.

## Accepted risks
This is a hackathon prototype, not a production-ready service. Do not upload real sensitive documents. Add migrations, secrets management, HTTPS, rate limits, malware scanning, external audit checkpoints, backups, and a security review before production use.
