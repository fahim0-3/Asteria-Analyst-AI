# Architecture

The monorepo separates the React presentation layer, FastAPI contracts, persistence, planner, validators, execution engines, and exports. SQLite provides a zero-configuration local path; Compose selects PostgreSQL. Uploaded files remain outside the metadata database and are addressed only by server-generated IDs.

Key trade-offs: a deterministic mock provider makes demos reproducible; pandas keeps the local path approachable; the typed DSL sacrifices arbitrary expressiveness to eliminate generated-code execution; and SQL validation is independent of generation so a compromised prompt cannot bypass it. A production scale-out would use object storage, DuckDB/Polars workers, async jobs, a secret manager, and database-native resource governance.

The frontend never receives storage paths, password hashes, connection secrets, or internal exceptions. The API retrieves sources through owner-scoped queries. Audit records capture the user, source, plan/query, validation/execution status, rows, and latency.

