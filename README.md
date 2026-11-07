# PBS Sentinel

**Web-first backup visibility and integrity investigation for Proxmox Backup Server.**

PBS Sentinel is a self-hosted web application for operators managing multiple Proxmox Backup Server instances. It adds a specific layer around **backup provenance, namespace organization, missing-chunk investigations, and reviewed recovery plans**. It is an independent open-source project, not affiliated with Proxmox.

> **Status: pre-alpha.** On `dev` a read-only React dashboard and FastAPI gateway are under development, alongside an offline diagnostic CLI. `main` contains the public documentation. No stable release or internet-ready authentication service is available yet.

## The problem

A successful PBS backup task is not proof of complete restoreability. After namespace migrations, multiple hosts can also share VMIDs while backup archives have different owners or histories. In a missing-chunk incident, the operator may need to correlate GC logs, indexes, namespaces and alternate datastores.

**PBS Sentinel connects the evidence and presents it through a web UI.** It will never silently delete archives or claim a metadata scan proves integrity.

## Architecture

```text
Authorized browser --HTTPS--> Reverse proxy + authentication
                                        |
                        React dashboard / FastAPI
                                        |
                             PBS API :8007 (GET)
                            /         |         \
                         PBS A       PBS B      PBS N
```

The browser never connects directly to PBS or receives PBS API tokens. Server-side instance URLs are allowlisted; backend tokens are held in environment secrets. The initial FastAPI MVP binds to `127.0.0.1:8787` and requires an independent bearer token; **do not expose it on the internet without a hardened login gateway (SSO/MFA) and reverse proxy**.

See [web architecture and development guide](docs/web-architecture.md).

## What exists on `dev`

- Read-only API: configured instances, datastore usage, namespaces, backup groups and PBS version.
- React/Vite web console for selecting an instance/datastore/namespace and viewing group metadata.
- Local CLI `pbs-sentinel audit` for datastore inventory and saved GC missing-chunk warnings.
- Synthetic tests and CI.
- No automatic namespace moves, chunk repair, backup deletion, remote shell or verify-job execution.

## Roadmap

Read-only fleet inventory → task/GC/verify incident overview → evidence-based missing-chunk lookup → reviewed recovery planning → optional controlled executor and restore drills.

See [roadmap](docs/roadmap.md), [security](docs/security.md), [architecture](docs/architecture.md), [API](docs/web-architecture.md) and [data model](docs/data-model.md).

## How is it different?

- **Proxmox Datacenter Manager** provides centralized management, resource monitoring and multi-cluster operations. PBS Sentinel intentionally focuses on *backup integrity evidence, namespace provenance and recovery workflow design*.
- **Pulse** focuses on monitoring and alerting; Sentinel on investigation and operator-reviewed remediation plans.
- **ProxSave** focuses on host configuration recovery; Sentinel on PBS backup group and chunk incidents.
- **pmx / Ansible** offer broad API or automation foundations; Sentinel adds domain-specific safety and reasoning, not a replacement for those tools.

Read the detailed [comparison with existing projects](docs/comparison.md).

## Development

```bash
git clone https://github.com/slapshot/pbs-sentinel.git
cd pbs-sentinel && git switch dev
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[web]'
python -m unittest discover -s tests -v
```

For the web UI and connection configuration, follow [docs/web-architecture.md](docs/web-architecture.md). The CLI can be run independently.

## Branches and license

- `main`: project documentation and later stable releases.
- `dev`: active development, tests and pre-release prototypes.
- Licensed under **Apache-2.0** ([LICENSE](LICENSE)). Proxmox trademarks belong to their owners.

Please do not include real backup data, infrastructure secrets, VM/customer names or private addresses in issues. See [contributing](CONTRIBUTING.md).
