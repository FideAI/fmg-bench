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

The default public release config reads from `dataset/data/`, so a fresh clone
can plan a run without access to the held-out corpus.

## Run Tests

From the repository root:

```bash
python -m pytest benchmark/tests
```

## Run A Small Live Evaluation

Live runs require an OpenRouter key:

```bash
export OPENROUTER_API_KEY="..."

python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --model openai/gpt-5.4 \
  --max-scenarios 2
```

Outputs are written under `results/system_benchmark/fmg_bench_v1/` by default.
Raw run outputs are ignored by git.

## Provider Credentials

Live model runs require provider credentials in environment variables. Do not
commit credentials or `.env` files.
