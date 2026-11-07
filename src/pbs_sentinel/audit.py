"""Read-only filesystem inventory of Proxmox Backup Server datastore layouts.

This is a *metadata* audit. It never opens backup archives or validates chunks.
No user-provided path is executed or written to.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re

BACKUP_TYPES = ("ct", "host", "vm")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


@dataclass(frozen=True)
class Group:
    namespace: str
    backup_type: str
    backup_id: str
    owner: str | None
    snapshots: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    namespace: str = ""
    backup_type: str = ""
    backup_id: str = ""
    message: str = ""
    chunk_digest: str | None = None
    index_path: str | None = None

    def as_dict(self) -> dict:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass
class AuditResult:
    groups: list[Group] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def add_finding(self, code: str, severity: str, namespace: str,
                    backup_type: str = "", backup_id: str = "",
                    message: str = "") -> None:
        self.findings.append(Finding(code, severity, namespace, backup_type,
                                     backup_id, message))

    def as_dict(self) -> dict:
        return {
            "schema_version": 1,
            "groups": [group.as_dict() for group in self.groups],
            "findings": [finding.as_dict() for finding in self.findings],
            "summary": {
                "groups": len(self.groups),
                "snapshots": sum(len(group.snapshots) for group in self.groups),
                "findings": len(self.findings),
            },
        }


def _children(path: Path, result: AuditResult, namespace: str,
              backup_type: str = "", backup_id: str = "") -> list[Path]:
    try:
        return sorted(path.iterdir(), key=lambda child: child.name)
    except OSError:
        result.add_finding("unreadable_path", "error", namespace,
                           backup_type, backup_id,
                           "Unable to enumerate a directory.")
        return []


def _scan_groups(base: Path, namespace: str, result: AuditResult) -> None:
    for backup_type in BACKUP_TYPES:
        typed = base / backup_type
        if typed.is_symlink():
            result.add_finding("symlink_entry", "warning", namespace,
                               backup_type, message="Backup type path is a symlink.")
            continue
        if not typed.is_dir():
            continue
        for group_dir in _children(typed, result, namespace, backup_type):
            if group_dir.is_symlink():
                result.add_finding("symlink_entry", "warning", namespace, backup_type,
                                   group_dir.name, "Group path is a symlink.")
                continue
            if not group_dir.is_dir():
                continue

            owner: str | None = None
            owner_file = group_dir / "owner"
            if owner_file.is_symlink():
                result.add_finding("symlink_entry", "warning", namespace, backup_type,
                                   group_dir.name, "Owner file is a symlink.")
            elif owner_file.is_file():
                try:
                    # Owner file should be tiny. Never read an unbounded special file.
                    with owner_file.open("rb") as handle:
                        raw = handle.read(4097)
                    if len(raw) > 4096:
                        raise ValueError("Owner file unexpectedly large")
                    owner = raw.decode("utf-8").strip() or None
                except (OSError, UnicodeError, ValueError):
                    result.add_finding("unreadable_path", "warning", namespace,
                                       backup_type, group_dir.name,
                                       "Unable to read group owner metadata.")

            snapshots: list[str] = []
            for item in _children(group_dir, result, namespace, backup_type,
                                  group_dir.name):
                if item.is_symlink():
                    result.add_finding("symlink_entry", "warning", namespace,
                                       backup_type, group_dir.name,
                                       "Group contains a symlink entry.")
                elif TIMESTAMP.fullmatch(item.name) and item.is_dir():
                    snapshots.append(item.name)

            result.groups.append(Group(namespace, backup_type, group_dir.name,
                                       owner, snapshots))
            if namespace == "":
                result.add_finding("root_group", "info", namespace, backup_type,
                                   group_dir.name,
                                   "Backup group resides in root namespace.")


def _walk_namespaces(base: Path, namespace: str, result: AuditResult) -> None:
    _scan_groups(base, namespace, result)
    ns_root = base / "ns"
    if ns_root.is_symlink():
        result.add_finding("symlink_entry", "warning", namespace,
                           message="Namespace directory is a symlink.")
        return
    if not ns_root.is_dir():
        return
    for child in _children(ns_root, result, namespace):
        child_ns = f"{namespace}/{child.name}" if namespace else child.name
        if child.is_symlink():
            result.add_finding("symlink_entry", "warning", child_ns,
                               message="Namespace path is a symlink.")
        elif child.is_dir():
            _walk_namespaces(child, child_ns, result)


def audit_datastore(root: Path) -> AuditResult:
    """Inventory groups and backup snapshot directory names, without writes."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Datastore path must be an existing non-symlink directory.")

    result = AuditResult()
    _walk_namespaces(root, "", result)
    result.groups.sort(key=lambda g: (g.namespace, g.backup_type, g.backup_id))

    collisions: dict[tuple[str, str], set[str]] = {}
    for group in result.groups:
        collisions.setdefault((group.backup_type, group.backup_id), set()).add(
            group.namespace
        )
    for group in result.groups:
        namespaces = collisions[(group.backup_type, group.backup_id)]
        if len(namespaces) > 1:
            locations = ", ".join("root" if n == "" else n for n in sorted(namespaces))
            result.add_finding("duplicate_group_identity", "warning",
                               group.namespace, group.backup_type, group.backup_id,
                               f"Same group ID appears in multiple namespaces: {locations}.")

    return result


def sort_findings(result: AuditResult) -> None:
    result.findings.sort(key=lambda f: (
        f.severity, f.code, f.namespace, f.backup_type, f.backup_id,
        f.chunk_digest or "", f.index_path or "", f.message,
    ))
