"""CLI output and fail-closed tests."""

from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pbs_sentinel.cli import main


class CLITests(unittest.TestCase):
    def test_json_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ct" / "101" / "2026-11-07T08:00:00Z").mkdir(parents=True)
            stream = StringIO()
            with redirect_stdout(stream):
                rc = main(["audit", "--datastore-path", str(root),
                           "--format", "json"])
            self.assertEqual(rc, 0)
            report = json.loads(stream.getvalue())
            self.assertEqual(report["summary"]["groups"], 1)
            self.assertEqual(report["summary"]["snapshots"], 1)
            self.assertEqual(report["findings"][0]["code"], "root_group")

    def test_missing_datastore_fails(self) -> None:
        stream = StringIO()
        with redirect_stderr(stream):
            rc = main(["audit", "--datastore-path", "/nonexistent/sentinel-test"])
        self.assertEqual(rc, 2)
        self.assertIn("audit failed", stream.getvalue())

    def test_json_with_missing_chunk_from_gc(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "store"
            root.mkdir()
            gc = Path(tmp) / "gc.log"
            digest = "f" * 64
            gc.write_text(
                f'warning: unable to access non-existent chunk {digest}, '
                'required by "/data/vm/42/date/drive.img.fidx"\n',
                encoding="utf-8",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                rc = main(["audit", "--datastore-path", str(root),
                           "--gc-log", str(gc), "--format", "json"])
            report = json.loads(stream.getvalue())
            self.assertEqual(rc, 0)
            self.assertEqual(report["findings"][0]["chunk_digest"], digest)


if __name__ == "__main__":
    unittest.main()
