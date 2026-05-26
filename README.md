# FMG-Bench

FMG-Bench is a benchmark for evaluating large language model behavior in
theological triage and pastoral guidance contexts. It tests whether systems can
preserve theological boundaries, represent Christian traditions fairly, avoid
fabricated grounding, maintain user agency, and recognize when human pastoral,
clinical, legal, or emergency support is needed.

This repository contains the public release artifacts for the paper:

> When AI Is Your Pastor: A Benchmark for Theological Triage and Pastoral
> Guidance in Large Language Models

## Release Surfaces

- Paper artifacts: `paper/`
- Public dataset split: `dataset/`
- Benchmark runner and scoring code: `benchmark/`
- Methodology and release documentation: `docs/`
- Aggregate results and public calibration summaries: `results/`, `calibration/`
- Hugging Face dataset: https://huggingface.co/datasets/FideAI/fmg-bench

## What Is Included

- 24 public FMG-Bench v1 scenarios in JSONL format.
- Public manifest metadata describing the 120-scenario benchmark and split counts.
- LaTeX source and PDFs for the full and short paper versions.
- Benchmark runner code, model configuration, scoring utilities, and tests.
- Benchmark card, dataset card, scoring specification, and held-out policy.
- Public aggregate calibration summaries.

## What Is Not Included

- Held-out scenarios used for benchmark integrity.
- Raw model responses or raw judge transcripts.
- Private reviewer packets or reviewer-identifying materials.
- API keys, provider credentials, local run logs, or internal planning documents.

## Quick Start

Install runner dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r benchmark/requirements.txt
```

Plan a run without model or judge API calls:

```bash
python benchmark/run_fmg_bench.py \
  --run-config benchmark/config/fmg_bench_v1.yaml \
  --plan-run
```

The public dataset split is available locally at:

```text
dataset/data/public.jsonl
dataset/data/manifest.json
```

## Responsible Use

FMG-Bench is a measurement tool, not a deployment license. A high benchmark
score does not make an AI system spiritually authoritative, pastorally endorsed,
clinically safe, legally reliable, or appropriate for unsupervised use. See
`docs/responsible_use.md`.

## Citation

See `CITATION.cff` and `paper/references.bib`.

## License

- Dataset, paper text, methodology docs, and result summaries: CC BY 4.0.
- Code: Apache License 2.0.

See `LICENSE` for details.
