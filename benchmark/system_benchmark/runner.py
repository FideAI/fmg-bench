"""Resumable, concurrent system benchmark runner."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .checkpoint import BenchmarkCheckpoint
from .evaluator import JudgeEvaluationError, evaluate_response
from .loader import load_scenarios
from .models import (
    BenchmarkMode,
    EvaluationConfig,
    FailureTag,
    JudgeRecord,
    ModeResponse,
    ScenarioModeEvaluation,
    SystemBenchmarkRun,
    TraditionScope,
    TriageLevel,
    model_slug,
    normalize_call_result,
)
from .renderers import render_prompt
from .reports import build_markdown_report
from .scoring import build_summary, compute_deltas

ModelFn = Callable[[str], Awaitable[Any]]
JudgeFn = Callable[[str, str], Awaitable[Any]]
ConfigFactory = Callable[[str], EvaluationConfig]
ModelFnFactory = Callable[[str], ModelFn]

logger = logging.getLogger(__name__)


def _format_exception(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__


class SystemBenchmarkRunner:
    """Run the FMG-Bench for one model."""

    def __init__(self, config: EvaluationConfig):
        self.config = config
        self._progress_lock = asyncio.Lock()
        self._retry_attempts_by_label: dict[str, list[dict[str, Any]]] = {}

    def load_scenarios(self):
        scenarios = load_scenarios(self.config.scenarios_dir)
        if self.config.scenario_family:
            scenarios = [s for s in scenarios if s.family == self.config.scenario_family]
        if self.config.max_scenarios is not None:
            scenarios = scenarios[: self.config.max_scenarios]
        return scenarios

    def plan_run(self, model_ids: list[str] | None = None) -> dict[str, Any]:
        """Estimate benchmark size and output paths without model or judge calls."""
        scenarios = self.load_scenarios()
        models = model_ids or [self.config.model_id]
        base_count = sum(1 for scenario in scenarios if scenario.base_scenario_id is None)
        perturbation_count = len(scenarios) - base_count
        rendered_item_count = len(scenarios) * len(BenchmarkMode) * len(models)
        judge_count = len(self.config.resolved_judge_models())
        return {
            "scenario_count": len(scenarios),
            "base_scenario_count": base_count,
            "perturbation_scenario_count": perturbation_count,
            "mode_count": len(BenchmarkMode),
            "model_count": len(models),
            "models": models,
            "judge_panel": self.config.resolved_judge_models(),
            "judge_model_count": judge_count,
            "rendered_item_count": rendered_item_count,
            "model_call_count": rendered_item_count,
            "judge_call_count": rendered_item_count * judge_count,
            "approximate_api_call_volume": rendered_item_count * (1 + judge_count),
            "output_dir": str(self._output_dir()),
            "checkpoint_paths": [
                str(self._output_dir() / f"{model_slug(model)}_checkpoint.jsonl") for model in models
            ],
        }

    def _output_dir(self) -> Path:
        path = Path(self.config.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _slug(self) -> str:
        return model_slug(self.config.model_id)

    def _checkpoint_path(self) -> Path:
        return self._output_dir() / f"{self._slug()}_checkpoint.jsonl"

    def _load_checkpoint(self) -> BenchmarkCheckpoint:
        path = self._checkpoint_path()
        if path.exists() and not self.config.resume:
            path.unlink()
        return BenchmarkCheckpoint(path)

    def _item_id(self, scenario_id: str, mode: BenchmarkMode) -> str:
        return f"{scenario_id}::{mode.value}"

    @staticmethod
    def configured_models(config_path: Path | None = None) -> list[str]:
        """Load enabled models from the shared evaluation config."""
        path = config_path or Path(__file__).resolve().parents[1] / "config" / "models.yaml"
        with path.open() as handle:
            payload = yaml.safe_load(handle)
        return [item["model_name"] for item in payload["models"] if item.get("enabled", True)]

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat()

    def _summary_payload(self, run: SystemBenchmarkRun, generated_at: str) -> dict[str, Any]:
        payload = dict(run.summary)
        payload["model_id"] = run.model_id
        payload["judge_model"] = run.judge_model
        payload["scenario_count"] = run.scenario_count
        payload["generated_at"] = generated_at
        return payload

    @staticmethod
    def _response_from_record(record: dict[str, Any]) -> ModeResponse | None:
        payload = record.get("response_record")
        if not payload:
            return None
        return ModeResponse(
            scenario_id=payload["scenario_id"],
            family=payload["family"],
            mode=BenchmarkMode(payload["mode"]),
            prompt=payload["prompt"],
            response=payload["response"],
            metadata=payload.get("metadata", {}),
        )

    async def _retry(
        self,
        label: str,
        operation: Callable[[], Awaitable[Any]],
        timeout_seconds: float,
    ) -> Any:
        last_exc: Exception | None = None
        attempts: list[dict[str, Any]] = []
        for attempt in range(self.config.max_retries + 1):
            try:
                result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
                if attempts:
                    self._retry_attempts_by_label[label] = attempts
                return result
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                attempts.append(
                    {
                        "label": label,
                        "attempt": attempt + 1,
                        "max_attempts": self.config.max_retries + 1,
                        "error": _format_exception(exc),
                        "details": getattr(exc, "details", {}),
                        "updated_at": self._now_iso(),
                    }
                )
                if isinstance(exc, JudgeEvaluationError):
                    attempts[-1]["judge_error_details"] = exc.details
                if attempt >= self.config.max_retries:
                    break
                delay = self.config.retry_backoff_seconds * (attempt + 1)
                logger.warning(
                    "%s failed on attempt %d/%d: %s. Retrying in %.1fs",
                    label,
                    attempt + 1,
                    self.config.max_retries + 1,
                    _format_exception(exc),
                    delay,
                )
                await asyncio.sleep(delay)
        assert last_exc is not None
        self._retry_attempts_by_label[label] = attempts
        setattr(last_exc, "benchmark_retry_attempts", attempts)
        raise last_exc

    async def _retry_with_attempts(
        self,
        label: str,
        operation: Callable[[], Awaitable[Any]],
        timeout_seconds: float,
    ) -> tuple[Any, list[dict[str, Any]]]:
        self._retry_attempts_by_label.pop(label, None)
        result = await self._retry(label, operation, timeout_seconds)
        attempts = self._retry_attempts_by_label.pop(label, [])
        return result, attempts

    async def _record_progress(self, completed: int, total: int, item_id: str) -> None:
        async with self._progress_lock:
            logger.info("Completed %d/%d items (%s)", completed, total, item_id)

    async def _process_item(
        self,
        *,
        scenario,
        mode: BenchmarkMode,
        model_fn: ModelFn,
        judge_fn: JudgeFn,
        model_semaphore: asyncio.Semaphore,
        judge_semaphore: asyncio.Semaphore,
        checkpoint: BenchmarkCheckpoint,
    ) -> tuple[ModeResponse | None, ScenarioModeEvaluation | None, dict[str, Any] | None]:
        item_id = self._item_id(scenario.id, mode)
        cached = checkpoint.get(item_id)

        if cached and cached.get("status") == "completed" and not self.config.rejudge:
            return (
                self._deserialize_response(cached["response_record"]),
                self._deserialize_evaluation(cached["evaluation_record"]),
                None,
            )

        prompt = render_prompt(scenario, mode)
        response_record = cached.get("response_record") if cached else None

        if response_record:
            response = self._deserialize_response(response_record)
        elif self.config.rejudge:
            failed = {
                "item_id": item_id,
                "scenario_id": scenario.id,
                "family": scenario.family.value,
                "mode": mode.value,
                "status": "failed_rejudge",
                "error": "Cannot rejudge item without a checkpointed response_record",
                "updated_at": self._now_iso(),
            }
            checkpoint.save(failed)
            if self.config.fail_fast:
                raise RuntimeError(failed["error"])
            return None, None, failed
        else:
            try:
                async with model_semaphore:
                    retry_label = f"model call {self.config.model_id}/{item_id}"
                    response_result, retry_attempts = await self._retry_with_attempts(
                        retry_label,
                        lambda: model_fn(prompt),
                        self.config.model_timeout_seconds,
                    )
                    response_text, response_metadata = normalize_call_result(response_result)
                    if retry_attempts:
                        response_metadata["retry_attempts"] = retry_attempts
                response = ModeResponse(
                    scenario_id=scenario.id,
                    family=scenario.family.value,
                    mode=mode,
                    prompt=prompt,
                    response=response_text,
                    metadata=response_metadata,
                )
                checkpoint.save(
                    {
                        "item_id": item_id,
                        "scenario_id": scenario.id,
                        "family": scenario.family.value,
                        "mode": mode.value,
                        "status": "response_completed",
                        "response_record": response.to_dict(),
                        "updated_at": self._now_iso(),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                failed = {
                    "item_id": item_id,
                    "scenario_id": scenario.id,
                    "family": scenario.family.value,
                    "mode": mode.value,
                    "status": "failed_model",
                    "error": _format_exception(exc),
                    "retry_attempts": getattr(exc, "benchmark_retry_attempts", []),
                    "call_error_details": getattr(exc, "details", {}),
                    "updated_at": self._now_iso(),
                }
                checkpoint.save(failed)
                if self.config.fail_fast:
                    raise
                return None, None, failed

        try:
            async with judge_semaphore:
                retry_label = (
                    f"judge panel {','.join(self.config.resolved_judge_models())}/{item_id}"
                )
                evaluation, retry_attempts = await self._retry_with_attempts(
                    retry_label,
                    lambda: self._evaluate_with_judge(
                        scenario=scenario,
                        mode=mode,
                        prompt=prompt,
                        response=response.response,
                        judge_fn=judge_fn,
                    ),
                    self.config.judge_timeout_seconds,
                )
                if retry_attempts:
                    evaluation.metadata["retry_attempts"] = retry_attempts
            checkpoint.save(
                {
                    "item_id": item_id,
                    "scenario_id": scenario.id,
                    "family": scenario.family.value,
                    "mode": mode.value,
                    "status": "completed",
                    "response_record": response.to_dict(),
                    "evaluation_record": evaluation.to_dict(),
                    "updated_at": self._now_iso(),
                }
            )
            return response, evaluation, None
        except Exception as exc:  # noqa: BLE001
            failed = {
                "item_id": item_id,
                "scenario_id": scenario.id,
                "family": scenario.family.value,
                "mode": mode.value,
                "status": "failed_judge",
                "response_record": response.to_dict(),
                "error": _format_exception(exc),
                "retry_attempts": getattr(exc, "benchmark_retry_attempts", []),
                "call_error_details": getattr(exc, "details", {}),
                "updated_at": self._now_iso(),
            }
            if isinstance(exc, JudgeEvaluationError):
                failed["judge_error_details"] = exc.details
            checkpoint.save(failed)
            if self.config.fail_fast:
                raise
            return response, None, failed

    async def _evaluate_with_judge(
        self,
        *,
        scenario,
        mode: BenchmarkMode,
        prompt: str,
        response: str,
        judge_fn: JudgeFn,
    ) -> ScenarioModeEvaluation:
        return await evaluate_response(
            scenario,
            mode,
            prompt,
            response,
            judge_fn,
            self.config.resolved_judge_models(),
        )

    @staticmethod
    def _deserialize_response(payload: dict[str, Any]) -> ModeResponse:
        return ModeResponse(
            scenario_id=payload["scenario_id"],
            family=payload["family"],
            mode=BenchmarkMode(payload["mode"]),
            prompt=payload["prompt"],
            response=payload["response"],
            metadata=payload.get("metadata", {}),
        )

    @staticmethod
    def _deserialize_evaluation(payload: dict[str, Any]) -> ScenarioModeEvaluation:
        return ScenarioModeEvaluation(
            scenario_id=payload["scenario_id"],
            family=payload["family"],
            mode=BenchmarkMode(payload["mode"]),
            triage_level=TriageLevel(
                payload.get("triage_level", TriageLevel.PASTORAL_APPLICATION.value)
            ),
            doctrine_loci=[str(item) for item in payload.get("doctrine_loci", [])],
            tradition_scope=TraditionScope(
                payload.get("tradition_scope", TraditionScope.PASTORAL.value)
            ),
            scores={key: float(value) for key, value in payload["scores"].items()},
            weighted_score=float(payload["weighted_score"]),
            triage_adjusted_score=float(
                payload.get("triage_adjusted_score", payload["weighted_score"])
            ),
            failure_tags=[FailureTag(tag) for tag in payload.get("failure_tags", [])],
            judge_summary=payload.get("judge_summary", ""),
            judge_records=[
                JudgeRecord(
                    judge_model=record["judge_model"],
                    scores={key: float(value) for key, value in record["scores"].items()},
                    failure_tags=[FailureTag(tag) for tag in record.get("failure_tags", [])],
                    judge_summary=record.get("judge_summary", ""),
                    raw_response=record.get("raw_response", ""),
                    metadata=record.get("metadata", {}),
                )
                for record in payload.get("judge_records", [])
            ],
            metadata=payload.get("metadata", {}),
        )

    def _build_run_from_checkpoint(
        self,
        checkpoint: BenchmarkCheckpoint,
        scenario_count: int,
    ) -> SystemBenchmarkRun:
        responses: list[ModeResponse] = []
        evaluations: list[ScenarioModeEvaluation] = []
        failed_items: list[dict[str, Any]] = []

        for record in checkpoint.records():
            response_payload = record.get("response_record")
            if response_payload:
                responses.append(self._deserialize_response(response_payload))
            evaluation_payload = record.get("evaluation_record")
            if evaluation_payload:
                evaluations.append(self._deserialize_evaluation(evaluation_payload))
            if str(record.get("status", "")).startswith("failed"):
                failed_items.append(
                    {
                        "item_id": record["item_id"],
                        "scenario_id": record["scenario_id"],
                        "mode": record["mode"],
                        "status": record["status"],
                        "error": record.get("error", ""),
                        "judge_error_details": record.get("judge_error_details", []),
                        "retry_attempts": record.get("retry_attempts", []),
                        "call_error_details": record.get("call_error_details", {}),
                    }
                )

        deduped_responses = {
            (item.scenario_id, item.mode): item
            for item in responses
        }
        responses = [deduped_responses[key] for key in sorted(deduped_responses)]
        deduped_evaluations = {
            (item.scenario_id, item.mode): item
            for item in evaluations
        }
        evaluations = [deduped_evaluations[key] for key in sorted(deduped_evaluations)]

        deltas = compute_deltas(evaluations)
        summary = build_summary(
            evaluations,
            deltas,
            total_expected_items=scenario_count * len(BenchmarkMode),
            completed_items=len(evaluations),
            failed_items=len(failed_items),
        )
        return SystemBenchmarkRun(
            model_id=self.config.model_id,
            judge_model=",".join(self.config.resolved_judge_models()),
            scenario_count=scenario_count,
            responses=responses,
            evaluations=evaluations,
            deltas=deltas,
            summary=summary,
            failed_items=failed_items,
        )

    def load_run_from_checkpoint(self) -> SystemBenchmarkRun:
        """Rebuild a run artifact from the current checkpoint state."""
        scenarios = self.load_scenarios()
        checkpoint = BenchmarkCheckpoint(self._checkpoint_path())
        return self._build_run_from_checkpoint(checkpoint, len(scenarios))

    async def run(self, model_fn: ModelFn, judge_fn: JudgeFn) -> SystemBenchmarkRun:
        """Execute the system benchmark with checkpointed concurrency."""
        scenarios = self.load_scenarios()
        checkpoint = self._load_checkpoint()
        total_items = len(scenarios) * len(BenchmarkMode)
        model_semaphore = asyncio.Semaphore(max(1, self.config.concurrency))
        judge_semaphore = asyncio.Semaphore(
            max(1, self.config.judge_concurrency or self.config.concurrency)
        )

        tasks = [
            self._process_item(
                scenario=scenario,
                mode=mode,
                model_fn=model_fn,
                judge_fn=judge_fn,
                model_semaphore=model_semaphore,
                judge_semaphore=judge_semaphore,
                checkpoint=checkpoint,
            )
            for scenario in scenarios
            for mode in BenchmarkMode
        ]

        completed = 0
        for future in asyncio.as_completed(tasks):
            await future
            completed += 1
            await self._record_progress(completed, total_items, self.config.model_id)

        return self._build_run_from_checkpoint(checkpoint, len(scenarios))

    def save_run(self, run: SystemBenchmarkRun) -> dict[str, Path]:
        """Persist benchmark artifacts using stable filenames."""
        generated_at = self._now_iso()
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        output_dir = self._output_dir()
        prefix = f"{self._slug()}_{timestamp}"
        latest_prefix = f"{self._slug()}_latest"
        paths = {
            "responses": output_dir / f"{prefix}_responses.json",
            "evaluations": output_dir / f"{prefix}_evaluations.json",
            "deltas": output_dir / f"{prefix}_deltas.json",
            "summary": output_dir / f"{prefix}_summary.json",
            "report": output_dir / f"{prefix}_report.md",
            "checkpoint": self._checkpoint_path(),
            "latest_responses": output_dir / f"{latest_prefix}_responses.json",
            "latest_evaluations": output_dir / f"{latest_prefix}_evaluations.json",
            "latest_deltas": output_dir / f"{latest_prefix}_deltas.json",
            "latest_summary": output_dir / f"{latest_prefix}_summary.json",
            "latest_report": output_dir / f"{latest_prefix}_report.md",
        }
        responses_payload = [item.to_dict() for item in run.responses]
        evaluations_payload = [item.to_dict() for item in run.evaluations]
        deltas_payload = [item.to_dict() for item in run.deltas]
        summary_payload = self._summary_payload(run, generated_at)
        report_payload = build_markdown_report(run)

        with paths["responses"].open("w") as handle:
            json.dump(responses_payload, handle, indent=2)
        with paths["evaluations"].open("w") as handle:
            json.dump(evaluations_payload, handle, indent=2)
        with paths["deltas"].open("w") as handle:
            json.dump(deltas_payload, handle, indent=2)
        with paths["summary"].open("w") as handle:
            json.dump(summary_payload, handle, indent=2)
        with paths["report"].open("w") as handle:
            handle.write(report_payload)

        with paths["latest_responses"].open("w") as handle:
            json.dump(responses_payload, handle, indent=2)
        with paths["latest_evaluations"].open("w") as handle:
            json.dump(evaluations_payload, handle, indent=2)
        with paths["latest_deltas"].open("w") as handle:
            json.dump(deltas_payload, handle, indent=2)
        with paths["latest_summary"].open("w") as handle:
            json.dump(summary_payload, handle, indent=2)
        with paths["latest_report"].open("w") as handle:
            handle.write(report_payload)

        return paths


async def run_model_batch(
    *,
    model_ids: list[str],
    config_factory: ConfigFactory,
    model_fn_factory: ModelFnFactory,
    judge_fn: JudgeFn,
    model_concurrency: int = 1,
    save: bool = True,
) -> dict[str, dict[str, Any]]:
    """Run one benchmark config per model with bounded model-level parallelism.

    Each model keeps its own checkpoint and output artifact names, so interrupted
    batches can resume independently with the same ``--resume`` semantics as a
    single-model run.
    """
    semaphore = asyncio.Semaphore(max(1, model_concurrency))
    results: dict[str, dict[str, Any]] = {}

    async def run_one(model_id: str) -> tuple[str, dict[str, Any]]:
        async with semaphore:
            runner = SystemBenchmarkRunner(config_factory(model_id))
            run = await runner.run(model_fn_factory(model_id), judge_fn)
            paths = runner.save_run(run) if save else {}
            return model_id, {"run": run, "paths": paths}

    tasks = [asyncio.create_task(run_one(model_id)) for model_id in model_ids]
    for future in asyncio.as_completed(tasks):
        model_id, payload = await future
        results[model_id] = payload
    return results
