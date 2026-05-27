# Benchmark Runner

This directory contains standalone FMG-Bench runner and scoring code.

## Contents

- `run_fmg_bench.py`: command-line runner.
- `system_benchmark/`: scenario loading, prompt rendering, scoring, reporting,
  and calibration helpers.
- `config/`: versioned benchmark and model configuration.
- `tests/`: regression tests.
- `requirements.txt`: Python dependencies.

## Plan A Run

Planning does not call model or judge APIs:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --plan-run
```

The default release config reads from the open benchmark dataset in
`dataset/data/`, so a fresh clone can plan a full-corpus run.

## Run Tests

From the repository root:

```bash
python -m pytest benchmark/tests
```

## Run A Small Live Evaluation

Live runs require an OpenRouter key. Use a small one-judge run first to verify
credentials, model access, judge parsing, and local output paths:

```bash
export OPENROUTER_API_KEY="..."

python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --model openai/gpt-5.4 \
  --judge openai/gpt-5.4-mini \
  --max-scenarios 1 \
  --output runs/smoke
```

The paper-comparable judge panel is:

```text
openai/gpt-5.4-mini,google/gemini-3.1-flash-lite-preview,anthropic/claude-sonnet-4.6
```

Outputs are written under the directory passed to `--output`. Use `runs/` for
local experiments; it is ignored by git.

## Summarize Finished Runs

After one or more model runs finish, regenerate CSV summaries:

```bash
python tools/summarize_run_outputs.py \
  --input-dir runs/fmg_bench_v1 \
  --output-dir runs/fmg_bench_v1_summary
```

See `docs/reproducing_results.md` for full reproduction notes.

## Provider Credentials

Live model runs require provider credentials in environment variables. Do not
commit credentials or `.env` files.
