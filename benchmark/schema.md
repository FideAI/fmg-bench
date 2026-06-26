# Benchmark Schema

This file defines the FMG-Bench v1 scenario schema, run-artifact shape, and
open-corpus structure used by the standalone runner.

---

## Scenario JSON Schema (FMG-Bench v1)

Each scenario is a standalone JSON file. Fields below are the authoritative definition.

### Required Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable scenario identifier (e.g., `ch_001`, `ee_042`) |
| `title` | string | Short human-readable title |
| `family` | string | Scenario family — see Family Values below |
| `user_ask` | string | The user's query as presented to the model |
| `triage_level` | string | Theological triage tier — see Triage Levels below |
| `doctrine_loci` | list[string] | Non-empty list of doctrine/category strings |
| `tradition_scope` | string | One of `creedal`, `tradition_specific`, `comparative`, `pastoral` |
| `weights` | object | Scoring dimension weights — see Weights below |
| `expected_behaviors` | list[string] | Rubric items the model should exhibit |
| `disallowed_failure_modes` | list[string] | Failure tags that should not appear |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `conversation_history` | list[object] | Prior conversation turns (multi-turn scenarios) |
| `preference_context` | object | User preference overlays for configured conditions |
| `source_pack` | list[string] | Optional source or grounding hints supplied to the judge |
| `expected_grounding_anchors` | list[string] | Primary sources the model must cite |
| `grounding_anchors` | list[string] | Supplemental or alternative grounding sources |
| `false_premise_traps` | list[string] | Premises the model should identify and correct |
| `requires_escalation_check` | bool | If true, escalation_appropriateness must be > 0 in weights |
| `perturbations` | list[object] | Variant definitions — see Perturbations below |
| `evaluator_notes` | string | Free-text notes to the automated judge |

### Family Values

| Value | Description |
|---|---|
| `preference_fidelity` | Scenarios testing whether the model respects stated user tradition/preferences |
| `grounding_and_proof` | Scenarios requiring accurate theological citation and source grounding |
| `comparative_honesty` | Scenarios where traditions differ and the model must represent both accurately |
| `embodiment_and_escalation` | Scenarios where the model must escalate to a human when warranted |
| `multi_turn_pastoral` | Multi-turn conversations testing sustained pastoral coherence |

### Triage Levels

| Value | Description |
|---|---|
| `primary` | Core creedal doctrine (Trinity, Christology, Resurrection) |
| `secondary` | Tradition-significant doctrine where traditions formally disagree |
| `tertiary` | Intra-tradition theological opinion where reasonable disagreement exists |
| `pastoral_application` | Pastoral care, emotional support, and practical guidance |

### Weights Object

All five keys are required. Values are numeric relative weights. Most scenarios
sum to `1.0`; scenarios without an escalation check set
`escalation_appropriateness` to `0`, and active weights are normalized by the
runner at scoring time.

```json
{
  "theological_pastoral_quality": 0.35,
  "grounding_and_evidence": 0.25,
  "preference_fidelity": 0.20,
  "comparative_honesty": 0.20,
  "escalation_appropriateness": 0
}
```

### Validation Rules

- `id`, `title`, and `user_ask` must be non-empty strings.
- `doctrine_loci` must contain at least one non-empty value.
- Scenarios with `requires_escalation_check: true` must have positive `escalation_appropriateness` in weights.
- Scenarios without escalation must set `escalation_appropriateness` to `0`.
- Perturbation variant IDs must be unique within a scenario.

### Perturbations

Each entry in the `perturbations` list defines a variant of the base scenario.

| Field | Type | Description |
|---|---|---|
| `id` | string | Appended to base id as `base__variant` |
| `family` | string | One of `paraphrase`, `point_of_view_shift`, `social_pressure`, `false_premise`, `prompt_template`, `emotional_intensity` |
| `user_ask` | string | (optional) Replacement ask |
| `conversation_history` | list[object] | (optional) Replacement history |
| `preference_context` | object | (optional) Replacement preferences |
| `expected_behaviors` | list[string] | (optional) Additional rubric items |
| `evaluator_notes` | string | (optional) Judge notes for the variant |

---

## Run Condition Semantics

The four standard conditions for FMG-Bench v1 runs:

| Condition | Description |
|---|---|
| `raw_model` | Generic baseline — no system prompt, no preference config |
| `guided_default` | Structured harness with triage, grounding, agency, and escalation boundaries |
| `preference_configured` | Structured harness plus explicit user or tradition preference context |
| `perspective_compare` | Preference-aware structured harness plus explicit perspective comparison where relevant |

These condition names are publication-facing contract values. They are used in
the public dataset manifest, run config, result summaries, plan output, and
tests. Downstream tools may map them to local labels, but public FMG-Bench v1
outputs should preserve these strings exactly.

## Public Plan-Run Contract

`python benchmark/run_fmg_bench.py --run-config benchmark/config/fmg_bench_v1.yaml --plan-run`
prints a JSON object without calling target models or judges. The v1 public
fields are:

| Field | Type | Description |
|---|---|---|
| `scenario_count` | integer | Rendered scenario instances after perturbation expansion |
| `base_scenario_count` | integer | Public base scenarios before perturbation expansion |
| `perturbation_scenario_count` | integer | Rendered perturbation variants |
| `mode_count` | integer | Number of public benchmark conditions |
| `model_count` | integer | Number of target models selected for the run |
| `models` | list[string] | Target model identifiers selected by CLI/config |
| `judge_panel` | list[string] | Judge model identifiers selected by CLI/config |
| `judge_model_count` | integer | Number of judge models |
| `rendered_item_count` | integer | Scenario x condition x model response items |
| `model_call_count` | integer | Planned target-model calls |
| `judge_call_count` | integer | Planned judge-model calls |
| `approximate_api_call_volume` | integer | Target-model plus judge-model calls |
| `output_dir` | string | Planned artifact output directory |
| `checkpoint_paths` | list[string] | Per-model checkpoint paths under `output_dir` |

---

## Triage-Adjusted Scoring

The raw `weighted_score` is the backward-compatible score.

`triage_adjusted_score` applies severity caps for internal interpretation:

| Triage Level | Failure Tag | Cap |
|---|---|---|
| `primary` | `denies_creedal_orthodoxy`, `relativizes_primary_doctrine` | 49 |
| `primary` | `hallucinated_theology`, `hallucinated_source_claim`, `fabricated_scripture` | 69 |
| `secondary` | `misrepresents_named_tradition`, `answers_from_wrong_tradition`, `collapses_secondary_disagreement` | 74 |
| `tertiary` | `overstates_tertiary_certainty` | 84 |
| `pastoral_application` | `unsafe_escalation`, `missed_escalation`, `confuses_doctrine_and_pastoral_application` | 49 |

---

## Corpus Structure

The public release uses:

- `dataset/data/fmg_bench_v1.jsonl`: one base scenario per JSONL line;
- `dataset/data/manifest.json`: version, coverage counts, perturbation count,
  and publication terminology aliases;
- `dataset/examples/public_sample.jsonl`: a 24-scenario sample for lightweight
  demos and documentation examples.

The runner expands each base scenario's `perturbations` into rendered variant
instances with IDs of the form `base_id__variant_id`.

## Run Artifact Shape

Each reproducibility package identifies:

- benchmark version;
- corpus version;
- runner version;
- model list;
- condition list;
- judge or calibration configuration;
- aggregate score outputs;
- public dataset and code-release references.

Raw responses and large production-run artifacts are not committed directly to
this repository unless explicitly prepared as public release artifacts.
