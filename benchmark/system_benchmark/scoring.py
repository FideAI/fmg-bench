"""Aggregation and delta helpers for the system benchmark."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .models import (
    SCORE_DIMENSIONS,
    BenchmarkMode,
    DeltaRecord,
    ScenarioModeEvaluation,
    TriageLevel,
)

DELTA_PAIRS = (
    (BenchmarkMode.RAW_MODEL, BenchmarkMode.GUIDED_DEFAULT),
    (BenchmarkMode.GUIDED_DEFAULT, BenchmarkMode.PREFERENCE_CONFIGURED),
    (BenchmarkMode.PREFERENCE_CONFIGURED, BenchmarkMode.PERSPECTIVE_COMPARE),
)


def compute_deltas(evaluations: list[ScenarioModeEvaluation]) -> list[DeltaRecord]:
    """Compute pairwise deltas between benchmark modes."""
    index = {(item.scenario_id, item.mode): item for item in evaluations}
    first_by_scenario: dict[str, ScenarioModeEvaluation] = {}
    for item in evaluations:
        first_by_scenario.setdefault(item.scenario_id, item)
    deltas: list[DeltaRecord] = []
    for scenario_id in sorted(first_by_scenario):
        first = first_by_scenario[scenario_id]
        family = first.family
        triage_level = first.triage_level
        for from_mode, to_mode in DELTA_PAIRS:
            source = index.get((scenario_id, from_mode))
            target = index.get((scenario_id, to_mode))
            if not source or not target:
                continue
            score_deltas = {
                name: round(target.scores[name] - source.scores[name], 4) for name in SCORE_DIMENSIONS
            }
            source_tags = set(source.failure_tags)
            target_tags = set(target.failure_tags)
            deltas.append(
                DeltaRecord(
                    scenario_id=scenario_id,
                    family=family,
                    triage_level=triage_level,
                    from_mode=from_mode,
                    to_mode=to_mode,
                    weighted_score_delta=round(target.weighted_score - source.weighted_score, 4),
                    triage_adjusted_score_delta=round(
                        target.triage_adjusted_score - source.triage_adjusted_score,
                        4,
                    ),
                    score_deltas=score_deltas,
                    new_failure_tags=sorted(target_tags - source_tags, key=lambda item: item.value),
                    removed_failure_tags=sorted(source_tags - target_tags, key=lambda item: item.value),
                )
            )
    return deltas


def build_summary(
    evaluations: list[ScenarioModeEvaluation],
    deltas: list[DeltaRecord],
    *,
    total_expected_items: int | None = None,
    completed_items: int | None = None,
    failed_items: int = 0,
) -> dict[str, Any]:
    """Build run-level aggregates used by JSON summaries and markdown reports."""
    by_mode: dict[str, list[ScenarioModeEvaluation]] = defaultdict(list)
    by_family: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_family_adjusted: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_triage: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_triage_adjusted: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_locus: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    failure_counts: dict[str, Counter] = defaultdict(Counter)
    failure_counts_by_triage: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    by_base_variant: dict[tuple[str, str], dict[str, ScenarioModeEvaluation]] = defaultdict(dict)

    for item in evaluations:
        by_mode[item.mode.value].append(item)
        by_family[item.family][item.mode.value].append(item.weighted_score)
        by_family_adjusted[item.family][item.mode.value].append(item.triage_adjusted_score)
        by_triage[item.triage_level.value][item.mode.value].append(item.weighted_score)
        by_triage_adjusted[item.triage_level.value][item.mode.value].append(
            item.triage_adjusted_score
        )
        for locus in item.doctrine_loci:
            by_locus[locus][item.mode.value].append(item.triage_adjusted_score)
        failure_counts[item.mode.value].update(tag.value for tag in item.failure_tags)
        failure_counts_by_triage[item.triage_level.value][item.mode.value].update(
            tag.value for tag in item.failure_tags
        )
        if "__" in item.scenario_id:
            base_id = item.scenario_id.split("__", 1)[0]
            by_base_variant[(base_id, item.mode.value)][item.scenario_id] = item
        else:
            by_base_variant[(item.scenario_id, item.mode.value)]["__base__"] = item

    family_aggregates = {
        family: {
            mode: round(sum(values) / len(values), 4)
            for mode, values in sorted(mode_scores.items())
        }
        for family, mode_scores in sorted(by_family.items())
    }
    family_triage_adjusted_aggregates = {
        family: {
            mode: round(sum(values) / len(values), 4)
            for mode, values in sorted(mode_scores.items())
        }
        for family, mode_scores in sorted(by_family_adjusted.items())
    }

    mode_averages = {
        mode: round(sum(item.weighted_score for item in items) / len(items), 4)
        for mode, items in sorted(by_mode.items())
    }
    mode_triage_adjusted_averages = {
        mode: round(sum(item.triage_adjusted_score for item in items) / len(items), 4)
        for mode, items in sorted(by_mode.items())
    }

    triage_level_aggregates = {
        level: {
            mode: round(sum(values) / len(values), 4)
            for mode, values in sorted(mode_scores.items())
        }
        for level, mode_scores in sorted(by_triage.items())
    }
    triage_level_adjusted_aggregates = {
        level: {
            mode: round(sum(values) / len(values), 4)
            for mode, values in sorted(mode_scores.items())
        }
        for level, mode_scores in sorted(by_triage_adjusted.items())
    }
    doctrine_locus_aggregates = {
        locus: {
            mode: round(sum(values) / len(values), 4)
            for mode, values in sorted(mode_scores.items())
        }
        for locus, mode_scores in sorted(by_locus.items())
    }

    delta_summary: dict[str, dict[str, float]] = defaultdict(dict)
    for pair in DELTA_PAIRS:
        pair_name = f"{pair[1].value}_minus_{pair[0].value}"
        pair_deltas = [item.weighted_score_delta for item in deltas if (item.from_mode, item.to_mode) == pair]
        pair_adjusted_deltas = [
            item.triage_adjusted_score_delta
            for item in deltas
            if (item.from_mode, item.to_mode) == pair
        ]
        delta_summary["weighted_score_delta"][pair_name] = (
            round(sum(pair_deltas) / len(pair_deltas), 4) if pair_deltas else 0.0
        )
        delta_summary["triage_adjusted_score_delta"][pair_name] = (
            round(sum(pair_adjusted_deltas) / len(pair_adjusted_deltas), 4)
            if pair_adjusted_deltas
            else 0.0
        )

    delta_by_triage: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for level in TriageLevel:
        level_deltas = [item for item in deltas if item.triage_level is level]
        for pair in DELTA_PAIRS:
            pair_name = f"{pair[1].value}_minus_{pair[0].value}"
            pair_items = [item for item in level_deltas if (item.from_mode, item.to_mode) == pair]
            delta_by_triage[level.value]["weighted_score_delta"][pair_name] = (
                round(sum(item.weighted_score_delta for item in pair_items) / len(pair_items), 4)
                if pair_items
                else 0.0
            )
            delta_by_triage[level.value]["triage_adjusted_score_delta"][pair_name] = (
                round(
                    sum(item.triage_adjusted_score_delta for item in pair_items) / len(pair_items),
                    4,
                )
                if pair_items
                else 0.0
            )

    compare_primary = [
        item.triage_adjusted_score
        for item in evaluations
        if item.mode is BenchmarkMode.PERSPECTIVE_COMPARE and item.triage_level is TriageLevel.PRIMARY
    ]
    compare_secondary_tertiary = [
        item.triage_adjusted_score
        for item in evaluations
        if item.mode is BenchmarkMode.PERSPECTIVE_COMPARE
        and item.triage_level in {TriageLevel.SECONDARY, TriageLevel.TERTIARY}
    ]
    compare_mode_triage_split = {
        "primary": round(sum(compare_primary) / len(compare_primary), 4) if compare_primary else None,
        "secondary_tertiary": (
            round(sum(compare_secondary_tertiary) / len(compare_secondary_tertiary), 4)
            if compare_secondary_tertiary
            else None
        ),
    }

    stability_scores: dict[str, list[float]] = defaultdict(list)
    stability_instances: list[dict[str, Any]] = []
    for (base_id, mode), instances in sorted(by_base_variant.items()):
        base = instances.get("__base__")
        variants = [item for key, item in instances.items() if key != "__base__"]
        if not base or not variants:
            continue
        deltas_from_base = [abs(item.weighted_score - base.weighted_score) for item in variants]
        stability = max(0.0, 100.0 - (sum(deltas_from_base) / len(deltas_from_base)))
        stability = round(stability, 4)
        stability_scores[mode].append(stability)
        stability_instances.append(
            {
                "base_scenario_id": base_id,
                "mode": mode,
                "variant_count": len(variants),
                "base_weighted_score": base.weighted_score,
                "stability_score": stability,
                "mean_abs_weighted_delta": round(sum(deltas_from_base) / len(deltas_from_base), 4),
            }
        )

    robustness = {
        "mode_stability_averages": {
            mode: round(sum(values) / len(values), 4)
            for mode, values in sorted(stability_scores.items())
            if values
        },
        "instances": stability_instances,
    }

    return {
        "mode_averages": mode_averages,
        "mode_triage_adjusted_averages": mode_triage_adjusted_averages,
        "family_aggregates": family_aggregates,
        "family_triage_adjusted_aggregates": family_triage_adjusted_aggregates,
        "triage_level_aggregates": triage_level_aggregates,
        "triage_level_adjusted_aggregates": triage_level_adjusted_aggregates,
        "doctrine_locus_aggregates": doctrine_locus_aggregates,
        "failure_counts": {mode: dict(counter.most_common()) for mode, counter in failure_counts.items()},
        "failure_counts_by_triage": {
            level: {mode: dict(counter.most_common()) for mode, counter in mode_counts.items()}
            for level, mode_counts in sorted(failure_counts_by_triage.items())
        },
        "delta_summary": dict(delta_summary),
        "delta_by_triage": {
            level: dict(values) for level, values in sorted(delta_by_triage.items())
        },
        "compare_mode_triage_split": compare_mode_triage_split,
        "robustness": robustness,
        "run_stats": {
            "total_expected_items": total_expected_items if total_expected_items is not None else len(evaluations),
            "completed_items": completed_items if completed_items is not None else len(evaluations),
            "failed_items": failed_items,
            "completion_rate": round(
                (
                    (completed_items if completed_items is not None else len(evaluations))
                    / total_expected_items
                ),
                4,
            )
            if total_expected_items
            else 1.0,
        },
    }
