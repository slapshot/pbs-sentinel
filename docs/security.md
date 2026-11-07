# Security and safety model

**Do not run experimental code with root privileges on production PBS servers.** The first milestone needs only read access to exported logs or directory metadata.

## Non-negotiable constraints

1. Default operation is read-only. No deleting snapshots, pruning, GC invocation, group move, filesystem mutation, backup job modification or API write methods in the MVP.
2. Treat input directories, JSON and PBS task logs as untrusted. Do not use `shell=True` or interpolate paths into commands.
3. Symlink traversal is disallowed for datastore audit targets. A group or namespace symlink is reported as an anomaly, not traversed.
4. Output should avoid exposing absolute datastore paths by default; human-readable error details must not contain secrets, tokens, environment values or credentials.
5. API access (future) should use scoped tokens, validated TLS, and explicit endpoint allowlists. Do not normalize `--insecure` as a default.
6. Never infer source host from numeric VMID; the same VMID may exist in several locations.
7. A backup task marked OK, a successful group move or a CRC alone is not an integrity guarantee. Use digest checks, native PBS Verify and restore drills.
8. Any future repair needs approval, exact checksum matching, no-clobber writes, original owner/mode preservation, durable audit trail and separate final verification.
9. Encrypted chunks require appropriate handling; never assume local plaintext digest verification is possible without a decryption key.
10. Do not publish real manifests, hostnames, URLs, public/private IPs, credentials, VM names, access logs or actual client snapshots in bug reports/tests.

## Threat model

| Threat | Mitigation |
| --- | --- |
| Accidental modification of live datastore | No write capability in MVP; fail-closed defaults |
| Symlink traversal / malicious directory layout | Use `lstat`, reject symlink entries |
| Incorrect mapping of same VMID on two PVE nodes | Report duplicate identity scoped by namespace, never auto-move |
| Missing chunks silently surviving successful backups | Parse GC warnings and require native verify |
| Backup corruption caused by improvised chunk recovery | Planned guided workflow with digest checks and no-clobber atomic writes |
| Stolen or leaked API token | Future token-from-environment/keyring, redact logs, scoped permissions |
| False confidence from scan result | Explicit disclaimers: metadata scan != integrity check |

## Reporting a security issue

Use a private maintainer channel supported by the GitHub repository; if unavailable, open an issue **without confidential identifiers or an exploit** and request a secure disclosure channel. Never share real backup content.
