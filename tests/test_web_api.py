"""Web API uses a fixed read-only PBS proxy and never sends secrets to users."""

from __future__ import annotations

import json
import unittest

from fastapi.testclient import TestClient
import httpx

from pbs_sentinel.web_api import create_app
from pbs_sentinel.web_config import Remote, WebConfig


class APITests(unittest.TestCase):
    def setUp(self) -> None:
        self.requests: list[httpx.Request] = []
        self.secret = "super-private-pbs-token"
        self.local_token = "local-only-access-token-" + "x" * 20

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            if request.url.path.endswith("/groups"):
                data = [{"backup-type": "vm", "backup-id": "180", "backup-count": 8}]
            elif request.url.path.endswith("/namespace"):
                data = [{"ns": "pve4-standalone"}]
            elif request.url.path.endswith("/status"):
                data = {"total": 100, "used": 20}
            elif request.url.path.endswith("/admin/datastore"):
                data = [{"store": "backup"}, {"store": "not-allowed"}]
            else:
                data = {"version": "4.2.9"}
            return httpx.Response(200, json={"data": data})

        self.transport = httpx.MockTransport(handler)
        cfg = WebConfig(
            access_token=self.local_token,
            remotes=(Remote(
                identifier="pbs3",
                label="Test Backup Server",
                base_url="https://pbs3.example.test:8007",
                datastores=("backup",),
                token_id="audit@pbs!sentinel",
                token_secret=self.secret,
            ),),
        )
        self.client = TestClient(create_app(cfg, transport=self.transport))
        self.headers = {"Authorization": "Bearer " + self.local_token}

    def test_health_is_public_but_metadata_is_protected(self) -> None:
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/instances").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/instances",
                                         headers={"Authorization": "Bearer wrong"}).status_code, 401)

    def test_list_instances_does_not_leak_secrets_or_url(self) -> None:
        response = self.client.get("/api/v1/instances", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        body = response.text
        self.assertIn("Test Backup Server", body)
        self.assertNotIn(self.secret, body)
        self.assertNotIn("pbs3.example.test", body)
        self.assertNotIn("audit@pbs", body)

    def test_groups_namespaced_get_only(self) -> None:
        response = self.client.get(
            "/api/v1/instances/pbs3/datastores/backup/groups?ns=pve4-standalone",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["backup-id"], "180")
        self.assertEqual(self.requests[0].method, "GET")
        self.assertEqual(self.requests[0].url.params["ns"], "pve4-standalone")
        self.assertEqual(self.requests[0].headers["authorization"],
                         f"PBSAPIToken audit@pbs!sentinel:{self.secret}")

    def test_unknown_store_rejected_without_upstream_call(self) -> None:
        response = self.client.get(
            "/api/v1/instances/pbs3/datastores/forbidden/status", headers=self.headers
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.requests, [])

    def test_invalid_namespace(self) -> None:
        response = self.client.get(
            "/api/v1/instances/pbs3/datastores/backup/groups?ns=../escape",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.requests, [])

    def test_datastores_filtered_to_allowlist(self) -> None:
        response = self.client.get(
            "/api/v1/instances/pbs3/datastores", headers=self.headers
        )
        self.assertEqual(response.json()["items"], [{"store": "backup"}])

    def test_methods_are_read_only(self) -> None:
        response = self.client.post(
            "/api/v1/instances/pbs3/datastores/backup/groups", headers=self.headers
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.requests, [])

    def test_unreachable_upstream_is_sanitized(self) -> None:
        def fail(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("secret diagnostic", request=request)
        cfg = WebConfig(
            access_token=self.local_token,
            remotes=(Remote("pbs", "PBS", "https://private.example:8007",
                            ("backup",), "user@pbs!reader", "sensitive-secret"),),
        )
        test_client = TestClient(create_app(cfg, transport=httpx.MockTransport(fail)))
        response = test_client.get(
            "/api/v1/instances/pbs/datastores/backup/status", headers=self.headers
        )
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("secret", response.text)
        self.assertNotIn("private.example", response.text)


if __name__ == "__main__":
    unittest.main()
