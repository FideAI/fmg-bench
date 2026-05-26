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

## Provider Credentials

Live model runs require provider credentials in environment variables. Do not
commit credentials or `.env` files.
