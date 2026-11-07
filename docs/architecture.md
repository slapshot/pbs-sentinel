# Architecture

**Current product direction: central self-hosted web application.** The offline CLI remains a utility, not the intended user interface.

## Components

```text
Browser
   |
   | HTTPS + upstream SSO/MFA in production
   v
Reverse proxy
   | SPA assets             | /api/*
   v                        v
React/Vite                 FastAPI gateway
                               |
                     Allowlisted HTTPS :8007
                       /       |       \
                      PBS A   PBS B   PBS N
```

The browser never talks directly to PBS. All remote credentials stay on the server, and **no browser-supplied arbitrary URL** is allowed to reach the upstream client. Each remote has a datastore allowlist and a server-side API token. The web backend has no mutation routes.

See [web architecture](web-architecture.md) for endpoints, run commands and production hardening.

## Runtime layers

1. **API gateway:** `src/pbs_sentinel/web_api.py` (FastAPI) exposes only GET endpoints, scoped by remote and datastore. Uniform error responses do not include credentials or upstream exception strings.
2. **Configuration:** `src/pbs_sentinel/web_config.py` loads a static JSON allowlist; secret values are resolved from server environment variables, not JSON.
3. **Web UI:** `web/` is a responsive React SPA, hosted on the same HTTPS origin as the API. A dev-only shared bearer access token is kept in memory. Per-user identity/SSO/MFA is required for public production access and remains future work.
4. **Offline CLI:** `src/pbs_sentinel/cli.py` runs read-only audits of PBS-shaped datastore directories and saved GC logs. It remains useful when API access is unavailable.
5. **Future evidence/incident engine:** normalized verify, GC and prune task information, namespace drift, missing-chunk cross-store lookup, immutable reports and reviewed recovery proposals.

## Safety invariants

- No write endpoints in the current server.
- No background shell, arbitrary command execution, raw chunk download or client-provided upstream URL.
- No secret in browser API responses, logs or repository.
- Host provenance is not inferred from VMID alone.
- Neither a successful backup nor a metadata inventory proves data can be restored.
- PBS native Verify and isolated restore drills remain the authoritative tests.
- Any future action executor must be separately gated, dry-run first, validate digests and never overwrite existing chunks.

## First supported API routes

- `GET /api/v1/health`
- `GET /api/v1/instances`
- `GET /api/v1/instances/{id}/version`
- `GET /api/v1/instances/{id}/datastores`
- `GET /api/v1/instances/{id}/datastores/{store}/status`
- `GET /api/v1/instances/{id}/datastores/{store}/namespaces`
- `GET /api/v1/instances/{id}/datastores/{store}/groups?ns=...`

Except for health, a Sentinel-specific bearer token is required. The backend uses PBS API tokens per remote.

## Test boundaries

- Python >= 3.11; backend FastAPI/httpx are installed via the `[web]` optional extra.
- UI: React/Vite, built with Node.js.
- Unit tests use synthetic datastore fixtures and an isolated mocked PBS HTTP transport; real systems are never targeted by CI.
- The next acceptance gate is a read-only smoke test against a **test PBS user with minimal privileges**. Support for specific PBS versions cannot be asserted until that test is completed.

## Future design

Task collectors and incident reports should use an asynchronous queue and durable history, but we will not introduce a database or background scheduler until the requirements justify it. A remote mutation agent is **not part of the current MVP**.

See [security](security.md), [comparison](comparison.md), [roadmap](roadmap.md).
