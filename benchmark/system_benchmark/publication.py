"""Publication-facing helpers for standalone benchmark packages."""

from __future__ import annotations

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
        "definition": "A bounded guided system layer emphasizing triage, grounding, user agency, and escalation.",
        "rationale": "Generalizes product-mediated default guidance without product branding.",
    },
    BenchmarkMode.PREFERENCE_CONFIGURED: {
        "definition": "Guided system behavior with explicit user or tradition preferences supplied as context.",
        "rationale": "Tests whether systems can honor declared preferences while preserving safety and epistemic limits.",
    },
    BenchmarkMode.PERSPECTIVE_COMPARE: {
        "definition": "Preference-aware behavior that also surfaces meaningful faithful disagreement.",
        "rationale": "Tests whether systems can compare perspectives without flattening disagreement or overstating consensus.",
    },
}


@dataclass(frozen=True)
class ScenarioSetManifest:
    """Validated publication scenario-set manifest."""

    version: str
    scenario_ids: list[str]
    public_sample_ids: list[str]
    held_out_ids: list[str]
    calibration_candidate_ids: list[str]
    triage_coverage: dict[str, int]
    doctrine_locus_coverage: dict[str, int]
    tradition_coverage: dict[str, int]
    publication_terminology_aliases: dict[str, str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScenarioSetManifest":
        required = {
            "version",
            "scenario_ids",
            "public_sample_ids",
            "held_out_ids",
            "calibration_candidate_ids",
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
            scenario_ids=[str(item) for item in payload["scenario_ids"]],
            public_sample_ids=[str(item) for item in payload["public_sample_ids"]],
            held_out_ids=[str(item) for item in payload["held_out_ids"]],
            calibration_candidate_ids=[str(item) for item in payload["calibration_candidate_ids"]],
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
    """Load and validate a scenario-set manifest YAML file."""
    manifest_path = Path(path)
    with manifest_path.open() as handle:
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
    manifest_ids = set(manifest.scenario_ids)

    if expected_base_count is not None and len(base_scenarios) != expected_base_count:
        raise ValueError(
            f"Expected {expected_base_count} base scenarios, found {len(base_scenarios)}"
        )
    if base_ids != manifest_ids:
        missing = sorted(base_ids - manifest_ids)
        extra = sorted(manifest_ids - base_ids)
        raise ValueError(f"Manifest scenario ids mismatch; missing={missing}, extra={extra}")

    for split_name, ids in {
        "public_sample_ids": manifest.public_sample_ids,
        "held_out_ids": manifest.held_out_ids,
        "calibration_candidate_ids": manifest.calibration_candidate_ids,
    }.items():
        unknown = sorted(set(ids) - base_ids)
        if unknown:
            raise ValueError(f"{split_name} contains unknown scenario ids: {unknown}")

    public = set(manifest.public_sample_ids)
    held_out = set(manifest.held_out_ids)
    if public & held_out:
        raise ValueError("public_sample_ids and held_out_ids must be disjoint")

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
