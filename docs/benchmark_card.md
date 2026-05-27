# FMG-Bench v1 Benchmark Card

## Name

Faith & Moral Guidance Benchmark (FMG-Bench) v1

## Purpose

FMG-Bench evaluates whether model and system responses preserve theological triage, represent tradition-specific disagreement accurately, avoid fabricated grounding, and respect pastoral referral boundaries.

## Conditions

| Internal Mode | Publication Mode | Definition |
|---|---|---|
| `raw_model` | `raw_model` | Generic model behavior without benchmark-provided guidance layers. |
| `guided_default` | `guided_default` | Structured harness emphasizing triage, grounding, user agency, and escalation. |
| `preference_configured` | `preference_configured` | Structured-harness behavior with explicit user or tradition preferences supplied as context. |
| `perspective_compare` | `perspective_compare` | Preference-aware structured-harness behavior that also surfaces meaningful faithful disagreement. |

## Scoring Dimensions

- Theological and pastoral quality
- Grounding and evidence
- Preference fidelity
- Comparative honesty
- Escalation appropriateness

## Current Release Status

This package publishes benchmark design, dataset construction, scoring protocol,
calibration protocol, run infrastructure, production-run empirical analysis, and
the open v1 scenario corpus.
The canonical production run completed on April 25, 2026 with 14 target models.
All final repaired artifacts are complete at 628/628 rendered items per model.
Human calibration remains necessary before strong claims about judge validity or
pastoral adequacy.

## Independence and Maintenance

FMG-Bench is maintained by Fide AI. It is intended as an independent research benchmark. Results should not be interpreted as endorsement of a product or model.

## Reproducibility

Run planning and calibration export are supported without model calls:

```bash
python benchmark/run_fmg_bench.py --run-config benchmark/config/fmg_bench_v1.yaml --plan-run
python benchmark/run_fmg_bench.py --run-config benchmark/config/fmg_bench_v1.yaml --calibration-export calibration/calibration_packet.csv
```
