# FMG-Bench v1 Dataset Card

## Dataset Summary

FMG-Bench v1 is a 120-scenario benchmark corpus for evaluating faith, theological triage, tradition-aware moral reasoning, and pastoral guidance behavior in large language model systems. It is maintained by Fide AI as an independent research benchmark.

The canonical production run completed on April 25, 2026 with 14 target models.
Current empirical tables use the final repaired result snapshot with 628/628
rendered items per model. Human calibration remains necessary before strong
claims about judge validity or pastoral adequacy.

## Composition

- 25 primary doctrine scenarios
- 35 secondary doctrine scenarios
- 25 tertiary doctrine scenarios
- 35 pastoral application scenarios

The corpus includes existing internal benchmark scenarios and new original scenarios authored for FMG-Bench v1. It does not import CTTAF questions or external benchmark items.

## Splits

Split identifiers are declared in `dataset/data/manifest.json` for the public
release. The held-out split is described in aggregate only.

- `public_sample_ids`: scenarios suitable for examples, documentation, and reviewer orientation.
- `held_out_ids`: scenarios intended for model evaluation reporting.
- `calibration_candidate_ids`: scenarios suitable for human calibration packets.

## Intended Use

FMG-Bench is intended for research on theological triage, pastoral guidance boundaries, tradition-aware evaluation, model robustness, and guided system-layer behavior.

## Out-of-Scope Use

FMG-Bench results should not be interpreted as endorsement of a product, model, denomination, or pastoral decision. The benchmark is not a pastoral care replacement and is not a clinical, legal, or emergency response tool.

## Risks

The corpus includes sensitive pastoral application topics such as self-harm, abuse, addiction, sexuality and identity, family conflict, and scrupulosity. Reviewers and researchers should use appropriate safeguards and referral protocols.

## Maintenance

FMG-Bench is maintained by Fide AI. It is intended as an independent research benchmark, not a product-launch artifact.
