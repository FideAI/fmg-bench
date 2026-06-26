# Taxonomy And Methodology Reuse Notes

FMG-Bench is the public companion repository for the paper _When AI Is Your
Pastor: A Benchmark for Theological Triage and Pastoral Guidance in Large
Language Models_. This note explains which public benchmark terms and methods
are stable enough for other researchers to cite, reproduce, compare against, or
adapt in follow-on work.

Reuse should preserve the boundary between FMG-Bench as a public research
benchmark and any separate product, deployment, procurement, or certification
claim.

## Reusable Public Assets

The following assets are stable public inputs for research, replication,
secondary analysis, and compatible benchmark tooling:

| Asset | Reuse Contract |
|---|---|
| Triage levels | `primary`, `secondary`, `tertiary`, and `pastoral_application` may be reused as severity layers for faith and care evaluation. |
| Scenario families | The public family names in `benchmark/schema.md` may seed comparable task taxonomies. |
| Doctrine loci | The manifest coverage keys may seed doctrine-category registries when treated as descriptive labels, not as a complete ontology. |
| Scoring dimensions | The five public score dimensions may be reused for rubric design and aggregate reporting. |
| Failure tags | Public failure tags may be reused for error analysis, triage-adjusted scoring, and reviewer calibration. |
| Run conditions | The four public condition names are stable labels for benchmark reproducibility and publication tables. |
| Reproduction methodology | Dataset loading, perturbation expansion, judging, calibration, and score aggregation may be reused as methodological patterns for comparable research. |

Any downstream reuse should cite FMG-Bench and preserve the public terminology
exactly when comparing against published FMG-Bench results.

## Boundaries

FMG-Bench does not provide hosted certification, endorsement, procurement
approval, deployment review, pastoral approval, or product-readiness decisions.

Researchers and builders may adapt FMG-Bench concepts for separate studies, but
those studies should clearly distinguish their own scenarios, thresholds,
reviewer process, evidence custody, and governance from the published
FMG-Bench v1 benchmark. A separate evaluation must not be presented as an
FMG-Bench score unless it was produced by the public benchmark runner against
the public benchmark contract.

## Compatibility Rules

- Preserve the public condition labels:
  `raw_model`, `guided_default`, `preference_configured`, and
  `perspective_compare`.
- Preserve the public triage labels:
  `primary`, `secondary`, `tertiary`, and `pastoral_application`.
- Treat perturbation variants as rendered benchmark instances; do not count
  them as additional base scenarios.
- Keep FMG-Bench result summaries separate from deployment-readiness or product
  findings produced outside this public benchmark.
- Do not use FMG-Bench as a certification service or endorsement mechanism.

## Change Management

FMG-Bench v1 terminology is contract-stable for public reproduction. Future
benchmark versions may add new taxonomies or fields, but they should document
versioned changes and keep v1 labels available for interpreting existing
results.
