#!/usr/bin/env python3
"""CLI for the FMG-Bench evaluation runner."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from openrouter import call_openrouter_model
from system_benchmark.calibration import export_calibration_packet_csv
from system_benchmark import (
    EvaluationConfig,
    ScenarioFamily,
    SystemBenchmarkRunner,
    run_model_batch,
)
from system_benchmark.publication import load_scenario_set_manifest

logger = logging.getLogger(__name__)
RUNNER_ROOT = Path(__file__).resolve().parent

DEFAULT_JUDGE_MODELS = [
    "openai/gpt-5.4-mini",
    "google/gemini-3.1-flash-lite-preview",
    "anthropic/claude-sonnet-4.6",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the FMG-Bench evaluation")
    parser.add_argument("--model", type=str, help="Model ID to evaluate")
    parser.add_argument(
        "--judge",
        type=str,
        default=",".join(DEFAULT_JUDGE_MODELS),
        help=(
            "Judge model or comma-separated judge panel "
            f"(default: {','.join(DEFAULT_JUDGE_MODELS)})"
        ),
    )
    parser.add_argument(
        "--scenarios-dir",
        type=str,
        default=None,
        help="Directory containing scenario files (overrides --scenario-set)",
    )
    parser.add_argument(
        "--scenario-set",
        type=str,
        default="fmg_bench_v1",
        help="Named scenario set under corpus/ (default: fmg_bench_v1)",
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default=None,
        help="Root directory containing scenario sets (default: ../corpus relative to runner)",
    )
    parser.add_argument(
        "--run-config",
        type=str,
        default=None,
        help="YAML run configuration path",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/fmg_bench_v1",
        help="Output directory for benchmark artifacts",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=None,
        help="Maximum number of scenarios to run",
    )
    parser.add_argument(
        "--scenario-family",
        type=str,
        choices=[item.value for item in ScenarioFamily],
        default=None,
        help="Filter to a single scenario family",
    )
    parser.add_argument("--resume", action="store_true", help="Reuse latest saved responses")
    parser.add_argument(
        "--rejudge",
        action="store_true",
        help="Reuse checkpointed model responses and rerun only the judge panel",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Discard existing checkpoint for selected model(s) before running",
    )
    parser.add_argument(
        "--rebuild-from-checkpoint",
        action="store_true",
        help="Rebuild result artifacts from existing checkpoint(s) without model or judge calls",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate and summarize scenarios only")
    parser.add_argument(
        "--plan-run",
        action="store_true",
        help="Estimate scenarios, rendered items, calls, and outputs without calling models or judges",
    )
    parser.add_argument(
        "--calibration-export",
        type=str,
        default=None,
        help="Write a blank reviewer calibration packet CSV and exit",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Max concurrent benchmark items (default: 8)",
    )
    parser.add_argument(
        "--model-concurrency",
        type=int,
        default=1,
        help="Max models to run in parallel (default: 1)",
    )
    parser.add_argument(
        "--judge-concurrency",
        type=int,
        default=None,
        help="Max concurrent judge calls (defaults to --concurrency)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retries per model/judge call after the first attempt (default: 2)",
    )
    parser.add_argument(
        "--model-timeout",
        type=float,
        default=180.0,
        help="Timeout in seconds for model calls (default: 180)",
    )
    parser.add_argument(
        "--judge-timeout",
        type=float,
        default=180.0,
        help="Timeout in seconds for judge calls (default: 180)",
    )
    parser.add_argument(
        "--model-max-tokens",
        type=int,
        default=4000,
        help="Maximum output tokens for target model calls (default: 4000)",
    )
    parser.add_argument(
        "--judge-max-tokens",
        type=int,
        default=1800,
        help="Maximum output tokens for judge model calls (default: 1800)",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=1.0,
        help="Base backoff in seconds between retries (default: 1.0)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on the first failed item",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    parser.add_argument(
        "--all-models",
        action="store_true",
        help="Run all enabled models from --run-config",
    )
    return parser.parse_args()


def _corpus_root(args: argparse.Namespace) -> Path:
    if args.corpus_dir:
        return Path(args.corpus_dir)
    return RUNNER_ROOT.parent / "corpus"


def _resolve_scenarios_dir(args: argparse.Namespace, run_config: dict) -> Path:
    if args.scenarios_dir:
        p = Path(args.scenarios_dir)
        return p if p.is_absolute() else RUNNER_ROOT / p
    if run_config.get("scenarios_dir"):
        p = Path(str(run_config["scenarios_dir"]))
        return p if p.is_absolute() else RUNNER_ROOT / p
    scenario_set = args.scenario_set or run_config.get("scenario_set", "fmg_bench_v1")
    return _corpus_root(args) / scenario_set


def _load_run_config(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        p = RUNNER_ROOT / p
    with p.open() as f:
        return yaml.safe_load(f) or {}


def _models_from_run_config(payload: dict) -> list[str]:
    models = payload.get("models") or []
    parsed: list[str] = []
    for item in models:
        if isinstance(item, str):
            parsed.append(item)
        elif isinstance(item, dict) and item.get("model_name"):
            if item.get("enabled", True):
                parsed.append(str(item["model_name"]))
    return parsed


def _build_config(args: argparse.Namespace, model_id: str, run_config: dict) -> EvaluationConfig:
    scenarios_dir = _resolve_scenarios_dir(args, run_config)
    output_dir = args.output
    if args.output == "results/fmg_bench_v1" and run_config.get("output_dir"):
        output_dir = str(run_config["output_dir"])
    return EvaluationConfig(
        model_id=model_id,
        judge_model=parse_judge_models(args.judge)[0],
        judge_models=parse_judge_models(args.judge) or run_config.get("judge_models", []),
        scenarios_dir=str(scenarios_dir),
        output_dir=output_dir,
        max_scenarios=args.max_scenarios,
        scenario_family=ScenarioFamily(args.scenario_family) if args.scenario_family else None,
        resume=args.resume and not args.restart,
        concurrency=args.concurrency,
        judge_concurrency=args.judge_concurrency,
        model_timeout_seconds=args.model_timeout,
        judge_timeout_seconds=args.judge_timeout,
        max_retries=args.max_retries,
        retry_backoff_seconds=args.retry_backoff,
        fail_fast=args.fail_fast,
        rejudge=args.rejudge,
    )


def _calibration_ids_for(args: argparse.Namespace, run_config: dict) -> list[str] | None:
    if run_config.get("calibration_candidate_ids"):
        return run_config["calibration_candidate_ids"]
    scenario_set = args.scenario_set or run_config.get("scenario_set")
    if not scenario_set:
        return None
    manifest_path = _corpus_root(args) / scenario_set / "manifest.yaml"
    if not manifest_path.exists():
        return None
    return load_scenario_set_manifest(manifest_path).calibration_candidate_ids


async def call_model(prompt: str, model_id: str, max_tokens: int = 4000, timeout_seconds: float = 120.0) -> dict:
    return await call_openrouter_model(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
    )


async def call_judge(prompt: str, judge_model: str, max_tokens: int = 1800, timeout_seconds: float = 120.0) -> dict:
    return await call_openrouter_model(
        model=judge_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
    )


def parse_judge_models(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


async def run_single_model(args: argparse.Namespace, model_id: str) -> int:
    run_config = _load_run_config(args.run_config)
    config = _build_config(args, model_id, run_config)
    runner = SystemBenchmarkRunner(config)
    scenarios = runner.load_scenarios()

    print(f"\n{'='*60}")
    print("FMG-BENCH")
    print(f"{'='*60}")
    print(f"Model: {model_id}")
    print(f"Judge panel: {', '.join(parse_judge_models(args.judge))}")
    print(f"Scenarios: {len(scenarios)}")
    if args.scenario_family:
        print(f"Family filter: {args.scenario_family}")
    print(f"Output: {config.output_dir}")
    print(f"Concurrency: {args.concurrency}")
    checkpoint_mode = "rejudge" if config.rejudge else ("resume" if config.resume else "restart")
    print(f"Checkpoint mode: {checkpoint_mode}")
    print(f"{'='*60}\n")

    if args.dry_run:
        family_counts: dict[str, int] = {}
        for scenario in scenarios:
            family_counts[scenario.family.value] = family_counts.get(scenario.family.value, 0) + 1
        print("Dry run complete. Loaded scenarios:")
        for family, count in sorted(family_counts.items()):
            print(f"  {family}: {count}")
        return 0

    if args.rebuild_from_checkpoint:
        run = runner.load_run_from_checkpoint()
        paths = runner.save_run(run)
        print("Rebuilt artifacts from checkpoint:")
        for key, path in paths.items():
            print(f"  {key}: {path}")
        return 0

    run = await runner.run(
        lambda prompt: call_model(prompt, model_id, max_tokens=args.model_max_tokens, timeout_seconds=args.model_timeout),
        lambda prompt, judge_model: call_judge(prompt, judge_model, max_tokens=args.judge_max_tokens, timeout_seconds=args.judge_timeout),
    )
    paths = runner.save_run(run)
    print("Saved artifacts:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    return 0


async def main_async() -> int:
    args = parse_args()
    if args.resume and args.restart:
        print("Error: --resume and --restart are mutually exclusive")
        return 1
    if args.rejudge and args.restart:
        print("Error: --rejudge and --restart are mutually exclusive")
        return 1
    if args.rejudge:
        args.resume = True

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    run_config = _load_run_config(args.run_config)
    configured_models = _models_from_run_config(run_config)

    if (
        not args.model
        and not args.all_models
        and not configured_models
        and not args.plan_run
        and not args.calibration_export
        and not args.dry_run
        and not args.rebuild_from_checkpoint
    ):
        print("Error: provide --model or use --all-models")
        return 1

    if args.all_models:
        models = configured_models or SystemBenchmarkRunner.configured_models()
    elif configured_models and not args.model:
        models = configured_models
    else:
        models = [args.model or "dry-run"]

    if args.plan_run:
        config = _build_config(args, models[0], run_config)
        runner = SystemBenchmarkRunner(config)
        print(json.dumps(runner.plan_run(models), indent=2))
        return 0

    if args.calibration_export:
        config = _build_config(args, models[0], run_config)
        runner = SystemBenchmarkRunner(config)
        scenarios = runner.load_scenarios()
        path = export_calibration_packet_csv(
            scenarios,
            args.calibration_export,
            calibration_ids=_calibration_ids_for(args, run_config),
        )
        print(f"Calibration packet written: {path}")
        return 0

    if args.model_concurrency <= 1 or len(models) <= 1 or args.dry_run or args.rebuild_from_checkpoint:
        exit_code = 0
        for model_id in models:
            result = await run_single_model(args, model_id)
            exit_code = exit_code or result
        return exit_code

    print(f"Running {len(models)} models with model concurrency {args.model_concurrency}")
    results = await run_model_batch(
        model_ids=models,
        config_factory=lambda model_id: _build_config(args, model_id, run_config),
        model_fn_factory=lambda model_id: (
            lambda prompt: call_model(prompt, model_id, max_tokens=args.model_max_tokens, timeout_seconds=args.model_timeout)
        ),
        judge_fn=lambda prompt, judge_model: call_judge(
            prompt, judge_model, max_tokens=args.judge_max_tokens, timeout_seconds=args.judge_timeout
        ),
        model_concurrency=args.model_concurrency,
        save=True,
    )
    print("Saved artifacts:")
    for model_id, payload in results.items():
        print(f"  {model_id}:")
        for key, path in payload["paths"].items():
            print(f"    {key}: {path}")
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
