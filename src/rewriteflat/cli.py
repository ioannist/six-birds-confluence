"""Tiny CLI for project-control checks."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .project_config import (
    CLAIM_REGISTRY_PATH,
    EXAMPLE_REGISTRY_PATH,
    RegistryValidationError,
    load_and_validate_registries,
)


def _print_status() -> int:
    result = load_and_validate_registries(CLAIM_REGISTRY_PATH, EXAMPLE_REGISTRY_PATH)

    print(f"name: rewriteflat")
    print(f"version: {__version__}")
    print(f"claim count: {len(result['claims'])}")
    print(f"example count: {len(result['examples'])}")
    print(f"claim registry: {Path(result['claim_registry_path'])}")
    print(f"example registry: {Path(result['example_catalog_path'])}")
    return 0


def _print_audit() -> int:
    try:
        result = load_and_validate_registries(CLAIM_REGISTRY_PATH, EXAMPLE_REGISTRY_PATH)
    except RegistryValidationError as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 1

    print(
        "audit ok: "
        f"claims={len(result['claims'])}, "
        f"examples={len(result['examples'])}, "
        f"cross_references={result['cross_reference_count']}"
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rewriteflat")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="print registry summary")
    subparsers.add_parser("audit", help="validate project registries")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        return _print_status()
    if args.command == "audit":
        return _print_audit()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
