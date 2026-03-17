"""Module entrypoint for ``python -m rewriteflat``."""

from . import cli


def main() -> int:
    return cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
