"""Isolated tests; never access a production datastore."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pbs_sentinel.audit import audit_datastore, sort_findings


class DatastoreAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "store"
        self.root.mkdir()

    def group(self, namespace: str, backup_type: str, backup_id: str,
              snapshots: tuple[str, ...] = ()) -> Path:
        base = self.root
        for component in namespace.split("/") if namespace else ():
            base = base / "ns" / component
        path = base / backup_type / backup_id
        path.mkdir(parents=True)
        (path / "owner").write_text("root@pam\n", encoding="utf-8")
        for snap in snapshots:
            (path / snap).mkdir()
        return path

    def test_empty_datastore(self) -> None:
        report = audit_datastore(self.root)
        self.assertEqual(report.as_dict()["summary"]["groups"], 0)

    def test_root_and_namespace_collision(self) -> None:
        snap = "2026-11-06T22:04:23Z"
        self.group("", "vm", "180", (snap,))
        self.group("pve4-standalone", "vm", "180", (snap,))
        report = audit_datastore(self.root)
        self.assertEqual(len(report.groups), 2)
        self.assertEqual(sum(len(g.snapshots) for g in report.groups), 2)
        self.assertEqual(
            [f.code for f in report.findings].count("root_group"), 1
        )
        self.assertEqual(
            [f.code for f in report.findings].count("duplicate_group_identity"), 2
        )
        self.assertEqual(report.groups[0].owner, "root@pam")

    def test_nested_namespace(self) -> None:
        self.group("site-a/node-1", "ct", "101",
                   ("2026-11-07T01:00:00Z",))
        report = audit_datastore(self.root)
        self.assertEqual(len(report.groups), 1)
        self.assertEqual(report.groups[0].namespace, "site-a/node-1")
        self.assertEqual(report.as_dict()["summary"]["snapshots"], 1)

    def test_same_id_different_type_not_collision(self) -> None:
        self.group("a", "ct", "101")
        self.group("b", "vm", "101")
        result = audit_datastore(self.root)
        self.assertNotIn("duplicate_group_identity", [f.code for f in result.findings])

    def test_group_symlink_not_followed(self) -> None:
        target = Path(self.tmp.name) / "outside"
        target.mkdir()
        typed = self.root / "vm"
        typed.mkdir()
        (typed / "999").symlink_to(target, target_is_directory=True)
        result = audit_datastore(self.root)
        self.assertEqual(result.groups, [])
        self.assertIn("symlink_entry", [f.code for f in result.findings])

    def test_namespace_symlink_not_followed(self) -> None:
        target = Path(self.tmp.name) / "outside"
        (target / "vm" / "999").mkdir(parents=True)
        (self.root / "ns").mkdir()
        (self.root / "ns" / "external").symlink_to(target, target_is_directory=True)
        result = audit_datastore(self.root)
        self.assertEqual(result.groups, [])
        self.assertIn("symlink_entry", [f.code for f in result.findings])

    def test_root_symlink_rejected(self) -> None:
        link = Path(self.tmp.name) / "link"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            audit_datastore(link)

    def test_missing_owner_is_not_fatal(self) -> None:
        path = self.group("one", "host", "node")
        (path / "owner").unlink()
        result = audit_datastore(self.root)
        self.assertIsNone(result.groups[0].owner)
        sort_findings(result)
        self.assertEqual(result.as_dict()["summary"]["groups"], 1)


if __name__ == "__main__":
    unittest.main()
