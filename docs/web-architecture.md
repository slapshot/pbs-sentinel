# Web-first architecture

PBS Sentinel is a **self-hosted web application**, reachable from authorized devices through HTTPS. The offline CLI remains a supporting diagnostic utility, not the primary user interface.

## Deployment boundary

```text
Browser (desktop / phone)
   |
   | HTTPS, identity provider / MFA at ingress (production)
   v
Reverse proxy (TLS, rate limiting, security headers)
   | /              | /api/v1/*
   v                v
React SPA        FastAPI application (127.0.0.1:8787)
                       |
                       | HTTPS / PBSAPIToken, TLS checked
                       +--> PBS A :8007
                       +--> PBS B :8007
                       +--> PBS N :8007
```

**No browser-to-PBS connections.** The browser does not receive PBS credentials, and browser-supplied URLs are never forwarded to PBS.

The server uses a **static allowlist** of upstream PBS URLs and datastores. API tokens are resolved from server environment variables; the configuration file includes only references to their variable names. Do not use `root@pam` tokens for this application. Use dedicated read-only users/tokens and grant the minimum PBS permissions (e.g. Datastore.Audit and additional specific read grants as required by tested endpoints). Verify actual privileges on every server.

## Initial development milestone

On `dev`, the app includes:

- Python FastAPI server exposing **GET-only** endpoints, protected by a distinct PBS Sentinel bearer access token.
- Configured PBS instances, datastore metadata and status, namespaces and groups through official management API (port 8007).
- Basic responsive React dashboard for selecting instance, datastore and namespace, with group counts and health summary.
- Separate offline CLI for filesystem metadata audit and saved GC logs.
- No create/update/delete actions; no arbitrary remote URLs, native verify triggers, chunk downloads, recovery or namespace moves.

The first authentication form is **MVP-only**: it holds the Sentinel access token in browser memory and does not persist it in localStorage or cookies. It is not a production identity system. **Do not expose this initial service to the public internet without a hardened authentication gateway with MFA/SSO and access restrictions.** Long term, replace the shared token with per-user OIDC sessions, RBAC and auditable roles.

## Backend API (versioned)

All endpoints below are read-only. Except `health`, they require `Authorization: Bearer <sentinel access token>`.

| Route | Purpose |
| --- | --- |
| `GET /api/v1/health` | Liveness and version |
| `GET /api/v1/instances` | Configured instances (no secrets or URLs) |
| `GET /api/v1/instances/{id}/version` | PBS version |
| `GET /api/v1/instances/{id}/datastores` | PBS datastore listing, filtered to allowlist |
| `GET /api/v1/instances/{id}/datastores/{store}/status` | Datastore usage and status |
| `GET /api/v1/instances/{id}/datastores/{store}/namespaces` | Namespace discovery |
| `GET /api/v1/instances/{id}/datastores/{store}/groups?ns=...` | Groups for one namespace |

The API uses official PBS routes such as `GET /api2/json/admin/datastore/{store}/groups?ns=...`. Endpoint data shapes and access permissions should be validated against each supported PBS version.

## Development setup

Prerequisites: Python 3.11+, Node.js compatible with Vite 7, a Linux host for production and a PBS API token for remote inspection.

```bash
git switch dev
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[web]'
cp config/remotes.example.json config/remotes.local.json
```

Edit `config/remotes.local.json` with real instance URLs, datastore allowlists and token IDs. **Never commit this file.** Provide the PBS token secret as an environment variable named in `token_secret_env`, then set:

```bash
export PBS_SENTINEL_CONFIG="$PWD/config/remotes.local.json"
export PBS_SENTINEL_ACCESS_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export PBS_SENTINEL_PBS_PRIMARY_TOKEN='<token secret>'
pbs-sentinel-web
```

Keep the application access token available for the browser login and keep the PBS API token **server-side only**. A terminal export is okay in a disposable dev session, but production secrets belong in environment files with restrictive permissions or a secret manager.

In a **separate** terminal:

```bash
cd web
npm install
npm run dev
```

Open the Vite development UI through a trusted local connection (default `http://127.0.0.1:5173`). The Vite proxy routes `/api` to `http://127.0.0.1:8787`.

Test API manually from the same host:

```bash
curl -H "Authorization: Bearer ${PBS_SENTINEL_ACCESS_TOKEN}" \
  http://127.0.0.1:8787/api/v1/instances
```

## Production posture (not yet released)

- Dedicated non-root LXC/VM. Avoid installing PBS Sentinel inside a PBS daemon/VM.
- Reverse proxy with HTTPS, robust login / MFA, allowlisted clients where practical, rate limiting and security headers.
- Backend listens on loopback or a private interface only. Never expose Uvicorn directly.
- Serve built `web/dist` assets on the same HTTPS origin with `/api` proxied to loopback.
- Store credentials in root-owned secrets accessible to the dedicated service account, not Git.
- Restrict egress to configured PBS 8007, pin appropriate trust roots, prevent remote auto-proxying and audit all API calls.
- Ensure repository fixtures/docs never reveal operational names, IP addresses or hashes from production.

## Future milestones

- Normalized task/verify/GC incident views and searchable history.
- Per-user authentication and roles, asynchronous job collection, retention of redacted findings.
- Guided read-only missing-chunk investigation and later reviewed recovery execution.
- Native PBS Verify remains authoritative for integrity; this app must never call a metadata listing a verified backup.

## References

- [Official Proxmox Backup Server API viewer](https://pbs.proxmox.com/docs/api-viewer/index.html)
- [PBS API token documentation](https://pbs.proxmox.com/docs/user-management.html)
- [Namespace API and group `ns` query examples](https://forum.proxmox.com/threads/inquiry-about-the-proxmox-backup-api.166986/)
- [Comparison with neighboring projects](comparison.md)
