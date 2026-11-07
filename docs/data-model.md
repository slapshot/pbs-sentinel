# Data model and finding taxonomy

MVP output contains deterministic JSON:

```json
{
  "schema_version": 1,
  "groups": [
    {
      "namespace": "",
      "backup_type": "vm",
      "backup_id": "42",
      "owner": "root@pam",
      "snapshots": ["2026-01-02T03:04:05Z"]
    }
  ],
  "findings": [
    {
      "code": "root_group",
      "severity": "info",
      "namespace": "",
      "backup_type": "vm",
      "backup_id": "42",
      "message": "Backup group resides in root namespace."
    }
  ],
  "summary": {
    "groups": 1,
    "snapshots": 1,
    "findings": 1
  }
}
```

Source is intentionally not embedded as a full physical absolute path in findings. `namespace: ""` denotes the root namespace. Group identity is **(repository, datastore, namespace, backup type, backup id)** at fleet level; the offline MVP only knows namespace, type and ID within the explicitly supplied datastore.

## Fields

- `schema_version`: integer for compatibility
- `groups`: stable sort by namespace, backup type, backup ID
- `findings`: stable sort by severity/code/namespace/type/id/message
- `owner`: text read from the group owner metadata, or null if unavailable
- `snapshots`: sorted directory names with timestamp-like naming, not a guarantee of valid manifests
- `summary`: counts of observed groups, snapshots and findings

## Missing chunk finding

`missing_chunk` adds `chunk_digest` (64 hex) and `index_path` (as emitted by the log), which may contain sensitive storage layout details. Treat JSON as operational data; sanitize before publishing.

## Severity

- `info`: normal observation worth reviewing (root group)
- `warning`: anomaly requiring context (duplicate identity, missing chunk from GC)
- `error`: layout/read failure

Future versions should introduce stable machine-readable evidence provenance (task UPID, timestamp, specific API version) and separate *observed* from *assumed* origin.
