"""Read-only HTTP API for the central PBS Sentinel web application.

No client-supplied upstream URLs. No PBS tokens cross the server/browser boundary.
"""

from __future__ import annotations

import hmac
import re
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query

from . import __version__
from .web_config import Remote, WebConfig, load_config


_NAMESPACE = re.compile(r"(?:[A-Za-z0-9_.-]+)(?:/[A-Za-z0-9_.-]+){0,7}\Z")


def create_app(
    config: WebConfig | None = None,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Construct the app. Tests can inject an isolated HTTP transport."""
    settings = config if config is not None else load_config()
    remotes = {remote.identifier: remote for remote in settings.remotes}
    app = FastAPI(
        title="PBS Sentinel API",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    def require_access(authorization: str | None = Header(default=None)) -> None:
        if (authorization is None or not authorization.startswith("Bearer ")
                or not hmac.compare_digest(
                    authorization.removeprefix("Bearer "), settings.access_token
                )):
            raise HTTPException(status_code=401, detail="Unauthorized",
                                headers={"WWW-Authenticate": "Bearer"})

    def get_remote(remote_id: str) -> Remote:
        remote = remotes.get(remote_id)
        if remote is None:
            raise HTTPException(status_code=404, detail="Unknown instance")
        return remote

    def require_store(remote: Remote, store: str) -> None:
        if store not in remote.datastores:
            raise HTTPException(status_code=404, detail="Unknown datastore")

    async def upstream_get(
        remote: Remote, path: str, params: dict[str, str] | None = None
    ) -> Any:
        timeout = httpx.Timeout(15.0, connect=5.0)
        try:
            async with httpx.AsyncClient(
                timeout=timeout, verify=remote.ca_bundle or True,
                follow_redirects=False, trust_env=False, transport=transport
            ) as client:
                response = await client.get(
                    f"{remote.base_url}/api2/json/{path}",
                    headers={
                        "Authorization":
                            f"PBSAPIToken {remote.token_id}:{remote.token_secret}"
                    },
                    params=params,
                )
                response.raise_for_status()
                if len(response.content) > 8_000_000:
                    raise HTTPException(502, detail="Upstream response too large")
                payload = response.json()
        except httpx.HTTPError as exc:
            # Deliberately don't return upstream URLs, tokens or exception strings.
            raise HTTPException(502, detail="PBS upstream request failed") from exc
        except (ValueError, TypeError) as exc:
            raise HTTPException(502, detail="Invalid PBS upstream response") from exc
        if not isinstance(payload, dict) or "data" not in payload:
            raise HTTPException(502, detail="Invalid PBS upstream response")
        return payload["data"]

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/v1/instances", dependencies=[Depends(require_access)])
    def instances() -> dict[str, list[dict[str, Any]]]:
        return {
            "items": [
                {
                    "id": r.identifier,
                    "label": r.label,
                    "datastores": list(r.datastores),
                }
                for r in settings.remotes
            ]
        }

    @app.get("/api/v1/instances/{remote_id}/version",
             dependencies=[Depends(require_access)])
    async def version(remote_id: str) -> dict[str, Any]:
        remote = get_remote(remote_id)
        return {"instance": remote.identifier,
                "data": await upstream_get(remote, "version")}

    @app.get("/api/v1/instances/{remote_id}/datastores",
             dependencies=[Depends(require_access)])
    async def datastores(remote_id: str) -> dict[str, Any]:
        remote = get_remote(remote_id)
        items = await upstream_get(remote, "admin/datastore")
        if not isinstance(items, list):
            raise HTTPException(502, detail="Unexpected PBS datastore response")
        allowed = set(remote.datastores)
        return {
            "instance": remote.identifier,
            "items": [
                item for item in items
                if isinstance(item, dict)
                and (item.get("store") or item.get("name")) in allowed
            ],
        }

    @app.get("/api/v1/instances/{remote_id}/datastores/{store}/status",
             dependencies=[Depends(require_access)])
    async def status(remote_id: str, store: str) -> dict[str, Any]:
        remote = get_remote(remote_id)
        require_store(remote, store)
        return {
            "instance": remote.identifier,
            "datastore": store,
            "data": await upstream_get(
                remote, f"admin/datastore/{quote(store, safe='')}/status"
            ),
        }

    @app.get("/api/v1/instances/{remote_id}/datastores/{store}/namespaces",
             dependencies=[Depends(require_access)])
    async def namespaces(remote_id: str, store: str) -> dict[str, Any]:
        remote = get_remote(remote_id)
        require_store(remote, store)
        return {
            "instance": remote.identifier, "datastore": store,
            "data": await upstream_get(
                remote, f"admin/datastore/{quote(store, safe='')}/namespace"
            ),
        }

    @app.get("/api/v1/instances/{remote_id}/datastores/{store}/groups",
             dependencies=[Depends(require_access)])
    async def groups(
        remote_id: str, store: str,
        ns: str = Query(default="", max_length=255),
    ) -> dict[str, Any]:
        remote = get_remote(remote_id)
        require_store(remote, store)
        if ns and (not _NAMESPACE.fullmatch(ns) or any(
            part in (".", "..") for part in ns.split("/")
        )):
            raise HTTPException(422, detail="Invalid namespace")
        params = {"ns": ns} if ns else None
        return {
            "instance": remote.identifier, "datastore": store,
            "namespace": ns,
            "data": await upstream_get(
                remote, f"admin/datastore/{quote(store, safe='')}/groups",
                params=params,
            ),
        }

    return app
