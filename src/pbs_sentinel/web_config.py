"""Server-only configuration for the PBS Sentinel web API.

Credentials must come from environment variables, never from frontend payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
_STORE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_ENV = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


@dataclass(frozen=True)
class Remote:
    identifier: str
    label: str
    base_url: str
    datastores: tuple[str, ...]
    token_id: str
    token_secret: str
    ca_bundle: str | None = None


@dataclass(frozen=True)
class WebConfig:
    access_token: str
    remotes: tuple[Remote, ...]


def load_config() -> WebConfig:
    """Validate configuration and resolve secrets before starting the API."""
    access_token = os.environ.get("PBS_SENTINEL_ACCESS_TOKEN", "")
    if len(access_token) < 32:
        raise ValueError("PBS_SENTINEL_ACCESS_TOKEN must have at least 32 characters.")
    path = os.environ.get("PBS_SENTINEL_CONFIG", "")
    if not path:
        raise ValueError("PBS_SENTINEL_CONFIG must point to a JSON configuration file.")
    config_path = Path(path)
    if config_path.is_symlink() or not config_path.is_file():
        raise ValueError("Configuration must be an existing non-symlink file.")
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("remotes"), list):
        raise ValueError("Configuration must contain a 'remotes' array.")

    remotes: list[Remote] = []
    seen: set[str] = set()
    for value in raw["remotes"]:
        if not isinstance(value, dict):
            raise ValueError("Each remote must be an object.")
        identifier = value.get("id")
        label = value.get("label")
        base_url = value.get("base_url")
        datastores = value.get("datastores")
        token_id = value.get("token_id")
        secret_env = value.get("token_secret_env")
        ca_bundle = value.get("ca_bundle")
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
            raise ValueError("Invalid remote ID.")
        if identifier in seen:
            raise ValueError("Duplicate remote ID.")
        seen.add(identifier)
        if not isinstance(label, str) or not 1 <= len(label) <= 100:
            raise ValueError("Remote label must contain 1–100 characters.")
        if not isinstance(base_url, str):
            raise ValueError("Remote base_url must be HTTPS.")
        url = urlsplit(base_url)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment or url.path not in ("", "/")):
            raise ValueError("Remote base_url must be an HTTPS origin.")
        try:
            _ = url.port
        except ValueError as exc:
            raise ValueError("Invalid remote port.") from exc
        if not isinstance(datastores, list) or not datastores or any(
            not isinstance(store, str) or not _STORE.fullmatch(store)
            for store in datastores
        ):
            raise ValueError("Each remote needs an explicit datastore allowlist.")
        if len(set(datastores)) != len(datastores):
            raise ValueError("Duplicate datastore in allowlist.")
        if not isinstance(token_id, str) or "!" not in token_id or not token_id.strip():
            raise ValueError("Remote requires a PBS API token identifier.")
        if not isinstance(secret_env, str) or not _ENV.fullmatch(secret_env):
            raise ValueError("Invalid token secret environment variable name.")
        secret = os.environ.get(secret_env, "")
        if not secret:
            raise ValueError(f"Missing remote token secret environment variable: {secret_env}")
        if ca_bundle is not None and (
            not isinstance(ca_bundle, str) or not Path(ca_bundle).is_file()
        ):
            raise ValueError("CA bundle must be an existing file.")
        remotes.append(Remote(identifier, label, base_url.rstrip("/"),
                              tuple(datastores), token_id, secret, ca_bundle))
    return WebConfig(access_token=access_token, remotes=tuple(remotes))
