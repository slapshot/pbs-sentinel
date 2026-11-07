"""Uvicorn entrypoint. The default listener is loopback-only."""

from __future__ import annotations

import uvicorn

from .web_api import create_app

app = create_app


def main() -> None:
    # Explicitly instantiate only when the service starts; no config during CLI import.
    uvicorn.run(create_app(), host="127.0.0.1", port=8787, proxy_headers=False)


if __name__ == "__main__":
    main()
