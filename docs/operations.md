# Operations guide

PBS Sentinel is a web-first application. For architecture, environment variables, PBS token setup and how to start the API/UI, follow **[web-architecture.md](web-architecture.md)**.

**Deployment status:** development prototype only. Do not expose the current shared-token service directly to the public internet; production SSO/MFA, security headers, access control and hardened deployment remain tracked in issue #5.

## Offline CLI (support utility)

Clone the `dev` branch and install the Python package:

```bash
git clone https://github.com/slapshot/pbs-sentinel.git
cd pbs-sentinel
git switch dev
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[web]'
python -m unittest discover -s tests -v
```

To inspect an **exported/read-only** PBS datastore layout:

```bash
pbs-sentinel audit --datastore-path /path/to/datastore-copy --format text
```

To correlate a saved GC log and output structured data:

```bash
pbs-sentinel audit --datastore-path /path/to/datastore-copy \
  --gc-log /path/to/exported-gc.log --format json > report.json
```

The current offline CLI does not require network access, does not modify backups and does not verify raw data. The web dashboard uses separate read-only PBS management API calls on port 8007.

## Interpreting findings

- `root_group`: group lives in the root namespace. Informational, not necessarily incorrect.
- `duplicate_group_identity`: the same type/ID appears in multiple namespaces. It may be legitimate across independent PVE hosts.
- `missing_chunk`: referenced by a saved GC log. This is historical log evidence, not a current filesystem check.
- `unreadable_path`, `symlink_entry`: suspicious or inaccessible paths, never followed or repaired.

**A successful backup, migration or metadata audit does not establish integrity.** Run native PBS Verify and regular isolated restore tests.

Do not run experimental programs as root on production backup servers. Do not commit production connection configs, API secrets or actual backup files.

## Native documentation

- [Official PBS API viewer](https://pbs.proxmox.com/docs/api-viewer/index.html)
- [PBS backup client](https://pbs.proxmox.com/docs/backup-client.html)
- [PBS permissions and API tokens](https://pbs.proxmox.com/docs/user-management.html)
