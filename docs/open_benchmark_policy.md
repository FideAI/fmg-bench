# Open Benchmark Policy

## Purpose

FMG-Bench v1 is released as an open dataset benchmark. The benchmark scenarios,
rubric, scoring dimensions, runner, and aggregate result summaries are public so
researchers can inspect, rerun, critique, and extend the evaluation.

## Policy

- The v1 benchmark corpus is released in `dataset/data/fmg_bench_v1.jsonl`.
- The 24-scenario example sample in `dataset/examples/public_sample.jsonl` is
  for quick inspection and documentation, not a separate official test set.
- Fide AI does not operate a hosted hidden-test leaderboard for this release.
- Published comparisons should disclose model versions, prompts or system
  conditions, judge configuration, scenario coverage, and scoring-spec version.
- Fide AI may maintain additional internal audit items for future contamination
  checks, regression analysis, or follow-up studies. Those items are not the
  official public scoring path for FMG-Bench v1.

## Reporting Expectations

When publishing new FMG-Bench results, report:

- dataset version;
- scoring specification version;
- model identifiers and access path;
- instruction condition or system prompt policy;
- judge model panel, if automated judging is used;
- number of completed base scenarios and perturbation variants;
- any filtering, repair passes, or failed responses.

## Responsible Participation

Participants should not treat a high score as pastoral endorsement, clinical
safety certification, or permission for unsupervised deployment in faith or care
contexts. See `docs/responsible_use.md`.
