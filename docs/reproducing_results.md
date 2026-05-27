# Reproducing FMG-Bench Runs

This guide is for researchers and engineers who want to inspect the benchmark,
run it with their own API keys, and regenerate comparable result tables.

## What Is Reproducible

This repository includes:

- the open FMG-Bench v1 corpus: 120 base scenarios and 37 perturbation variants;
- the four instruction conditions used in the paper;
- the judge prompt, failure taxonomy, score aggregation, and triage-adjustment
  code;
- the model list and judge panel used for the reported production run;
- aggregate CSV/JSON result summaries from the production run.

Exact model outputs may change over time because hosted model providers can
update model weights, routing, safety layers, and availability behind a stable
model identifier. Treat exact numeric replication as provider- and date-bound.
For new studies, report the run date, model IDs, provider path, judge panel, and
scenario coverage.

## API Keys

Live runs use OpenRouter by default. Create an environment variable before
running model or judge calls:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

Do not commit `.env` files or raw run artifacts. The repository includes
`.env.example` only as a template.

## Install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r benchmark/requirements.txt pytest
```

Check that the local package and dataset load correctly:

```bash
python -m pytest benchmark/tests
```

## Plan Before Spending

Planning does not call any APIs:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --plan-run
```

The full v1 plan should show:

- 120 base scenarios;
- 37 perturbation variants;
- 157 rendered scenario instances;
- 4 instruction conditions;
- 14 target models;
- 8,792 target-model calls;
- 26,376 judge calls with the default three-judge panel.

## Low-Cost Connectivity Test

Use a tiny run before attempting the full benchmark. This checks the API key,
model ID, judge parsing, checkpointing, and output files:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --model openai/gpt-5.4 \
  --judge openai/gpt-5.4-mini \
  --max-scenarios 1 \
  --output runs/smoke
```

This runs one base scenario across the four instruction conditions and uses one
judge model. It is useful for debugging but is not comparable to the paper.

## Paper-Comparable Single-Model Run

The paper used a three-model judge panel:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --model openai/gpt-5.4 \
  --judge openai/gpt-5.4-mini,google/gemini-3.1-flash-lite-preview,anthropic/claude-sonnet-4.6 \
  --model-max-tokens 20000 \
  --output runs/fmg_bench_v1
```

Use `--resume` to continue after interruption:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --model openai/gpt-5.4 \
  --resume \
  --output runs/fmg_bench_v1
```

Use `--rejudge` to reuse checkpointed model responses and rerun only the judge
panel:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --model openai/gpt-5.4 \
  --rejudge \
  --output runs/fmg_bench_v1
```

## Full Production-Style Run

To run all enabled models from `benchmark/config/fmg_bench_v1.yaml`:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --all-models \
  --model-concurrency 1 \
  --concurrency 8 \
  --model-max-tokens 20000 \
  --output runs/fmg_bench_v1
```

Increase concurrency only after confirming provider rate limits and budget.

## Output Artifacts

Each model run writes:

- `*_checkpoint.jsonl`: append-only resumable checkpoint;
- `*_responses.json`: rendered prompts and model responses;
- `*_evaluations.json`: normalized judge scores and failure tags;
- `*_deltas.json`: pairwise condition deltas;
- `*_summary.json`: run-level aggregates;
- `*_report.md`: readable per-model report.

Raw outputs can include model responses and judge text. Review them before
sharing publicly.

## Regenerate Summary Tables

After one or more model runs finish, regenerate publication-style tables:

```bash
python tools/summarize_run_outputs.py \
  --input-dir runs/fmg_bench_v1 \
  --output-dir runs/fmg_bench_v1_summary
```

This writes:

- `model_scores.csv`;
- `triage_scores.csv`;
- `dimension_scores.csv`.

The checked-in production summaries under `results/` are the curated release
tables from the paper. Newly generated tables should be compared with those only
when the model IDs, provider routing, judge panel, scoring code, and scenario
coverage match.
