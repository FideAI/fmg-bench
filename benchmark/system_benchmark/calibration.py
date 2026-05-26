"""Human calibration export/import helpers for the system benchmark."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .models import BenchmarkMode, ScenarioModeEvaluation
from .publication import publication_mode_name

HUMAN_SCORE_FIELDS = (
    "theological_pastoral_quality",
    "grounding_and_evidence",
    "preference_fidelity",
    "comparative_honesty",
    "escalation_appropriateness",
)

REVIEWER_METADATA_FIELDS = (
    "reviewer_id",
    "reviewer_role",
    "reviewer_tradition",
    "reviewer_confidence",
    "reviewer_notes",
)


def _parse_score(raw: str) -> float | None:
    """Parse a bounded human score, returning None for malformed cells."""
    try:
        return max(0.0, min(100.0, float(raw)))
    except ValueError:
        return None


def select_calibration_items(
    evaluations: list[ScenarioModeEvaluation],
    *,
    limit: int = 40,
    include_perturbations: bool = True,
) -> list[ScenarioModeEvaluation]:
    """Select a balanced calibration subset from completed evaluations."""
    grouped: dict[str, list[ScenarioModeEvaluation]] = defaultdict(list)
    for item in evaluations:
        if not include_perturbations and "__" in item.scenario_id:
            continue
        grouped[item.family].append(item)

    selected: list[ScenarioModeEvaluation] = []
    while len(selected) < limit and grouped:
        progressed = False
        for family in sorted(list(grouped)):
            bucket = grouped[family]
            if not bucket:
                grouped.pop(family)
                continue
            selected.append(bucket.pop(0))
            progressed = True
            if len(selected) >= limit:
                break
        if not progressed:
            break
    return selected


def export_human_review_csv(
    evaluations: list[ScenarioModeEvaluation],
    output_path: str | Path,
    *,
    limit: int = 40,
) -> Path:
    """Export scenario-mode judge scores into a CSV rubric for human review."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = select_calibration_items(evaluations, limit=limit)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "family",
                "mode",
                "publication_mode",
                "triage_level",
                "doctrine_loci",
                "tradition_scope",
                *REVIEWER_METADATA_FIELDS,
                "judge_weighted_score",
                "judge_triage_adjusted_score",
                *[f"judge_{field}" for field in HUMAN_SCORE_FIELDS],
                *[f"human_{field}" for field in HUMAN_SCORE_FIELDS],
                "human_failure_tags",
                "human_notes",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "scenario_id": item.scenario_id,
                    "family": item.family,
                    "mode": item.mode.value,
                    "publication_mode": publication_mode_name(item.mode),
                    "triage_level": item.triage_level.value,
                    "doctrine_loci": ";".join(item.doctrine_loci),
                    "tradition_scope": item.tradition_scope.value,
                    **{field: "" for field in REVIEWER_METADATA_FIELDS},
                    "judge_weighted_score": item.weighted_score,
                    "judge_triage_adjusted_score": item.triage_adjusted_score,
                    **{f"judge_{field}": item.scores[field] for field in HUMAN_SCORE_FIELDS},
                    **{f"human_{field}": "" for field in HUMAN_SCORE_FIELDS},
                    "human_failure_tags": "",
                    "human_notes": "",
                }
            )
    return path


def import_human_review_csv(path: str | Path) -> list[dict[str, Any]]:
    """Import completed human calibration rows from CSV."""
    rows: list[dict[str, Any]] = []
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            scores = {}
            for field in HUMAN_SCORE_FIELDS:
                raw = str(row.get(f"human_{field}", "")).strip()
                if raw:
                    score = _parse_score(raw)
                    if score is not None:
                        scores[field] = score
            if not scores:
                continue
            raw_mode = row.get("mode") or row.get("internal_mode") or ""
            try:
                mode = BenchmarkMode(raw_mode)
            except ValueError:
                continue
            rows.append(
                {
                    "scenario_id": row["scenario_id"],
                    "family": row["family"],
                    "mode": mode,
                    "triage_level": row.get("triage_level", ""),
                    "doctrine_loci": [
                        item.strip()
                        for item in str(row.get("doctrine_loci", "")).split(";")
                        if item.strip()
                    ],
                    "tradition_scope": row.get("tradition_scope", ""),
                    "human_scores": scores,
                    "human_failure_tags": [
                        tag.strip()
                        for tag in str(row.get("human_failure_tags", "")).split(",")
                        if tag.strip()
                    ],
                    "human_notes": row.get("human_notes", ""),
                    "reviewer_id": row.get("reviewer_id", ""),
                    "reviewer_role": row.get("reviewer_role", ""),
                    "reviewer_tradition": row.get("reviewer_tradition", ""),
                    "reviewer_confidence": row.get("reviewer_confidence", ""),
                    "reviewer_notes": row.get("reviewer_notes", ""),
                }
            )
    return rows


def import_human_review_csvs(paths: list[str | Path]) -> list[dict[str, Any]]:
    """Import completed human calibration rows from multiple reviewer CSVs."""
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(import_human_review_csv(path))
    return rows


def export_calibration_packet_csv(
    scenarios: list[Any],
    output_path: str | Path,
    *,
    calibration_ids: list[str] | None = None,
    modes: list[BenchmarkMode] | None = None,
) -> Path:
    """Export blank FMG-Bench reviewer packet rows without calling models."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    base_scenarios = [item for item in scenarios if getattr(item, "base_scenario_id", None) is None]
    if calibration_ids:
        wanted = set(calibration_ids)
        base_scenarios = [item for item in base_scenarios if item.id in wanted]
    selected_modes = modes or list(BenchmarkMode)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "title",
                "family",
                "internal_mode",
                "publication_mode",
                "triage_level",
                "doctrine_loci",
                "tradition_scope",
                "user_ask",
                "expected_behaviors",
                "disallowed_failure_modes",
                *REVIEWER_METADATA_FIELDS,
                *[f"human_{field}" for field in HUMAN_SCORE_FIELDS],
                "human_failure_tags",
                "human_notes",
            ],
        )
        writer.writeheader()
        for scenario in base_scenarios:
            for mode in selected_modes:
                writer.writerow(
                    {
                        "scenario_id": scenario.id,
                        "title": scenario.title,
                        "family": scenario.family.value,
                        "internal_mode": mode.value,
                        "publication_mode": publication_mode_name(mode),
                        "triage_level": scenario.triage_level.value,
                        "doctrine_loci": ";".join(scenario.doctrine_loci),
                        "tradition_scope": scenario.tradition_scope.value,
                        "user_ask": scenario.user_ask,
                        "expected_behaviors": " | ".join(scenario.expected_behaviors),
                        "disallowed_failure_modes": ",".join(
                            tag.value for tag in scenario.disallowed_failure_modes
                        ),
                        **{field: "" for field in REVIEWER_METADATA_FIELDS},
                        **{f"human_{field}": "" for field in HUMAN_SCORE_FIELDS},
                        "human_failure_tags": "",
                        "human_notes": "",
                    }
                )
    return path


def build_agreement_report(
    evaluations: list[ScenarioModeEvaluation],
    human_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare judge scores with imported human/expert scores."""
    index = {(item.scenario_id, item.mode): item for item in evaluations}
    comparisons: list[dict[str, Any]] = []
    deltas_by_field: dict[str, list[float]] = defaultdict(list)
    deltas_by_triage: dict[str, list[float]] = defaultdict(list)
    deltas_by_tradition_scope: dict[str, list[float]] = defaultdict(list)

    for row in human_rows:
        judge = index.get((row["scenario_id"], row["mode"]))
        if not judge:
            continue
        field_deltas = {}
        for field, human_score in row["human_scores"].items():
            delta = round(human_score - judge.scores[field], 4)
            field_deltas[field] = delta
            deltas_by_field[field].append(abs(delta))
            deltas_by_triage[row.get("triage_level") or judge.triage_level.value].append(abs(delta))
            deltas_by_tradition_scope[
                row.get("tradition_scope") or judge.tradition_scope.value
            ].append(abs(delta))
        comparisons.append(
            {
                "scenario_id": row["scenario_id"],
                "mode": row["mode"].value,
                "family": row["family"],
                "triage_level": row.get("triage_level") or judge.triage_level.value,
                "doctrine_loci": row.get("doctrine_loci") or judge.doctrine_loci,
                "tradition_scope": row.get("tradition_scope") or judge.tradition_scope.value,
                "judge_weighted_score": judge.weighted_score,
                "judge_triage_adjusted_score": judge.triage_adjusted_score,
                "human_scores": row["human_scores"],
                "score_deltas": field_deltas,
                "judge_failure_tags": [tag.value for tag in judge.failure_tags],
                "human_failure_tags": row["human_failure_tags"],
                "reviewer_id": row.get("reviewer_id", ""),
                "reviewer_role": row.get("reviewer_role", ""),
                "reviewer_tradition": row.get("reviewer_tradition", ""),
                "reviewer_confidence": row.get("reviewer_confidence", ""),
            }
        )

    return {
        "comparison_count": len(comparisons),
        "mean_absolute_delta_by_dimension": {
            field: round(mean(values), 4) for field, values in sorted(deltas_by_field.items())
        },
        "mean_absolute_delta_by_triage_level": {
            field: round(mean(values), 4) for field, values in sorted(deltas_by_triage.items())
        },
        "mean_absolute_delta_by_tradition_scope": {
            field: round(mean(values), 4)
            for field, values in sorted(deltas_by_tradition_scope.items())
        },
        "comparisons": comparisons,
        "limitations": (
            "This is an initial calibration check between model-judge outputs and human/expert "
            "rubric scores. It is not a final validation study."
        ),
    }


def write_agreement_report(report: dict[str, Any], output_path: str | Path) -> Path:
    """Persist an agreement report as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(report, handle, indent=2)
    return path
