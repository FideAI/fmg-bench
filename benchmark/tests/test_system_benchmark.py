import json
import csv
import subprocess
import sys
from pathlib import Path

import yaml

RUNNER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUNNER_ROOT.parent
sys.path.insert(0, str(RUNNER_ROOT))

from system_benchmark.loader import load_scenario_set, load_scenarios
from system_benchmark.models import BenchmarkMode, EvaluationConfig, TriageLevel
from system_benchmark.publication import PUBLICATION_MODE_ALIASES
from system_benchmark.renderers import render_prompt
from system_benchmark.runner import SystemBenchmarkRunner


PUBLIC_CONDITION_NAMES = [
    "raw_model",
    "guided_default",
    "preference_configured",
    "perspective_compare",
]

PUBLIC_PLAN_FIELDS = [
    "scenario_count",
    "base_scenario_count",
    "perturbation_scenario_count",
    "mode_count",
    "model_count",
    "models",
    "judge_panel",
    "judge_model_count",
    "rendered_item_count",
    "model_call_count",
    "judge_call_count",
    "approximate_api_call_volume",
    "output_dir",
    "checkpoint_paths",
]


def public_data_dir() -> Path:
    return REPO_ROOT / "dataset" / "data"


def test_open_benchmark_jsonl_loads_and_expands_perturbations():
    scenarios = load_scenarios(public_data_dir())
    base_ids = {scenario.id for scenario in scenarios if scenario.base_scenario_id is None}
    variant_ids = {scenario.id for scenario in scenarios if scenario.base_scenario_id is not None}

    assert len(base_ids) == 120
    assert len(scenarios) > len(base_ids)
    assert "ch_001_women_ordained" in base_ids
    assert any(item.startswith("ch_001_women_ordained__") for item in variant_ids)


def test_manifest_matches_open_benchmark_count():
    manifest = json.loads((public_data_dir() / "manifest.json").read_text())
    line_count = sum(
        1
        for line in (public_data_dir() / "fmg_bench_v1.jsonl").read_text().splitlines()
        if line
    )

    assert manifest["total_scenarios"] == line_count == 120
    assert manifest["open_benchmark_count"] == 120
    assert manifest["example_sample_count"] == 24
    assert manifest["rendered_instance_count"] == 157
    assert manifest["publication_terminology_aliases"] == {
        name: name for name in PUBLIC_CONDITION_NAMES
    }


def test_scenario_set_manifest_validates_open_corpus():
    scenarios, manifest = load_scenario_set(public_data_dir())

    assert manifest.open_benchmark_count == 120
    assert manifest.perturbation_variant_count == 37
    assert manifest.rendered_instance_count == len(scenarios) == 157


def test_benchmark_modes_use_public_condition_names():
    assert [mode.value for mode in BenchmarkMode] == PUBLIC_CONDITION_NAMES


def test_public_condition_names_match_publication_and_config_contracts():
    manifest = json.loads((public_data_dir() / "manifest.json").read_text())
    run_config = yaml.safe_load((RUNNER_ROOT / "config" / "fmg_bench_v1.yaml").read_text())

    assert list(PUBLICATION_MODE_ALIASES.values()) == PUBLIC_CONDITION_NAMES
    assert manifest["publication_terminology_aliases"] == {
        name: name for name in PUBLIC_CONDITION_NAMES
    }
    assert run_config["publication_terminology_aliases"] == {
        name: name for name in PUBLIC_CONDITION_NAMES
    }


def test_render_prompt_uses_guided_instructions_without_product_name():
    scenario = next(
        scenario
        for scenario in load_scenarios(public_data_dir())
        if scenario.triage_level is TriageLevel.PASTORAL_APPLICATION
        and scenario.requires_escalation_check
    )

    prompt = render_prompt(scenario, BenchmarkMode.GUIDED_DEFAULT)

    assert "guided-default benchmark instructions" in prompt
    assert "pastoral, clinical, legal, or emergency escalation" in prompt
    assert "Petr" + "os" not in prompt


def test_plan_run_uses_public_split_without_api_calls():
    runner = SystemBenchmarkRunner(
        EvaluationConfig(
            model_id="dry-run",
            scenarios_dir=str(public_data_dir()),
            judge_models=["judge-a", "judge-b", "judge-c"],
        )
    )

    plan = runner.plan_run(["model-a", "model-b"])

    assert list(plan.keys()) == PUBLIC_PLAN_FIELDS
    assert plan["base_scenario_count"] == 120
    assert plan["scenario_count"] == 157
    assert plan["perturbation_scenario_count"] == 37
    assert plan["mode_count"] == 4
    assert plan["model_count"] == 2
    assert plan["models"] == ["model-a", "model-b"]
    assert plan["judge_panel"] == ["judge-a", "judge-b", "judge-c"]
    assert plan["judge_model_count"] == 3
    assert plan["rendered_item_count"] == 157 * 4 * 2
    assert plan["model_call_count"] == plan["rendered_item_count"]
    assert plan["judge_call_count"] == plan["rendered_item_count"] * 3
    assert plan["approximate_api_call_volume"] == (
        plan["model_call_count"] + plan["judge_call_count"]
    )
    assert len(plan["checkpoint_paths"]) == 2


def test_cli_plan_run_from_repo_root():
    result = subprocess.run(
        [
            sys.executable,
            "benchmark/run_fmg_bench.py",
            "--run-config",
            "benchmark/config/fmg_bench_v1.yaml",
            "--plan-run",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert list(payload.keys()) == PUBLIC_PLAN_FIELDS
    assert payload["base_scenario_count"] == 120
    assert payload["scenario_count"] == 157
    assert payload["perturbation_scenario_count"] == 37
    assert payload["mode_count"] == len(PUBLIC_CONDITION_NAMES)
    assert payload["model_count"] == 14
    assert len(payload["models"]) == 14
    assert payload["judge_panel"] == [
        "openai/gpt-5.4-mini",
        "google/gemini-3.1-flash-lite-preview",
        "anthropic/claude-sonnet-4.6",
    ]
    assert payload["model_call_count"] > 0
    assert payload["rendered_item_count"] == 157 * len(PUBLIC_CONDITION_NAMES) * 14


def test_public_result_summaries_match_headline_claims():
    summary = json.loads((REPO_ROOT / "results" / "production_summary.json").read_text())
    model_rows = list(csv.DictReader((REPO_ROOT / "results" / "model_scores.csv").open()))
    triage_rows = {
        row["triage_level"]: row
        for row in csv.DictReader((REPO_ROOT / "results" / "triage_scores.csv").open())
    }

    assert summary["target_models"] == 14
    assert summary["scored_model_condition_items"] == 8792
    assert summary["headline_results"]["guided_default_minus_raw_model"] == 3.96
    assert len([row for row in model_rows if row["model"] != "Mean"]) == 14
    assert model_rows[-1]["model"] == "Mean"
    assert float(model_rows[-1]["guided_minus_raw"]) == 3.96
    assert float(triage_rows["pastoral_application"]["guided_minus_raw"]) == 6.62


def test_summarize_run_outputs_generates_model_table(tmp_path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    payload = [
        {
            "scenario_id": "s1",
            "mode": mode,
            "triage_level": "primary",
            "weighted_score": score,
            "triage_adjusted_score": score,
            "scores": {
                "theological_pastoral_quality": score,
                "grounding_and_evidence": score,
                "preference_fidelity": score,
                "comparative_honesty": score,
                "escalation_appropriateness": 0,
            },
            "metadata": {"request": {"model": "test/model"}},
        }
        for mode, score in [
            ("raw_model", 80),
            ("guided_default", 90),
            ("preference_configured", 91),
            ("perspective_compare", 89),
        ]
    ]
    (input_dir / "test_latest_evaluations.json").write_text(json.dumps(payload))

    subprocess.run(
        [
            sys.executable,
            "tools/summarize_run_outputs.py",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    rows = list(csv.DictReader((output_dir / "model_scores.csv").open()))
    assert rows[0]["model"] == "test/model"
    assert rows[0]["guided_minus_raw"] == "10.00"
    assert rows[-1]["model"] == "Mean"
