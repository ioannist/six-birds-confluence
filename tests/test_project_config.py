from pathlib import Path

from rewriteflat.project_config import (
    MIN_CLAIMS,
    MIN_EXAMPLES,
    load_and_validate_registries,
)


def test_yaml_registries_load_and_validate():
    summary = load_and_validate_registries()
    assert len(summary["claims"]) >= MIN_CLAIMS
    assert len(summary["examples"]) >= MIN_EXAMPLES


def test_registry_ids_are_unique():
    summary = load_and_validate_registries()

    claim_ids = [claim["id"] for claim in summary["claims"]]
    example_ids = [example["id"] for example in summary["examples"]]

    assert len(claim_ids) == len(set(claim_ids))
    assert len(example_ids) == len(set(example_ids))


def test_claims_reference_known_examples():
    summary = load_and_validate_registries()
    example_ids = {example["id"] for example in summary["examples"]}

    for claim in summary["claims"]:
        for example_id in claim["related_example_ids"]:
            assert example_id in example_ids
