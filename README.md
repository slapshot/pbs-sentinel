# PBS Sentinel

**Backup integrity, namespace hygiene and recovery planning for Proxmox Backup Server.**

PBS Sentinel is a community-driven, safety-first operations toolkit for administrators who run multiple Proxmox VE and Proxmox Backup Server instances. It addresses a specific gap: *understanding whether backup groups are correctly attributed and which data needs attention before attempting a recovery.*

> **Status:** early-stage project. The `main` branch contains the design and operational documentation. Initial read-only code is developed on `dev`. Do not use it as a substitute for PBS verification or restore tests.

## Why it exists

A backup task showing *OK* does not prove that every referenced chunk is available. Backups can also be hard to identify when several independent PVE hosts reuse the same VMID, or when older snapshots live in the root namespace while newer ones live under host-specific namespaces.

PBS Sentinel aims to help operators **audit first, plan second, and change nothing without explicit approval**.

## What is available

The documentation describes a staged implementation. The first development milestone is an **offline, read-only datastore audit** with structured output and optional analysis of PBS garbage-collection logs. Namespace moves, cross-datastore chunk recovery, remote API discovery and restore drills remain proposed capabilities, **not completed features**.

See [architecture](docs/architecture.md), [security](docs/security.md), [roadmap](docs/roadmap.md), [operations](docs/operations.md), [comparison with other tools](docs/comparison.md) and [data model](docs/data-model.md).

## How it differs

- **[Pulse](https://github.com/rcourtman/Pulse)** focuses on observability, monitoring and alerts across infrastructure; PBS Sentinel focuses on *offline forensic audit, evidence-led recovery plans and namespace provenance*.
- **[ProxSave](https://github.com/tis24dev/proxsave)** safeguards host configuration and guides host rebuilds; PBS Sentinel focuses on PBS *backup groups, snapshot integrity evidence and chunk availability*.
- **[pmx](https://github.com/fivetwenty-io/proxmox-cli)** provides a broad API CLI for Proxmox products; PBS Sentinel aims to provide *opinionated, multi-step safety checks* on top of native capabilities.
- **[foundata.proxmox](https://github.com/foundata/ansible-collection-proxmox)** provides Ansible automation for configuring Proxmox components; PBS Sentinel is intended for *backup audits and guarded recovery workflows*, not general provisioning.

These tools are complementary, not competitors. See [comparison](docs/comparison.md) for a feature/status matrix.

## Design principles

1. Read-only by default; destructive operations must never be the default.
2. Use Proxmox APIs and native CLI tools when available; never rewrite index files.
3. Never infer machine identity solely from VMID; preserve namespace and repository context.
4. No private infrastructure data or credentials in the repository, fixtures or logs.
5. Machine-readable evidence, reproducible tests and clear limitations.

## Branch policy

- **`main`**: documentation and subsequently reviewed, stable releases.
- **`dev`**: working code, tests and experimental non-destructive features.

## License and trademarks

Apache-2.0 (see [LICENSE](LICENSE)). This is an independent community project, **not affiliated with or endorsed by Proxmox Server Solutions GmbH**. Proxmox is a trademark of its respective owner.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Security-sensitive findings should be reported privately, not through public issues containing hostnames, credentials, snapshots or internal IPs.
