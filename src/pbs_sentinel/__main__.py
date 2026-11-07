"""Allow python -m pbs_sentinel."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
