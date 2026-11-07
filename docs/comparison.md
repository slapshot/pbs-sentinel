# How PBS Sentinel differs from existing tools

PBS Sentinel is **not** a general-purpose Proxmox controller, dashboard, or replacement for the official Proxmox Backup Server verification tool.

We reviewed the publicly documented purposes of these projects in November 2026; product scope may change. This is an **intent and scope comparison**, not a claim that other tools cannot perform any of these operations.

| Project | Main focus (documented) | Where PBS Sentinel is different |
| --- | --- | --- |
| [Pulse](https://github.com/rcourtman/Pulse) | Self-hosted, real-time monitoring and alerting for Proxmox and other platforms | Evidence-focused, operator-initiated **forensics of namespace/group provenance** and **guided response to missing-chunk incidents**, rather than another monitoring dashboard |
| [ProxSave](https://github.com/tis24dev/proxsave) | Backup and guided disaster recovery of **PVE/PBS host configuration** | Audit and recovery planning for **PBS snapshots, indexes, chunk availability** and namespace assignment, not host configuration backup |
| [pmx](https://github.com/fivetwenty-io/proxmox-cli) | Broad CLI access to PVE/PBS/PDM APIs, tasks and operational actions | Opinionated multi-step workflow: **collect evidence -> assess risk -> generate an operator-reviewed plan**; does not compete on API endpoint coverage |
| [foundata.proxmox](https://github.com/foundata/ansible-collection-proxmox) | Ansible configuration/automation for multiple Proxmox products | Forensic reporting and backup integrity triage rather than provisioning and config convergence |
| [Proxmox Backup Server](https://pbs.proxmox.com/docs/) | Native backup, deduplication, verify, GC, sync, namespace and restore operations | Combines native findings into a **cross-host investigation**, without replacing native verify or creating its own backup format |

## A realistic incident

1. A verify or GC task reports that an index references a missing chunk.
2. The operator wants to know **which snapshot/namespace/group** references it and whether the **same chunk is available in an alternate datastore**.
3. The tool records evidence, validates candidates, and prepares a **non-destructive recovery plan**.
4. Any future repair step requires explicit approval; final validation uses native PBS verification and an isolated restore drill.

**Implemented in the initial `dev` milestone:** offline read-only inventory plus extraction of missing-chunk references from saved GC logs; output as JSON or human-readable text.

**Not yet implemented:** remote discovery, multi-datastore search, cross-store transfer, mutation, remediation, restore drills, ongoing monitoring, UI.

## Why not just run Ansible/pmx?

We should reuse those tools and the native PBS client where appropriate. PBS Sentinel's value is a *specific safety policy, audit model and reproducible response workflow*, not reimplementing every Proxmox API.

## Research references

- [Pulse](https://github.com/rcourtman/Pulse)
- [ProxSave](https://github.com/tis24dev/proxsave)
- [pmx](https://github.com/fivetwenty-io/proxmox-cli)
- [foundata.proxmox](https://github.com/foundata/ansible-collection-proxmox)
- [Official Proxmox Backup Server docs](https://pbs.proxmox.com/docs/)
