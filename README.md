# FMG-Bench

**Faith & Moral Guidance Benchmark for evaluating large language models in
theological triage and pastoral guidance contexts.**

FMG-Bench asks whether a model gives the right kind of answer for the kind of
faith-and-care question being asked: creedal clarity for primary doctrine,
tradition-aware representation for secondary disagreement, humility for lower
certainty questions, and human referral boundaries for pastoral situations.

This repository contains the public release package for:

> **When AI Is Your Pastor: A Benchmark for Theological Triage and Pastoral
> Guidance in Large Language Models**

Links:

- Fide AI research page: https://fideai.org/research/fmg-bench
- Hugging Face dataset: https://huggingface.co/datasets/FideAI/fmg-bench
- GitHub repository: https://github.com/FideAI/fmg-bench
- Full paper PDF: [`paper/main.pdf`](paper/main.pdf)
- Short paper PDF: [`paper/main_short.pdf`](paper/main_short.pdf)

## Headline Results

FMG-Bench v1 evaluates 14 advanced models across four instruction conditions for
8,792 scored model-condition items. The main empirical finding is that placing
models inside a structured harness improves every tested model over raw model
behavior.

| Finding | Result | Interpretation |
|---|---:|---|
| Guided default vs. raw model | **+3.96 points** | Every one of the 14 models improved. |
| Pastoral application gain | **+6.62 points** | Largest triage-level gain; safety and referral boundaries benefit most. |
| Escalation appropriateness gain | **+10.8 points** | The structured harness helps models recognize when human support is needed. |
| Robustness stability | **92.88 -> 98.02** | Structured-harness behavior is more stable under rewording, pressure, and perturbation. |
| Perspective comparison | Mixed | Helps secondary doctrine, but can hurt primary doctrine and urgent pastoral cases. |

The benchmark is a measurement tool, not an endorsement of AI systems as
pastoral authorities.

## What Is In This Repo

| Path | Purpose |
|---|---|
| [`paper/`](paper/) | LaTeX source, PDFs, bibliography, and paper figures. |
| [`dataset/`](dataset/) | Open 120-scenario benchmark dataset and Hugging Face dataset card. |
| [`benchmark/`](benchmark/) | Standalone runner, scoring code, config, and tests. |
| [`docs/`](docs/) | Benchmark card, dataset card, scoring spec, open-benchmark policy, responsible-use notes, and taxonomy reuse notes. |
| [`calibration/`](calibration/) | Public synthetic calibration summaries and aggregate CSVs. |
| [`results/`](results/) | Machine-readable public result summaries. |
| [`tools/`](tools/) | Release-safety checks. |

Included:

- Full open FMG-Bench v1 dataset: 120 base scenarios and 37 perturbation variants.
- Public manifest metadata for the 120-scenario benchmark and coverage counts.
- Benchmark runner code, model configuration, scoring utilities, and smoke tests.
- Paper artifacts for the full arXiv-style version and the short conference-style version.
- Benchmark card, dataset card, scoring specification, open-benchmark policy, and responsible-use documentation.
- Taxonomy and methodology reuse notes for researchers and compatible benchmark tooling.

Not included:

- Raw model responses or raw judge transcripts.
- Private reviewer packets or reviewer-identifying materials.
- API keys, provider credentials, local run logs, or internal planning documents.

## Quick Start For Developers

Create an environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r benchmark/requirements.txt pytest
```

Run the public smoke tests:

```bash
python -m pytest benchmark/tests
```

Plan a benchmark run without model or judge API calls:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --plan-run
```

Expected benchmark plan shape:

```json
{
  "base_scenario_count": 120,
  "scenario_count": 157,
  "mode_count": 4,
  "model_count": 14
}
```

Run the public-release scan:

```bash
python tools/release_scan.py
```

For full reproduction guidance, including API-key setup, call-volume planning,
resuming interrupted runs, and regenerating CSV result tables, see
[`docs/reproducing_results.md`](docs/reproducing_results.md).

## Inspect The Dataset

The local benchmark dataset is:

```text
dataset/data/fmg_bench_v1.jsonl
dataset/data/manifest.json
dataset/examples/public_sample.jsonl
```

Preview scenarios:

```bash
python - <<'PY'
import json
from pathlib import Path

for line in Path("dataset/data/fmg_bench_v1.jsonl").read_text().splitlines()[:3]:
    item = json.loads(line)
    print(f"{item['id']} | {item['triage_level']} | {item['title']}")
PY
```

Load with Python:

```python
from benchmark.system_benchmark.loader import load_scenarios

scenarios = load_scenarios("dataset/data")
print(len(scenarios))  # base scenarios plus perturbation variants
```

## Inspect The Results

Public result summaries are available as CSV/JSON:

```text
results/production_summary.json
results/model_scores.csv
results/triage_scores.csv
results/dimension_scores.csv
```

Quickly view the model table:

```bash
python - <<'PY'
import csv
from pathlib import Path

rows = list(csv.DictReader(Path("results/model_scores.csv").open()))
for row in rows[:5]:
    print(row["model"], row["guided_minus_raw"])
PY
```

## Run Live Evaluations

Live model calls use OpenRouter by default. Do not commit credentials.

```bash
export OPENROUTER_API_KEY="..."

python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --model openai/gpt-5.4 \
  --judge openai/gpt-5.4-mini \
  --max-scenarios 1 \
  --output runs/smoke
```

The smoke command uses one target model, one judge, and one base scenario across
the four instruction conditions. Paper-comparable runs use the default
three-model judge panel and the full 157 rendered scenario instances.

The public config points at the open benchmark dataset. Fide AI may keep
additional internal audit items for future contamination checks, but this
repository does not operate a hidden-test leaderboard or hosted evaluation
service.

## Benchmark Design

FMG-Bench evaluates four triage levels:

| Triage level | What it tests |
|---|---|
| Primary doctrine | Creedal and gospel-boundary faithfulness. |
| Secondary doctrine | Tradition-specific accuracy and fair disagreement. |
| Tertiary doctrine | Proportional confidence and humility. |
| Pastoral application | Care, safety, agency, and referral boundaries. |

Responses are scored across five dimensions:

- Theological and pastoral quality
- Grounding and evidence
- Preference fidelity
- Comparative honesty
- Escalation appropriateness

The four instruction conditions are:

- `raw_model`
- `guided_default`
- `preference_configured`
- `perspective_compare`

See [`docs/scoring_spec.md`](docs/scoring_spec.md) and
[`docs/benchmark_card.md`](docs/benchmark_card.md) for details.

## Responsible Use

FMG-Bench is a measurement tool, not a deployment license. A high benchmark score
does not make an AI system spiritually authoritative, pastorally endorsed,
clinically safe, legally reliable, or appropriate for unsupervised use.

Do not use FMG-Bench scores to rank denominations, certify pastoral authority, or
market a model as safe for unsupervised pastoral care.

See [`docs/responsible_use.md`](docs/responsible_use.md).

## Citation

See [`CITATION.cff`](CITATION.cff) and [`paper/references.bib`](paper/references.bib).

```bibtex
@misc{chao2026fmgbench,
  title        = {When AI Is Your Pastor: A Benchmark for Theological Triage
                  and Pastoral Guidance in Large Language Models},
  author       = {Chao, Alex},
  year         = {2026},
  institution  = {Fide AI},
  url          = {https://github.com/FideAI/fmg-bench}
}
```

## License

- Dataset, paper text, methodology docs, and result summaries: CC BY 4.0.
- Code: Apache License 2.0.

See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
