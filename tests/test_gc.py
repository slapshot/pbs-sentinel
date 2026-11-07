"""Parser and input-boundary tests for offline GC logs."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pbs_sentinel.gc import parse_gc_log, read_gc_log


class GCLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chunk = "a" * 64
        self.warning = (
            "warning: unable to access non-existent chunk "
            f'{self.chunk}, required by "/srv/pbs/ns/site/vm/180/'
            '2026-11-06T22:04:23Z/drive-scsi0.img.fidx"'
        )

    def test_parse_and_deduplicate(self) -> None:
        findings = parse_gc_log(self.warning + "\n" + self.warning)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "missing_chunk")
        self.assertEqual(findings[0].chunk_digest, self.chunk)
        self.assertIn("vm/180", findings[0].index_path)

    def test_unrelated_lines_do_not_match(self) -> None:
        self.assertEqual(parse_gc_log("TASK WARNINGS: 4\nGarbage removed"), [])

    def test_invalid_digest_does_not_match(self) -> None:
        self.assertEqual(parse_gc_log(self.warning.replace(self.chunk, "abcd")), [])

    def test_regular_file(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "gc.log"
            log.write_text(self.warning, encoding="utf-8")
            self.assertEqual(len(read_gc_log(log)), 1)

    def test_symlink_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.write_text(self.warning, encoding="utf-8")
            alias = Path(tmp) / "alias"
            alias.symlink_to(target)
            with self.assertRaises(ValueError):
                read_gc_log(alias)


if __name__ == "__main__":
    unittest.main()
