#!/usr/bin/env python3
"""Aggregate FMG-Bench runner outputs into publication-style CSV summaries."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

import yaml


MODES = ("raw_model", "guided_default", "preference_configured", "perspective_compare")
DIMENSIONS = (
    "theological_pastoral_quality",
    "grounding_and_evidence",
    "preference_fidelity",
    "comparative_honesty",
    "escalation_appropriateness",
)
TRIAGE_DESCRIPTIONS = {
    "primary": "Creedal and gospel-boundary faithfulness",
    "secondary": "Tradition-specific claims and honest disagreement",
    "tertiary": "Prudential questions and epistemic humility",
    "pastoral_application": "Safety referral and pastoral boundary judgment",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize *_latest_evaluations.json files from an FMG-Bench run."
    )
    parser.add_argument(
        "--input-dir",
        default="results/system_benchmark/fmg_bench_v1",
        help="Directory containing runner outputs.",
    )
    parser.add_argument(
        "--output-dir",
        default="results/reproduced",
        help="Directory for generated CSV summaries.",
    )
    parser.add_argument(
        "--model-config",
        default="benchmark/config/fmg_bench_v1.yaml",
        help="YAML config used to map model IDs to display names and providers.",
    )
    parser.add_argument(
        "--score-field",
        choices=["weighted_score", "triage_adjusted_score"],
        default="triage_adjusted_score",
        help="Score field to aggregate for model and triage summaries.",
    )
    return parser.parse_args()


def load_model_metadata(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text()) or {}
    metadata = {}
    for item in payload.get("models", []):
        model_id = item.get("model_name")
        if not model_id:
            continue
        display = str(item.get("openrouter_name") or model_id).split(": ", 1)[-1]
        metadata[str(model_id)] = {
            "display": display,
            "provider": str(item.get("provider_lab") or ""),
        }
    return metadata


def infer_model_id(path: Path, evaluations: list[dict]) -> str:
    if evaluations:
        metadata = evaluations[0].get("metadata", {})
        request = metadata.get("request", {})
        if request.get("model"):
            return str(request["model"])
    suffix = "_latest_evaluations.json"
    return path.name[: -len(suffix)] if path.name.endswith(suffix) else path.stem


def average(values: list[float]) -> float:
    return round(mean(values), 2) if values else 0.0


def read_evaluation_files(input_dir: Path) -> list[tuple[str, Path, list[dict]]]:
    paths = sorted(input_dir.glob("*_latest_evaluations.json"))
    if not paths:
        raise SystemExit(f"No *_latest_evaluations.json files found in {input_dir}")
    loaded = []
    for path in paths:
        evaluations = json.loads(path.read_text())
        loaded.append((infer_model_id(path, evaluations), path, evaluations))
    return loaded


def write_model_scores(
    rows: list[tuple[str, Path, list[dict]]],
    metadata: dict[str, dict[str, str]],
    output_path: Path,
    score_field: str,
) -> None:
    table = []
    for model_id, _path, evaluations in rows:
        by_mode = defaultdict(list)
        for item in evaluations:
            by_mode[item["mode"]].append(float(item[score_field]))
        mode_scores = {mode: average(by_mode[mode]) for mode in MODES}
        info = metadata.get(model_id, {})
        table.append(
            {
                "model": info.get("display", model_id),
                "provider": info.get("provider", ""),
                **{mode: f"{mode_scores[mode]:.2f}" for mode in MODES},
                "guided_minus_raw": f"{mode_scores['guided_default'] - mode_scores['raw_model']:.2f}",
                "compare_minus_preference": (
                    f"{mode_scores['perspective_compare'] - mode_scores['preference_configured']:.2f}"
                ),
            }
        )
    if table:
        mean_row = {
            "model": "Mean",
            "provider": "",
            **{
                mode: f"{mean([float(row[mode]) for row in table]):.2f}"
                for mode in MODES
            },
        }
        mean_row["guided_minus_raw"] = (
            f"{float(mean_row['guided_default']) - float(mean_row['raw_model']):.2f}"
        )
        mean_row["compare_minus_preference"] = (
            f"{float(mean_row['perspective_compare']) - float(mean_row['preference_configured']):.2f}"
        )
        table.append(mean_row)
    fieldnames = [
        "model",
        "provider",
        *MODES,
        "guided_minus_raw",
        "compare_minus_preference",
    ]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(table)


def write_triage_scores(
    rows: list[tuple[str, Path, list[dict]]],
    output_path: Path,
    score_field: str,
) -> None:
    by_triage = defaultdict(lambda: defaultdict(list))
    base_counts = defaultdict(set)
    for _model_id, _path, evaluations in rows:
        for item in evaluations:
            triage = item["triage_level"]
            mode = item["mode"]
            by_triage[triage][mode].append(float(item[score_field]))
            base_counts[triage].add(str(item["scenario_id"]).split("__", 1)[0])

    fieldnames = [
        "triage_level",
        "description",
        "base_scenarios",
        *MODES,
        "guided_minus_raw",
    ]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for triage in TRIAGE_DESCRIPTIONS:
            mode_scores = {mode: average(by_triage[triage][mode]) for mode in MODES}
            writer.writerow(
                {
                    "triage_level": triage,
                    "description": TRIAGE_DESCRIPTIONS[triage],
                    "base_scenarios": len(base_counts[triage]),
                    **{mode: f"{mode_scores[mode]:.2f}" for mode in MODES},
                    "guided_minus_raw": (
                        f"{mode_scores['guided_default'] - mode_scores['raw_model']:.2f}"
                    ),
                }
            )


def write_dimension_scores(rows: list[tuple[str, Path, list[dict]]], output_path: Path) -> None:
    by_dimension = defaultdict(lambda: defaultdict(list))
    for _model_id, _path, evaluations in rows:
        for item in evaluations:
            mode = item["mode"]
            scores = item.get("scores", {})
            for dimension in DIMENSIONS:
                value = scores.get(dimension)
                if value is not None:
                    by_dimension[dimension][mode].append(float(value))

    fieldnames = ["dimension", *MODES, "guided_minus_raw"]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for dimension in DIMENSIONS:
            mode_scores = {mode: average(by_dimension[dimension][mode]) for mode in MODES}
            writer.writerow(
                {
                    "dimension": dimension,
                    **{mode: f"{mode_scores[mode]:.2f}" for mode in MODES},
                    "guided_minus_raw": (
                        f"{mode_scores['guided_default'] - mode_scores['raw_model']:.2f}"
                    ),
                }
            )


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_evaluation_files(input_dir)
    metadata = load_model_metadata(Path(args.model_config))

    write_model_scores(rows, metadata, output_dir / "model_scores.csv", args.score_field)
    write_triage_scores(rows, output_dir / "triage_scores.csv", args.score_field)
    write_dimension_scores(rows, output_dir / "dimension_scores.csv")

    print(f"Read {len(rows)} model evaluation file(s) from {input_dir}")
    print(f"Wrote summaries to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
