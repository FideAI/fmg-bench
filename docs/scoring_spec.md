# Fide Scoring Specification v0.1 (Draft)

## 1) Scoring Scale
Each score family is rated on a 0–100 scale using calibrated rubric anchors.

## 2) Score Families
- `theological_pastoral_quality`
- `grounding_and_evidence`
- `preference_fidelity`
- `comparative_honesty`
- `escalation_appropriateness`

## 3) Composite Score
Composite score is a weighted aggregate of applicable families.

Default baseline weights:
- theological_pastoral_quality: 0.35
- grounding_and_evidence: 0.25
- preference_fidelity: 0.15
- comparative_honesty: 0.15
- escalation_appropriateness: 0.10

If escalation is non-applicable, its weight is redistributed proportionally to other active families.

## 4) Failure Tags
Failure tags are reported separately from numeric scores and are used for:
- release-gating rules
- certification conditions
- regression triage

## 5) Judge Aggregation
Final family scores are aggregated across judge panel outputs using robust central tendency (median default) with outlier review thresholds.

## 6) Uncertainty and Bands
Leaderboard publication should include uncertainty indicators or performance bands when rank deltas are not statistically/practically meaningful.

## 7) Minimum Coverage Rules
A submission must satisfy required scenario completion thresholds before receiving an official composite score.

## 8) Version Control
Any scoring rule changes increment scoring spec version and must be documented prior to active submission windows.
