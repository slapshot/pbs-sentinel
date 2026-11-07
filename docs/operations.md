# Operator guide

## Install and run (development branch)

The initial implementation lives on `dev`; `main` initially publishes documentation only.

```bash
git clone https://github.com/slapshot/pbs-sentinel.git
cd pbs-sentinel
git switch dev
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
pbs-sentinel audit --datastore-path /path/to/read-only/export --format text
```

To parse an exported GC log as part of an audit:

```bash
pbs-sentinel audit --datastore-path /path/to/read-only/export \
  --gc-log /path/to/gc.log --format json > report.json
```

The `--datastore-path` parameter requires access to a PBS-shaped directory tree (root `vm/`, `ct/`, `host/`; `ns/` namespaces). **Do not give the process write access to production datastores.** Use read-only snapshots, copies or a restricted user.

## How to interpret findings

- `root_group`: group exists outside a named namespace. This is **informational**, not by itself an error.
- `duplicate_group_identity`: same backup type and ID appear in more than one namespace. Legitimate when different PVE nodes reuse VMIDs.
- `missing_chunk`: parsed from a GC log. Does **not** imply that other chunks are present, nor does it validate currently observed filesystem state.
- `invalid_group`, `unreadable_path` and `symlink_entry`: layout anomalies to investigate.

A clean audit is **not** evidence that any backup can be restored. Always run official PBS Verify and a periodic isolated restore drill.

## Separate responsibilities

- PBS Sentinel: evidence collection and read-only diagnostics (M1).
- Native PBS: verify jobs, garbage collection, prune, group moves, restore.
- Operator: decides namespace provenance, approves future recovery actions and performs restore drills.

## Why 8007 is not SSH

PBS clients can use HTTPS port 8007 for backup/restore even when TCP 22 is closed. Avoid opening SSH publicly simply to copy files between backup servers. If a transfer is required, prefer an approved native PBS backup/restore workflow and verify hashes at both ends.

## Source references

- [PBS backup client](https://pbs.proxmox.com/docs/backup-client.html)
- [PBS administration](https://pbs.proxmox.com/docs/)
