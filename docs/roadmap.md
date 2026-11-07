# Roadmap

The project is intentionally narrow: **audit -> explain -> plan -> approve**. Avoid feature bloat.

## M0 — Documentation and OSS scaffolding (main)

- [x] Scope, architecture, comparison, data model and security principles
- [x] Document branch policy and contribution expectations
- [x] License Apache-2.0
- [ ] First tagged release

## M1 — Read-only offline CLI (dev)

- [x] Synthetic datastore layout inventory
- [x] Find root-namespace groups and namespace ID collisions
- [x] Parse missing chunk references from PBS GC logs
- [x] Text and JSON output
- [x] No runtime third-party dependencies
- [x] Unit tests, isolated fixtures and basic CI
- [ ] Test against sanitized exports from multiple PBS versions
- [ ] Improve handling of unexpectedly large or nonstandard filesystem layouts

## M2 — Remote fleet audit (planned)

- [ ] API token authentication with TLS validation
- [ ] Inventory remote datastores, namespaces, group ownership, snapshot metadata, verify tasks
- [ ] Compare intended PVE storage mappings and actual PBS namespaces
- [ ] Context-scoped JSON reports; avoid secret-bearing output
- [ ] Explicit compatibility matrix for PBS/PVE versions

## M3 — Evidence-based repair planning (planned)

- [ ] Missing chunk digest extraction from verify + GC
- [ ] Search alternate datastores via authorized connectors
- [ ] Decode and validate candidate chunk integrity (incl. encrypted-data limitations)
- [ ] Dry-run recovery plan; immutable approval record
- [ ] Preflight checks and safe, non-clobber executor behind an opt-in switch
- [ ] Native PBS Verify and isolated restore drill guidance

## M4 — Fleet workflows (planned)

- [ ] Namespace migration plan with collision and chronological merge validation
- [ ] Review-only retention/GC policies
- [ ] Idempotent incident reports and operator runbooks
- [ ] Optional Ansible integration, metrics export

## Non-goals

- Replacing PBS native backup/restore and verification.
- Automated deletion of snapshots to silence warnings.
- Editing index files or manufacturing chunk hashes.
- Another broad Proxmox dashboard.
- Storing secrets or production backup contents in this repository.

See [comparison](comparison.md) for boundaries relative to existing projects.
