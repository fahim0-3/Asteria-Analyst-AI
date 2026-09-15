# API reference

Interactive OpenAPI is available at `/docs`. The versioned surface provides health/readiness, login/logout/me, upload/list/detail/delete/schema/profile/preview/type override, analysis execution, saved-analysis list/create, dashboard list/create, CSV analysis export, and admin metrics. All non-health endpoints require a bearer token; resource methods enforce ownership. Structured analysis responses distinguish result, clarification, warning, unsupported, query error, empty, and export states.

