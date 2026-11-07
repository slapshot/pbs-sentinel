"""Command-line entrypoint. No mutating commands are exposed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .audit import audit_datastore, sort_findings
from .gc import read_gc_log


def _format_text(data: dict) -> str:
    stats = data["summary"]
    lines = [
        f"PBS Sentinel {__version__} (read-only metadata audit)",
        f"Groups: {stats['groups']} | Snapshots: {stats['snapshots']} "
        f"| Findings: {stats['findings']}",
    ]
    for group in data["groups"]:
        ns = group["namespace"] or "root"
        lines.append(
            f"  {ns}: {group['backup_type']}/{group['backup_id']}  "
            f"snapshots={len(group['snapshots'])}  owner={group['owner'] or '-'}"
        )
    for finding in data["findings"]:
        target = f"{finding.get('backup_type','')}/{finding.get('backup_id','')}".strip("/")
        suffix = f" [{target}]" if target else ""
        lines.append(
            f"  {finding['severity'].upper()} {finding['code']}{suffix}: "
            f"{finding['message']}"
        )
        if "chunk_digest" in finding:
            lines.append(f"    chunk={finding['chunk_digest']}")
            lines.append(f"    index={finding['index_path']}")
    lines.append("NOTICE: Inventory and GC logs do not prove snapshot integrity.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pbs-sentinel",
        description="Read-only PBS namespace inventory and GC-log triage.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="inspect a local PBS-shaped datastore")
    audit.add_argument("--datastore-path", type=Path, required=True,
                       help="existing datastore directory (read-only access)")
    audit.add_argument("--gc-log", type=Path,
                       help="optional exported PBS garbage-collection task log")
    audit.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        report = audit_datastore(args.datastore_path)
        if args.gc_log:
            report.findings.extend(read_gc_log(args.gc_log))
        sort_findings(report)
        data = report.as_dict()
    except (OSError, ValueError) as exc:
        print(f"pbs-sentinel: audit failed: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(_format_text(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
