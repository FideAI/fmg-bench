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
      - split: public
        path: data/public.jsonl
---

# FMG-Bench v1 Dataset

FMG-Bench is a 120-scenario benchmark for evaluating large language model
behavior in theological triage and pastoral guidance contexts. This dataset
release contains the 24-scenario public split.

## Files

- `data/public.jsonl`: public scenario split.
- `data/manifest.json`: release metadata and aggregate coverage counts.
- `scripts/push_to_hf.py`: helper for uploading the dataset to Hugging Face.

## Splits

- Public split: 24 scenarios.
- Held-out split: not released publicly.

Held-out scenarios are intentionally excluded to preserve benchmark integrity.

## License

CC BY 4.0.
