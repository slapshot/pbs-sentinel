# Contributing

Thanks for helping improve PBS Sentinel. Safety comes before feature count.

1. Work against the `dev` branch. Open a focused pull request with the motivation, risk, test coverage and any changes to CLI output.
2. Use synthetic fixtures in tests. Never commit hostnames, actual backup indices/chunks, IP addresses, token secrets, backup credentials or customer data.
3. Read [docs/security.md](docs/security.md) before proposing any operation that changes a datastore.
4. New filesystem mutations must be an explicit proposal with dry-run, preflight, no-clobber semantics and an auditable rollback/recovery story. **No self-healing-by-deletion.**
5. A metadata audit is not a native PBS verification; document limits in help text and output.
6. Run `python -m unittest discover -s tests -v` on `dev` before proposing changes.
7. Favor Python standard library for the current milestone; dependencies require a documented benefit and security review.

This independent project is not affiliated with Proxmox Server Solutions GmbH.
