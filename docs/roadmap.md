# Roadmap

**Product:** a centralized, self-hosted web application with a read-only API gateway and an optional diagnostic CLI. Do not confuse general Proxmox fleet dashboards with PBS-specific backup integrity analysis.

## M0 — Public project foundation (`main`)

- [x] Open-source scope, comparison with other projects and license
- [x] Security model, data model and contribution policy
- [x] Web-first architecture and documented API boundaries
- [ ] First stable tagged release

## M1 — Working read-only prototype (`dev`)

- [x] Offline datastore/namespace inventory and GC warning parser
- [x] JSON/text CLI and synthetic test fixtures
- [x] FastAPI server with a static allowlist of PBS endpoints and datastores
- [x] API token auth to PBS with TLS verification; independent bearer access token for Sentinel
- [x] GET-only endpoints for instance, datastore, namespace and group metadata
- [x] Responsive React dashboard preview
- [x] Automated Python tests and frontend build on CI
- [ ] Real, permission-scoped PBS smoke test (read-only only)
- [ ] Browser-level tests, pagination/large-inventory testing, and access-token UX hardening
- [ ] Reproducible frontend lockfile before release

## M2 — Production-ready web foundation (planned)

- [ ] Per-user identity (OIDC/SSO), MFA, authorization roles and sessions
- [ ] Deployment guides for dedicated LXC/VM, reverse proxy and HTTPS
- [ ] Central audit trail and server-side secret management
- [ ] Status refresh, asynchronous collectors and caching/rate limits
- [ ] Validated API compatibility matrix for PBS 4.x
- [ ] Accessible responsive UI, browser-level tests and telemetry minimization

## M3 — Backup integrity incident analysis (planned)

- [ ] GC/Verify/task log ingestion and incident timeline
- [ ] Missing chunk digest mapping to affected backup index and snapshots
- [ ] Read-only authorized search for alternative chunk copies
- [ ] Candidate integrity validation with digest/CRC/decode checks; document encryption limits
- [ ] Operator-readable, replayable recovery proposals; no automatic repair

## M4 — Guarded operations and restore drills (planned)

- [ ] Namespace migration planner with provenance, owner/collision/time-window evidence
- [ ] Explicit dry-run and approval workflow
- [ ] Carefully reviewed non-clobber recovery executor, only after M3 acceptance
- [ ] Native PBS Verify and isolated restore drill orchestration with explicit permissions
- [ ] Retention/GC policy audit, no auto-delete

## Non-goals

- General-purpose Proxmox cluster management or another monitoring suite
- Reimplementing the native PBS data protocol or editing index files
- Auto-deleting backups to suppress GC/Verify warnings
- Treating successful backups or namespace group counts as evidence of integrity
- Shipping production credentials, topology or backup payloads in source control

See [web architecture](web-architecture.md), [security](security.md) and [comparison](comparison.md).
