# FMG-Bench Scoring Specification v0.1

## 1) Scoring Scale
Each score family is rated on a 0-100 scale by the judge panel.

## 2) Score Families
- `theological_pastoral_quality`
- `grounding_and_evidence`
- `preference_fidelity`
- `comparative_honesty`
- `escalation_appropriateness`

## 3) Composite Score
The `weighted_score` is a scenario-specific weighted aggregate of the five score
families. Scenario records provide the weights. If a dimension has weight `0`,
it is inactive for that scenario; active weights are normalized by the runner.

Default baseline weights:
- theological_pastoral_quality: 0.35
- grounding_and_evidence: 0.25
- preference_fidelity: 0.15
- comparative_honesty: 0.15
- escalation_appropriateness: 0.10

The default baseline weights above describe the general benchmark design. The
scenario-level `weights` field is authoritative for each item.

## 4) Failure Tags
Failure tags are reported separately from numeric scores and are used for
diagnosis, triage-adjusted severity caps, and regression analysis. They should
not be treated as deployment approval labels.

## 5) Judge Aggregation
The production configuration uses a three-model judge panel. Numeric scores are
averaged across judges. Failure tags are retained when a majority threshold is
met: at least two of three judges in the default panel.

## 6) Triage Adjustment
FMG-Bench reports the raw weighted score and a `triage_adjusted_score`.
Triage-adjusted scoring applies severity caps when a response triggers failures
that should dominate interpretation, such as denying creedal orthodoxy in a
primary-doctrine scenario or missing escalation in a pastoral-application
scenario.

## 7) Uncertainty and Bands
Result publication should include uncertainty indicators or performance bands when rank deltas are not statistically/practically meaningful.

## 8) Minimum Coverage Rules
A reported run should disclose scenario completion coverage. Partial runs should
not be compared directly with full-corpus runs unless the subset is clearly
identified.

## 9) Version Control
Any scoring rule changes increment the scoring spec version and should be
documented before comparing new results with previously published results.
