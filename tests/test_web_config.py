"""Server configuration must reject untrusted URLs and missing credentials."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pbs_sentinel.web_config import load_config


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "remotes.json"
        self.remote = {
            "id": "lab-pbs",
            "label": "Lab PBS",
            "base_url": "https://pbs.example.test:8007",
            "datastores": ["backup"],
            "token_id": "sentinel@pbs!reader",
            "token_secret_env": "SENTINEL_TEST_PBS_SECRET",
        }

    def load(self, **remote_changes):
        obj = self.remote | remote_changes
        self.path.write_text(json.dumps({"remotes": [obj]}), encoding="utf-8")
        with patch.dict(os.environ, {
            "PBS_SENTINEL_ACCESS_TOKEN": "a" * 40,
            "PBS_SENTINEL_CONFIG": str(self.path),
            "SENTINEL_TEST_PBS_SECRET": "pbs-secret",
        }):
            return load_config()

    def test_valid(self) -> None:
        cfg = self.load()
        self.assertEqual(cfg.remotes[0].base_url, "https://pbs.example.test:8007")
        self.assertEqual(cfg.remotes[0].token_secret, "pbs-secret")

    def test_http_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.load(base_url="http://pbs.example.test:8007")

    def test_embedded_credentials_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.load(base_url="https://root:pass@pbs.example.test:8007")

    def test_url_path_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.load(base_url="https://pbs.example.test:8007/secret")

    def test_missing_datastore_allowlist_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.load(datastores=[])

    def test_no_token_error(self) -> None:
        with patch.dict(os.environ, {"PBS_SENTINEL_ACCESS_TOKEN": "short"}):
            with self.assertRaises(ValueError):
                load_config()


if __name__ == "__main__":
    unittest.main()
