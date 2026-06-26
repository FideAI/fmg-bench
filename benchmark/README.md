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

The `--plan-run` command prints a public JSON contract. Field names and the four
condition names are stable for FMG-Bench v1 reproducibility:

| Field | Meaning |
|---|---|
| `scenario_count` | Rendered scenario instances after perturbation expansion. |
| `base_scenario_count` | Public base scenarios before perturbation expansion. |
| `perturbation_scenario_count` | Rendered perturbation variants. |
| `mode_count` | Number of public benchmark conditions. |
| `model_count` | Number of target models in the planned run. |
| `models` | Target model identifiers selected by CLI/config. |
| `judge_panel` | Judge model identifiers selected by CLI/config. |
| `judge_model_count` | Number of judge models. |
| `rendered_item_count` | Scenario x condition x model response items. |
| `model_call_count` | Planned target-model API calls. |
| `judge_call_count` | Planned judge-model API calls. |
| `approximate_api_call_volume` | Target-model plus judge-model call count. |
| `output_dir` | Directory where run artifacts would be written. |
| `checkpoint_paths` | Per-model checkpoint files for the planned output directory. |

Public condition names are `raw_model`, `guided_default`,
`preference_configured`, and `perspective_compare`.

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
