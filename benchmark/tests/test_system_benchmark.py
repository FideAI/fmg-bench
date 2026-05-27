import json
import csv
import subprocess
import sys
from pathlib import Path

RUNNER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUNNER_ROOT.parent
sys.path.insert(0, str(RUNNER_ROOT))

from system_benchmark.loader import load_scenarios
from system_benchmark.models import BenchmarkMode, EvaluationConfig, TriageLevel
from system_benchmark.renderers import render_prompt
from system_benchmark.runner import SystemBenchmarkRunner


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
        "raw_model": "raw_model",
        "guided_default": "guided_default",
        "preference_configured": "preference_configured",
        "perspective_compare": "perspective_compare",
    }


def test_benchmark_modes_use_public_condition_names():
    assert [mode.value for mode in BenchmarkMode] == [
        "raw_model",
        "guided_default",
        "preference_configured",
        "perspective_compare",
    ]


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

    assert plan["base_scenario_count"] == 120
    assert plan["scenario_count"] == 157
    assert plan["mode_count"] == 4
    assert plan["model_count"] == 2
    assert plan["judge_model_count"] == 3


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
    assert payload["base_scenario_count"] == 120
    assert payload["scenario_count"] == 157
    assert payload["model_call_count"] > 0


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
