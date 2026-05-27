"""Publication-facing helpers for standalone benchmark packages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .models import BenchmarkMode, SystemBenchmarkScenario

PUBLICATION_MODE_ALIASES: dict[BenchmarkMode, str] = {
    BenchmarkMode.RAW_MODEL: "raw_model",
    BenchmarkMode.GUIDED_DEFAULT: "guided_default",
    BenchmarkMode.PREFERENCE_CONFIGURED: "preference_configured",
    BenchmarkMode.PERSPECTIVE_COMPARE: "perspective_compare",
}

PUBLICATION_MODE_DEFINITIONS: dict[BenchmarkMode, dict[str, str]] = {
    BenchmarkMode.RAW_MODEL: {
        "definition": "Generic model behavior without benchmark-provided guidance layers.",
        "rationale": "Baseline condition for measuring native model behavior.",
    },
    BenchmarkMode.GUIDED_DEFAULT: {
        "definition": "Structured harness emphasizing triage, grounding, user agency, and escalation.",
        "rationale": "Tests whether a structured harness improves behavior without product branding.",
    },
    BenchmarkMode.PREFERENCE_CONFIGURED: {
        "definition": "Structured-harness behavior with explicit user or tradition preferences supplied as context.",
        "rationale": "Tests whether systems can honor declared preferences while preserving safety and epistemic limits.",
    },
    BenchmarkMode.PERSPECTIVE_COMPARE: {
        "definition": "Preference-aware structured-harness behavior that also surfaces meaningful faithful disagreement.",
        "rationale": "Tests whether systems can compare perspectives without flattening disagreement or overstating consensus.",
    },
}


@dataclass(frozen=True)
class ScenarioSetManifest:
    """Validated publication scenario-set manifest."""

    version: str
    total_scenarios: int
    open_benchmark_count: int
    example_sample_count: int
    perturbation_variant_count: int
    rendered_instance_count: int
    calibration_candidate_ids: list[str]
    triage_coverage: dict[str, int]
    doctrine_locus_coverage: dict[str, int]
    tradition_coverage: dict[str, int]
    publication_terminology_aliases: dict[str, str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScenarioSetManifest":
        required = {
            "version",
            "total_scenarios",
            "open_benchmark_count",
            "example_sample_count",
            "perturbation_variant_count",
            "rendered_instance_count",
            "triage_coverage",
            "doctrine_locus_coverage",
            "tradition_coverage",
            "publication_terminology_aliases",
        }
        missing = required - set(payload)
        if missing:
            raise ValueError(f"Scenario-set manifest missing keys: {sorted(missing)}")
        return cls(
            version=str(payload["version"]),
            total_scenarios=int(payload["total_scenarios"]),
            open_benchmark_count=int(payload["open_benchmark_count"]),
            example_sample_count=int(payload["example_sample_count"]),
            perturbation_variant_count=int(payload["perturbation_variant_count"]),
            rendered_instance_count=int(payload["rendered_instance_count"]),
            calibration_candidate_ids=[
                str(item) for item in payload.get("calibration_candidate_ids", [])
            ],
            triage_coverage={str(k): int(v) for k, v in payload["triage_coverage"].items()},
            doctrine_locus_coverage={
                str(k): int(v) for k, v in payload["doctrine_locus_coverage"].items()
            },
            tradition_coverage={str(k): int(v) for k, v in payload["tradition_coverage"].items()},
            publication_terminology_aliases={
                str(k): str(v) for k, v in payload["publication_terminology_aliases"].items()
            },
        )


def publication_mode_name(mode: BenchmarkMode | str) -> str:
    """Return the neutral publication label for a benchmark mode."""
    parsed = mode if isinstance(mode, BenchmarkMode) else BenchmarkMode(mode)
    return PUBLICATION_MODE_ALIASES[parsed]


def terminology_mapping_rows() -> list[dict[str, str]]:
    """Return rows for terminology mapping tables."""
    rows: list[dict[str, str]] = []
    for mode in BenchmarkMode:
        detail = PUBLICATION_MODE_DEFINITIONS[mode]
        rows.append(
            {
                "internal_mode_name": mode.value,
                "publication_mode_name": publication_mode_name(mode),
                "definition": detail["definition"],
                "rationale": detail["rationale"],
            }
        )
    return rows


def load_scenario_set_manifest(path: str | Path) -> ScenarioSetManifest:
    """Load and validate a scenario-set manifest JSON or YAML file."""
    manifest_path = Path(path)
    with manifest_path.open() as handle:
        if manifest_path.suffix == ".json":
            payload = json.load(handle)
        else:
            payload = yaml.safe_load(handle) or {}
    return ScenarioSetManifest.from_dict(payload)


def validate_scenario_set_manifest(
    manifest: ScenarioSetManifest,
    scenarios: list[SystemBenchmarkScenario],
    *,
    expected_base_count: int | None = None,
) -> None:
    """Validate manifest ids and coverage against loaded base scenarios."""
    base_scenarios = [item for item in scenarios if item.base_scenario_id is None]
    base_ids = {item.id for item in base_scenarios}
    perturbation_count = len(scenarios) - len(base_scenarios)

    if expected_base_count is not None and len(base_scenarios) != expected_base_count:
        raise ValueError(
            f"Expected {expected_base_count} base scenarios, found {len(base_scenarios)}"
        )
    if len(base_scenarios) != manifest.total_scenarios:
        raise ValueError(
            f"Manifest total_scenarios mismatch; expected {len(base_scenarios)}, got {manifest.total_scenarios}"
        )
    if len(base_scenarios) != manifest.open_benchmark_count:
        raise ValueError(
            "Manifest open_benchmark_count must match loaded base scenarios; "
            f"expected {len(base_scenarios)}, got {manifest.open_benchmark_count}"
        )
    if perturbation_count != manifest.perturbation_variant_count:
        raise ValueError(
            "Manifest perturbation_variant_count mismatch; "
            f"expected {perturbation_count}, got {manifest.perturbation_variant_count}"
        )
    if len(scenarios) != manifest.rendered_instance_count:
        raise ValueError(
            "Manifest rendered_instance_count mismatch; "
            f"expected {len(scenarios)}, got {manifest.rendered_instance_count}"
        )

    unknown_calibration = sorted(set(manifest.calibration_candidate_ids) - base_ids)
    if unknown_calibration:
        raise ValueError(
            f"calibration_candidate_ids contains unknown scenario ids: {unknown_calibration}"
        )

    triage_counts: dict[str, int] = {}
    tradition_counts: dict[str, int] = {}
    doctrine_counts: dict[str, int] = {}
    for scenario in base_scenarios:
        triage_counts[scenario.triage_level.value] = triage_counts.get(scenario.triage_level.value, 0) + 1
        tradition_counts[scenario.tradition_scope.value] = (
            tradition_counts.get(scenario.tradition_scope.value, 0) + 1
        )
        for locus in scenario.doctrine_loci:
            doctrine_counts[locus] = doctrine_counts.get(locus, 0) + 1

    if triage_counts != manifest.triage_coverage:
        raise ValueError(
            f"Manifest triage coverage mismatch; expected {triage_counts}, got {manifest.triage_coverage}"
        )
    for locus, count in manifest.doctrine_locus_coverage.items():
        if doctrine_counts.get(locus) != count:
            raise ValueError(
                f"Manifest doctrine coverage mismatch for {locus}: expected {doctrine_counts.get(locus)}, got {count}"
            )
    for scope, count in manifest.tradition_coverage.items():
        if tradition_counts.get(scope) != count:
            raise ValueError(
                f"Manifest tradition coverage mismatch for {scope}: expected {tradition_counts.get(scope)}, got {count}"
            )
