# Security model

Implemented controls include PBKDF2-SHA256 password hashes with random salts; expiring HS256 demo tokens; analyst/admin authorization; owner filters; restricted CORS; maximum input lengths; file extension and upload-size allowlists; basename sanitization; generated storage names; duplicate hashes; no secret fields in response models; typed dataframe execution; SQL parsing/allowlists/limits; and audit records.

Threats tested include write SQL, multi-statements, comment bypasses, unknown tables, excessive joins, unknown DSL columns/operators, bad credentials, unauthenticated access, and analyst access to admin metrics.

Before production: use asymmetric or managed identity, token revocation/rotation, HTTPS, CSRF strategy where cookies are used, rate limiting, antivirus/content inspection, encrypted object storage, a cloud secret manager, database-specific read-only roles and timeouts, egress-denied workers, tenant-level database policies, backup/restore tests, dependency scanning, SAST/DAST, and formal incident procedures.

