# To Flatten a Stone with Six Birds: Critical Pairs, Holonomy, and Confluence in Rewriting Systems

This repository contains the **confluence instantiation** for the paper:

> **To Flatten a Stone with Six Birds: Critical Pairs, Holonomy, and Confluence in Rewriting Systems**
>
> DOI: [10.5281/zenodo.19061345](https://doi.org/10.5281/zenodo.19061345)
>
> Repository: https://github.com/ioannist/six-birds-confluence

This paper isolates a confluence-as-flatness bridge for rewriting systems after correcting the geometric object from a bare reduction graph to a reduction 2-complex. The repository includes theorem-level Lean anchors, exhaustive and curated computational evidence, machine-readable artifact ledgers, and a publication-ready manuscript.

## What this repository provides

- **Formal core in Lean** (`ConfluenceFlat/`): elementary flatness iff local confluence, plus uniqueness-of-normal-form support under confluence and normalization.
- **Finite-ARS exhaustive audits** (`results/audits/`): all labeled systems up to four states in the terminating regime, with discrepancy counters and row-level outputs.
- **Curated structured-rewriting bridges** (`results/string_rewrite/`, `results/term_rewrite/`, `results/critical_pairs/`): reachable critical-pair and graph-peak comparisons for string/TRS examples.
- **Reduction 2-complex artifacts** (`results/two_complex/`): generating 2-cells, filler/witness records, and elementary-holonomy status.
- **Completion case studies** (`results/case_studies/`): explicit before/after defect-elimination pairs.
- **Artifact ledger and freeze boundary** (`results/index.json`, `results/summary.csv`, `results/freeze/`), including claim-support outputs.
- **Paper source and generated assets** (`paper/`), including flattened manuscript output at `paper/build/main_flat.tex`.

## Scope and limitations

- The theorem-level core is formalized at abstract rewriting-system level; the full finite terminating left-linear TRS theorem package is intentionally deferred in the manuscript.
- The structured rewriting bridge is evidenced by curated bounded examples and exhaustive finite-ARS audits in the stated regime; it is not presented as an unrestricted global theorem.
- Graph-only flatness surrogates are treated as falsified diagnostics in this setting; the positive bridge claims are tied to local branching cells (local peaks/reachable critical pairs).

## Install

```bash
python -m pip install -e .
```

Build Lean artifacts (optional but recommended for the formal layer):

```bash
lake build
```

## Test

```bash
make test
```

## Run audits and regression

```bash
make audit
make regression
```

## Build paper

```bash
make paper
```

Outputs:

- `paper/build/main.pdf`
- `paper/build/main_flat.tex`

## Repository notes

- Active bibliography: `paper/references.bib`
- Zenodo related-works CSV: `assets/zenodo_related_works.csv`
- Section/artifact planning notes: `paper/notes/*.yaml`
