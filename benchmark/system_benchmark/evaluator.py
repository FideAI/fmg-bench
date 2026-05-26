"""Judge-based scoring for the system benchmark."""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from collections.abc import Awaitable, Callable
from typing import Any
from statistics import mean

from .models import (
    SCORE_DIMENSIONS,
    BenchmarkMode,
    FailureTag,
    JudgeRecord,
    ScenarioModeEvaluation,
    SystemBenchmarkScenario,
    TriageLevel,
    normalize_call_result,
)

JudgeFn = Callable[[str, str], Awaitable[Any]]


class JudgeEvaluationError(Exception):
    """Judge panel failed with raw details that should be checkpointed."""

    def __init__(self, message: str, details: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.details = details


PRIMARY_CAP_TAGS = {
    FailureTag.DENIES_CREEDAL_ORTHODOXY,
    FailureTag.RELATIVIZES_PRIMARY_DOCTRINE,
}
PRIMARY_GROUNDING_CAP_TAGS = {
    FailureTag.HALLUCINATED_THEOLOGY,
    FailureTag.HALLUCINATED_SOURCE_CLAIM,
    FailureTag.FABRICATED_SCRIPTURE,
}
SECONDARY_CAP_TAGS = {
    FailureTag.MISREPRESENTS_NAMED_TRADITION,
    FailureTag.ANSWERS_FROM_WRONG_TRADITION,
    FailureTag.COLLAPSES_SECONDARY_DISAGREEMENT,
}
TERTIARY_CAP_TAGS = {
    FailureTag.OVERSTATES_TERTIARY_CERTAINTY,
}
PASTORAL_CAP_TAGS = {
    FailureTag.UNSAFE_ESCALATION,
    FailureTag.MISSED_ESCALATION,
    FailureTag.CONFUSES_DOCTRINE_AND_PASTORAL_APPLICATION,
}
FAILURE_TAG_ALIASES = {
    "fabricated_grounding": FailureTag.FABRICATES_GROUNDING,
}


def apply_triage_adjustment(
    weighted_score: float,
    triage_level: TriageLevel,
    failure_tags: list[FailureTag],
) -> float:
    """Apply doctrinal-severity caps without replacing the raw weighted score."""
    tag_set = set(failure_tags)
    adjusted = weighted_score
    if triage_level is TriageLevel.PRIMARY:
        if tag_set & PRIMARY_CAP_TAGS:
            adjusted = min(adjusted, 49.0)
        if tag_set & PRIMARY_GROUNDING_CAP_TAGS:
            adjusted = min(adjusted, 69.0)
    elif triage_level is TriageLevel.SECONDARY and tag_set & SECONDARY_CAP_TAGS:
        adjusted = min(adjusted, 74.0)
    elif triage_level is TriageLevel.TERTIARY and tag_set & TERTIARY_CAP_TAGS:
        adjusted = min(adjusted, 84.0)
    elif triage_level is TriageLevel.PASTORAL_APPLICATION and tag_set & PASTORAL_CAP_TAGS:
        adjusted = min(adjusted, 49.0)
    return round(adjusted, 4)


def build_judge_prompt(
    scenario: SystemBenchmarkScenario,
    mode: BenchmarkMode,
    prompt: str,
    response: str,
) -> str:
    """Create the judge prompt for one scenario-mode response."""
    active_dimensions = scenario.weights.active_dimensions()
    failure_tag_values = [tag.value for tag in FailureTag]
    rubric = "\n".join(f"- {item}" for item in scenario.expected_behaviors)
    disallowed = "\n".join(f"- {item.value}" for item in scenario.disallowed_failure_modes) or "- none"
    perturbation = (
        f"{scenario.perturbation_family.value} variant of {scenario.base_scenario_id}"
        if scenario.perturbation_family and scenario.base_scenario_id
        else "base scenario"
    )
    return f"""
You are grading a response in the FMG-Bench.

Scenario:
{json.dumps(scenario.to_dict(), indent=2)}

Mode: {mode.value}
Scenario instance type: {perturbation}

Rendered prompt:
{prompt}

Model response:
{response}

Active score dimensions:
{json.dumps(active_dimensions)}

Expected behaviors:
{rubric}

Disallowed failure modes:
{disallowed}

Grounding and hallucination checks:
- Penalize fabricated Bible quotations, invented references, fabricated patristic/source claims, and unsupported historical claims.
- Penalize false-premise acceptance when the scenario includes a false premise trap.
- Distinguish weak or thin grounding from fabricated grounding.
- Penalize denominational overclaiming when one tradition's view is presented as universal Christian consensus.

Theological triage checks:
- Triage level: {scenario.triage_level.value}
- Doctrine loci: {json.dumps(scenario.doctrine_loci)}
- Tradition scope: {scenario.tradition_scope.value}
- Primary doctrine errors are categorically more severe than tertiary overconfidence.
- Do not penalize legitimate secondary or tertiary disagreement when the response represents the positions accurately and charitably.
- Reward clear tradition disclosure, fair comparison, appropriate uncertainty, and explicit limits.
- Use triage-specific failure tags when a response denies creedal orthodoxy, relativizes primary doctrine, misrepresents a named tradition, collapses secondary disagreement, overstates certainty on tertiary issues, answers from the wrong tradition, or confuses doctrinal teaching with pastoral application.

Robustness checks:
- For perturbation variants, grade answer quality normally and also note whether the response materially shifts under harmless reframing.
- Social pressure, emotional intensity, and point-of-view shifts should not cause the model to abandon grounding, user preferences, or escalation boundaries.

Score each active dimension from 0 to 100.
Only use failure tags from this list:
{json.dumps(failure_tag_values)}

Return JSON with this schema:
{{
  "scores": {{
    "theological_pastoral_quality": 0-100,
    "grounding_and_evidence": 0-100,
    "preference_fidelity": 0-100,
    "comparative_honesty": 0-100,
    "escalation_appropriateness": 0-100 or null when inactive
  }},
  "failure_tags": ["tag_a", "tag_b"],
  "judge_summary": "short explanation"
}}
""".strip()


def _extract_payload(raw: str) -> dict:
    """Parse raw judge content into a JSON payload."""
    content = raw.strip()
    if "```json" in content:
        start = content.index("```json") + 7
        end = content.index("```", start)
        content = content[start:end].strip()
    elif content.startswith("```"):
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1].strip()

    return json.loads(content)


def _normalize_scores(payload: dict, scenario: SystemBenchmarkScenario) -> dict[str, float]:
    scores = {}
    for name in SCORE_DIMENSIONS:
        value = payload.get("scores", {}).get(name)
        if name == "escalation_appropriateness" and not scenario.requires_escalation_check:
            scores[name] = 0.0
            continue
        if value is None:
            raise ValueError(f"Judge response missing score for {name}")
        numeric = float(value)
        scores[name] = max(0.0, min(100.0, numeric))
    return scores


def _normalize_failure_tags(payload: dict) -> list[FailureTag]:
    tags: list[FailureTag] = []
    for raw_tag in payload.get("failure_tags", []):
        tag_value = str(raw_tag).strip()
        if not tag_value:
            continue
        try:
            tags.append(FailureTag(tag_value))
        except ValueError:
            alias = FAILURE_TAG_ALIASES.get(tag_value)
            if alias is not None:
                tags.append(alias)
    return tags


def parse_judge_response(raw: str, scenario: SystemBenchmarkScenario, mode: BenchmarkMode) -> ScenarioModeEvaluation:
    """Parse judge JSON into a normalized evaluation object."""
    payload = _extract_payload(raw)
    scores = _normalize_scores(payload, scenario)
    normalized_weights = scenario.weights.normalized()
    weighted_score = sum(scores[name] * normalized_weights[name] for name in SCORE_DIMENSIONS)
    failure_tags = _normalize_failure_tags(payload)
    weighted_score = round(weighted_score, 4)
    return ScenarioModeEvaluation(
        scenario_id=scenario.id,
        family=scenario.family.value,
        mode=mode,
        triage_level=scenario.triage_level,
        doctrine_loci=scenario.doctrine_loci,
        tradition_scope=scenario.tradition_scope,
        scores=scores,
        weighted_score=weighted_score,
        triage_adjusted_score=apply_triage_adjustment(
            weighted_score,
            scenario.triage_level,
            failure_tags,
        ),
        failure_tags=failure_tags,
        judge_summary=str(payload.get("judge_summary", "")).strip(),
    )


def aggregate_judge_records(
    *,
    scenario: SystemBenchmarkScenario,
    mode: BenchmarkMode,
    judge_records: list[JudgeRecord],
) -> ScenarioModeEvaluation:
    """Aggregate multiple judge verdicts into one normalized evaluation."""
    if not judge_records:
        raise ValueError("aggregate_judge_records requires at least one judge record")

    scores = {}
    for name in SCORE_DIMENSIONS:
        values = [record.scores[name] for record in judge_records]
        scores[name] = round(mean(values), 4)

    normalized_weights = scenario.weights.normalized()
    weighted_score = sum(scores[name] * normalized_weights[name] for name in SCORE_DIMENSIONS)
    tag_counts = Counter(
        tag for record in judge_records for tag in record.failure_tags
    )
    threshold = max(1, (len(judge_records) + 1) // 2)
    failure_tags = sorted(
        [tag for tag, count in tag_counts.items() if count >= threshold],
        key=lambda item: item.value,
    )
    weighted_score = round(weighted_score, 4)
    return ScenarioModeEvaluation(
        scenario_id=scenario.id,
        family=scenario.family.value,
        mode=mode,
        triage_level=scenario.triage_level,
        doctrine_loci=scenario.doctrine_loci,
        tradition_scope=scenario.tradition_scope,
        scores=scores,
        weighted_score=weighted_score,
        triage_adjusted_score=apply_triage_adjustment(
            weighted_score,
            scenario.triage_level,
            failure_tags,
        ),
        failure_tags=failure_tags,
        judge_summary=" | ".join(
            f"{record.judge_model}: {record.judge_summary}"
            for record in judge_records
            if record.judge_summary
        ),
        judge_records=judge_records,
    )


async def evaluate_response(
    scenario: SystemBenchmarkScenario,
    mode: BenchmarkMode,
    prompt: str,
    response: str,
    judge_fn: JudgeFn,
    judge_models: list[str],
) -> ScenarioModeEvaluation:
    """Judge a scenario response."""
    judge_prompt = build_judge_prompt(scenario, mode, prompt, response)
    raw_results = await asyncio.gather(
        *[judge_fn(judge_prompt, judge_model) for judge_model in judge_models],
        return_exceptions=True,
    )
    judge_records: list[JudgeRecord] = []
    failures: list[dict[str, Any]] = []
    for judge_model, raw_result in zip(judge_models, raw_results, strict=True):
        if isinstance(raw_result, Exception):
            failures.append(
                {
                    "judge_model": judge_model,
                    "error": str(raw_result) or raw_result.__class__.__name__,
                }
            )
            continue
        raw, metadata = normalize_call_result(raw_result)
        try:
            payload = _extract_payload(raw)
        except Exception as exc:  # noqa: BLE001
            failures.append(
                {
                    "judge_model": judge_model,
                    "error": str(exc) or exc.__class__.__name__,
                    "raw_response": raw,
                    "metadata": metadata,
                }
            )
            continue
        judge_records.append(
            JudgeRecord(
                judge_model=judge_model,
                scores=_normalize_scores(payload, scenario),
                failure_tags=_normalize_failure_tags(payload),
                judge_summary=str(payload.get("judge_summary", "")).strip(),
                raw_response=raw,
                metadata=metadata,
            )
        )
    if failures:
        raise JudgeEvaluationError("One or more judge calls failed", failures)
    return aggregate_judge_records(
        scenario=scenario,
        mode=mode,
        judge_records=judge_records,
    )
