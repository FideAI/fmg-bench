---
license: cc-by-4.0
language:
  - en
tags:
  - benchmark
  - theology
  - religion
  - faith
  - pastoral
  - evaluation
  - llm-evaluation
  - safety
pretty_name: FMG-Bench v1
size_categories:
  - n<1K
task_categories:
  - text-generation
  - question-answering
configs:
  - config_name: default
    data_files:
      - split: benchmark
        path: data/fmg_bench_v1.jsonl
      - split: example_sample
        path: examples/public_sample.jsonl
---

# FMG-Bench v1 Dataset

FMG-Bench is a 120-scenario benchmark for evaluating large language model
behavior in theological triage and pastoral-guidance-adjacent contexts.

This release contains the open v1 benchmark corpus: 120 base scenarios with 37
perturbation variants. It is intended for researchers and engineers studying how
models handle faith-facing questions involving doctrine, tradition, moral
guidance, user preference, grounding, and escalation boundaries.

Project links:

- GitHub: https://github.com/FideAI/fmg-bench
- Fide AI research page: https://fideai.org/research/fmg-bench

## Files

- `data/fmg_bench_v1.jsonl`: open benchmark scenario corpus.
- `data/manifest.json`: release metadata and aggregate coverage counts.
- `examples/public_sample.jsonl`: 24-scenario sample for quick inspection and
  documentation examples.

## Splits

- Benchmark split: 120 base scenarios.
- Example sample: 24 scenarios, drawn from the benchmark split for lightweight
  demos and documentation.

FMG-Bench is released as an open dataset benchmark. Fide AI may maintain
additional internal audit items for future contamination checks, but there is no
hosted hidden-test leaderboard for this release.

## Load Locally

```python
import json
from pathlib import Path

records = [
    json.loads(line)
    for line in Path("data/fmg_bench_v1.jsonl").read_text().splitlines()
    if line.strip()
]
print(records[0]["id"], records[0]["triage_level"])
```

Each scenario includes:

- `user_ask`
- `triage_level`
- `tradition_scope`
- `doctrine_loci`
- scoring `weights`
- `expected_behaviors`
- `disallowed_failure_modes`
- optional perturbation variants

## Responsible Use

FMG-Bench is an evaluation dataset. It does not certify pastoral authority,
clinical safety, legal adequacy, or deployment readiness. Results should be
interpreted as behavioral evidence under the benchmark's scoring framework, not
as endorsement of a model for real-world pastoral, counseling, legal, or
crisis-support use.

## License

CC BY 4.0.
