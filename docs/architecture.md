# Architecture

## Goals and boundaries

PBS Sentinel starts as a **read-only local audit CLI**, designed for Proxmox Backup Server administrators. Later milestones may include remote API discovery and carefully fenced repair operations. We deliberately do **not** implement a custom backup protocol, index writer, or deduplication engine.

The primary separation is:

```text
Command interface (CLI)
      |
      v
Audit orchestration
  |        |
  v        v
Inventory  GC-log parser         [later: native PBS API adapters]
  \        /
   \      /
    Findings + evidence
          |
          v
     JSON / text output
          |
          v
    [later: reviewed plans]
          |
          v
    [later: opt-in executor]
```

## Milestone 0: offline inspection (dev)

- `audit --datastore-path <path>`: inspect `vm/`, `ct/`, `host/` root groups and the corresponding namespace trees under `ns/`.
- Collect backup-group type, identifier, namespace, owner (when readable), snapshot timestamps and count.
- Detect root namespace groups and duplicate `(type, id)` across multiple namespaces as **review items**, never proof of incorrect placement.
- `--gc-log <file>`: parse `warning: unable to access non-existent chunk <64-hex>, required by "<index path>"`; identify the chunk and referenced index path.
- `--format json|text`: deterministic results, safe for CI/reporting.
- The tool never opens snapshot archives, never reads raw chunk payloads, never runs `verify` and never interprets a directory count as integrity assurance.

## Planned adapters (not implemented)

### Remote PBS API adapter

Use HTTPS port 8007 and official Proxmox API endpoints. Authenticate with scoped API tokens; validate server TLS certificates or an explicitly pinned fingerprint. Consider dedicated read-only permissions and pagination. The endpoint and response shapes must be validated against supported PBS versions before implementation.

### Optional local filesystem probe

Advanced chunk checks require host-local access and cannot be implemented solely via the management API. Prefer an explicitly installed read-only agent or operator-executed signed plan. **Never expose raw chunk paths or write methods through a generic remote shell API.**

### Recovery planner and executor

1. Ingest verified GC/verify findings; capture original repository, datastore, namespace, snapshot and checksum.
2. Search alternate datastores; compare stored-file hashes and decode to validate actual chunk digest.
3. Produce a plan with explicit source/destination, bytes, required privileges, expected ownership and rollback limitations.
4. Operator approves each target; revalidate preconditions immediately before write.
5. Install with atomic no-clobber operations; never overwrite a pre-existing chunk, never fabricate chunks, never edit PBS index files.
6. Run official PBS verify and recommend isolated restore testing.

A completed `group move` or matching snapshot count does **not** prove backup integrity.

## Environment support

- Python >= 3.11; standard library only for the initial CLI.
- Linux and other platforms for GC-log parsing; local directory audits require access to the datastore filesystem.
- PBS 4.x incident scenarios motivate design but **version support is not asserted without compatibility tests**.
- No database, daemon, web UI or privileged agent in the first milestone.

## Error handling and testing

Fail closed for malformed inputs and inaccessible root paths. Record individual non-critical filesystem anomalies as findings rather than silently discarding them. Deterministic sorting, fixture-based tests with synthetic paths/VMIDs and no network requirement. Tests must never touch a real PBS datastore.

## Ownership / provenance limitations

The same VMID may belong to unrelated nodes. PBS group name alone cannot prove source ownership. Additional provenance evidence must come from job definitions, VM/CT configuration, notes and trusted operator annotations. The MVP flags ambiguity; it **does not automatically attribute groups to hosts**.

See [data model](data-model.md) and [security](security.md).
