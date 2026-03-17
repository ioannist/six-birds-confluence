"""YAML registry loading and lightweight schema validation."""

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[2]
CLAIM_REGISTRY_PATH = ROOT / "project" / "claim_registry.yaml"
EXAMPLE_REGISTRY_PATH = ROOT / "project" / "example_catalog.yaml"

MIN_CLAIMS = 6
MIN_EXAMPLES = 8

CLAIM_REQUIRED = {
    "id",
    "label",
    "kind",
    "scope_model",
    "status",
    "priority",
    "hypotheses",
    "target_phases",
    "evidence_targets",
    "related_example_ids",
}
EXAMPLE_REQUIRED = {
    "id",
    "label",
    "domain",
    "status",
    "target_phases",
    "expected_labels",
}


class RegistryValidationError(ValueError):
    """Raised when registry data does not satisfy lightweight constraints."""


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise RegistryValidationError(f"missing registry file: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise RegistryValidationError(f"registry must be a mapping: {path}")

    return data


def _require_keys(payload: Dict[str, Any], path: str, required: set[str]) -> None:
    missing = sorted(required - payload.keys())
    if missing:
        raise RegistryValidationError(f"{path}: missing keys {missing}")


def _validate_claims(claims: List[Any], example_ids: set[str]) -> Tuple[List[Dict[str, Any]], int]:
    if not isinstance(claims, list):
        raise RegistryValidationError("claims must be a list")

    validated: List[Dict[str, Any]] = []
    claim_ids: set[str] = set()
    cross_ref_count = 0

    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            raise RegistryValidationError(f"claim at index {index} is not a mapping")

        _require_keys(claim, f"claim[{index}]", CLAIM_REQUIRED)

        claim_id = claim["id"]
        if not isinstance(claim_id, str) or not claim_id:
            raise RegistryValidationError(f"claim[{index}] has invalid id")
        if claim_id in claim_ids:
            raise RegistryValidationError(f"duplicate claim id: {claim_id}")
        claim_ids.add(claim_id)

        for required_key in ("hypotheses", "target_phases", "evidence_targets", "related_example_ids"):
            value = claim[required_key]
            if not isinstance(value, list):
                raise RegistryValidationError(
                    f"claim[{index}] field '{required_key}' must be a list"
                )

        related = claim["related_example_ids"]
        for example_id in related:
            if not isinstance(example_id, str):
                raise RegistryValidationError(
                    f"claim[{index}] related_example_ids entry must be a string"
                )
            if example_id not in example_ids:
                raise RegistryValidationError(
                    f"claim[{index}] refers to unknown example id: {example_id}"
                )
            cross_ref_count += 1

        validated.append(claim)

    return validated, cross_ref_count


def _validate_examples(examples: List[Any]) -> Tuple[List[Dict[str, Any]], set[str]]:
    if not isinstance(examples, list):
        raise RegistryValidationError("examples must be a list")

    validated: List[Dict[str, Any]] = []
    example_ids: set[str] = set()

    for index, example in enumerate(examples, start=1):
        if not isinstance(example, dict):
            raise RegistryValidationError(f"example at index {index} is not a mapping")

        _require_keys(example, f"example[{index}]", EXAMPLE_REQUIRED)

        example_id = example["id"]
        if not isinstance(example_id, str) or not example_id:
            raise RegistryValidationError(f"example[{index}] has invalid id")
        if example_id in example_ids:
            raise RegistryValidationError(f"duplicate example id: {example_id}")
        example_ids.add(example_id)

        for required_key in ("target_phases", "expected_labels"):
            value = example[required_key]
            if not isinstance(value, list):
                raise RegistryValidationError(
                    f"example[{index}] field '{required_key}' must be a list"
                )

        validated.append(example)

    return validated, example_ids


def load_and_validate_registries(
    claim_path: Path = CLAIM_REGISTRY_PATH,
    example_path: Path = EXAMPLE_REGISTRY_PATH,
) -> Dict[str, Any]:
    claim_payload = _load_yaml(claim_path)
    example_payload = _load_yaml(example_path)

    _require_keys(claim_payload, "claim registry", {"schema_version", "claims"})
    _require_keys(example_payload, "example registry", {"schema_version", "examples"})

    examples, example_ids = _validate_examples(example_payload["examples"])
    claims, cross_ref_count = _validate_claims(claim_payload["claims"], example_ids)

    if len(claims) < MIN_CLAIMS:
        raise RegistryValidationError(
            f"insufficient claims: {len(claims)} (minimum {MIN_CLAIMS})"
        )
    if len(examples) < MIN_EXAMPLES:
        raise RegistryValidationError(
            f"insufficient examples: {len(examples)} (minimum {MIN_EXAMPLES})"
        )

    return {
        "claim_registry_path": str(claim_path),
        "example_catalog_path": str(example_path),
        "claims": claims,
        "examples": examples,
        "cross_reference_count": cross_ref_count,
    }
