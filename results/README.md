# Publication Results

Destination for curated result packages referenced by Fide AI publications.

Large production artifacts should not be committed unless they have been
explicitly reviewed for public release.

This repository starts with paper-level aggregate tables and public calibration
summaries only.

## Files

- `production_summary.json`: headline production-run metadata and key effects.
- `model_scores.csv`: per-model scores by instruction condition.
- `triage_scores.csv`: condition scores by theological triage level.
- `dimension_scores.csv`: condition scores by scoring dimension.
- `../calibration/results/`: public synthetic calibration summaries.

## Headline Production Results

| Metric | Result |
|---|---:|
| Target models | 14 |
| Scored model-condition items | 8,792 |
| Guided default over raw model | +3.96 points |
| Pastoral application gain | +6.62 points |
| Escalation appropriateness gain | +10.8 points |
| Robustness stability | 92.88 -> 98.02 |

Interpretation: bounded guided instructions improved all 14 tested models over
raw model behavior. Perspective comparison helped some secondary-doctrine cases
but was not a universal improvement.
