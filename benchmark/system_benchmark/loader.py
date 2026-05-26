"""Scenario loading and validation for the system benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from .models import (
    ConversationTurn,
    FailureTag,
    PerturbationFamily,
    PerturbationVariant,
    ScenarioFamily,
    ScenarioWeights,
    SystemBenchmarkScenario,
    TriageLevel,
    TraditionScope,
)
from .publication import (
    ScenarioSetManifest,
    load_scenario_set_manifest,
    validate_scenario_set_manifest,
)

REQUIRED_KEYS = {
    "id",
    "title",
    "family",
    "user_ask",
    "triage_level",
    "doctrine_loci",
    "tradition_scope",
    "weights",
    "expected_behaviors",
    "disallowed_failure_modes",
}


def _parse_turns(raw_turns: list[dict]) -> list[ConversationTurn]:
    turns: list[ConversationTurn] = []
    for turn in raw_turns:
        role = turn.get("role", "").strip()
        content = turn.get("content", "").strip()
        if not role or not content:
            raise ValueError("Conversation turns require non-empty role and content")
        turns.append(ConversationTurn(role=role, content=content))
    return turns


def _parse_perturbations(raw_variants: list[dict]) -> list[PerturbationVariant]:
    variants: list[PerturbationVariant] = []
    seen: set[str] = set()
    for raw in raw_variants:
        variant_id = str(raw.get("id", "")).strip()
        if not variant_id:
            raise ValueError("Perturbation variants require a non-empty id")
        if variant_id in seen:
            raise ValueError(f"Duplicate perturbation variant id: {variant_id}")
        seen.add(variant_id)
        variants.append(
            PerturbationVariant(
                id=variant_id,
                family=PerturbationFamily(raw["family"]),
                user_ask=str(raw["user_ask"]).strip() if raw.get("user_ask") else None,
                conversation_history=(
                    _parse_turns(raw["conversation_history"])
                    if "conversation_history" in raw
                    else None
                ),
                preference_context=(
                    {str(k): str(v) for k, v in raw["preference_context"].items()}
                    if "preference_context" in raw
                    else None
                ),
                expected_behaviors=[str(item) for item in raw.get("expected_behaviors", [])],
                evaluator_notes=str(raw.get("evaluator_notes", "")).strip(),
            )
        )
    return variants


def _parse_weights(raw_weights: dict) -> ScenarioWeights:
    expected = set(ScenarioWeights(0.35, 0.25, 0.15, 0.15, 0.10).as_dict())
    seen = set(raw_weights)
    missing = expected - seen
    if missing:
        raise ValueError(f"Missing score weights: {sorted(missing)}")
    weights = ScenarioWeights(**{key: float(value) for key, value in raw_weights.items()})
    weights.normalized()
    return weights


def _validate_scenario(raw: dict, source: Path) -> SystemBenchmarkScenario:
    missing = REQUIRED_KEYS - set(raw)
    if missing:
        raise ValueError(f"{source}: missing required keys {sorted(missing)}")

    scenario = SystemBenchmarkScenario(
        id=str(raw["id"]).strip(),
        title=str(raw["title"]).strip(),
        family=ScenarioFamily(raw["family"]),
        user_ask=str(raw["user_ask"]).strip(),
        triage_level=TriageLevel(raw["triage_level"]),
        doctrine_loci=[str(item).strip() for item in raw.get("doctrine_loci", [])],
        tradition_scope=TraditionScope(raw["tradition_scope"]),
        conversation_history=_parse_turns(raw.get("conversation_history", [])),
        preference_context={str(k): str(v) for k, v in raw.get("preference_context", {}).items()},
        source_pack=[str(item) for item in raw.get("source_pack", [])],
        expected_grounding_anchors=[str(item) for item in raw.get("expected_grounding_anchors", [])],
        grounding_anchors=[str(item) for item in raw.get("grounding_anchors", [])],
        false_premise_traps=[str(item) for item in raw.get("false_premise_traps", [])],
        requires_escalation_check=bool(raw.get("requires_escalation_check", False)),
        weights=_parse_weights(raw["weights"]),
        expected_behaviors=[str(item) for item in raw.get("expected_behaviors", [])],
        disallowed_failure_modes=[FailureTag(item) for item in raw.get("disallowed_failure_modes", [])],
        perturbations=_parse_perturbations(raw.get("perturbations", [])),
        evaluator_notes=str(raw.get("evaluator_notes", "")).strip(),
    )

    if not scenario.id or not scenario.title or not scenario.user_ask:
        raise ValueError(f"{source}: id, title, and user_ask must be non-empty")
    if not scenario.doctrine_loci or any(not item for item in scenario.doctrine_loci):
        raise ValueError(f"{source}: doctrine_loci must contain at least one non-empty locus")
    if scenario.requires_escalation_check and scenario.weights.escalation_appropriateness <= 0:
        raise ValueError(
            f"{source}: scenarios requiring escalation must assign positive escalation weight"
        )
    if not scenario.requires_escalation_check and scenario.weights.escalation_appropriateness != 0:
        raise ValueError(
            f"{source}: non-escalation scenarios must set escalation_appropriateness to 0"
        )
    return scenario


def _expand_perturbations(scenario: SystemBenchmarkScenario) -> list[SystemBenchmarkScenario]:
    expanded = [scenario]
    for variant in scenario.perturbations:
        expanded.append(
            SystemBenchmarkScenario(
                id=f"{scenario.id}__{variant.id}",
                title=f"{scenario.title} [{variant.family.value}]",
                family=scenario.family,
                user_ask=variant.user_ask or scenario.user_ask,
                triage_level=scenario.triage_level,
                doctrine_loci=scenario.doctrine_loci,
                tradition_scope=scenario.tradition_scope,
                base_scenario_id=scenario.id,
                perturbation_id=variant.id,
                perturbation_family=variant.family,
                conversation_history=(
                    variant.conversation_history
                    if variant.conversation_history is not None
                    else scenario.conversation_history
                ),
                preference_context=(
                    variant.preference_context
                    if variant.preference_context is not None
                    else scenario.preference_context
                ),
                source_pack=scenario.source_pack,
                expected_grounding_anchors=scenario.expected_grounding_anchors,
                grounding_anchors=scenario.grounding_anchors,
                false_premise_traps=scenario.false_premise_traps,
                requires_escalation_check=scenario.requires_escalation_check,
                weights=scenario.weights,
                expected_behaviors=[
                    *scenario.expected_behaviors,
                    *variant.expected_behaviors,
                    "Maintain materially consistent moral and pastoral guidance under this perturbation.",
                ],
                disallowed_failure_modes=scenario.disallowed_failure_modes,
                perturbations=[],
                evaluator_notes=" ".join(
                    item
                    for item in [scenario.evaluator_notes, variant.evaluator_notes]
                    if item
                ),
            )
        )
    return expanded


def _raw_scenario_records(root: Path) -> list[tuple[Path, dict]]:
    records: list[tuple[Path, dict]] = []
    for path in sorted(root.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        with path.open() as handle:
            records.append((path, json.load(handle)))
    for path in sorted(root.rglob("*.jsonl")):
        with path.open() as handle:
            for lineno, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                records.append((Path(f"{path}:{lineno}"), json.loads(line)))
    return records


def load_scenarios(scenarios_dir: str | Path) -> list[SystemBenchmarkScenario]:
    """Load all system benchmark scenarios from JSON or JSONL files."""
    root = Path(scenarios_dir)
    if not root.exists():
        raise FileNotFoundError(f"Scenario directory not found: {root}")

    scenarios: list[SystemBenchmarkScenario] = []
    ids: set[str] = set()
    for path, raw in _raw_scenario_records(root):
        scenario = _validate_scenario(raw, path)
        for instance in _expand_perturbations(scenario):
            if instance.id in ids:
                raise ValueError(f"Duplicate system benchmark scenario id: {instance.id}")
            ids.add(instance.id)
            scenarios.append(instance)
    return scenarios


def load_scenario_set(
    scenario_set_dir: str | Path,
    *,
    expected_base_count: int | None = None,
) -> tuple[list[SystemBenchmarkScenario], ScenarioSetManifest]:
    """Load scenarios and validate a publication scenario-set manifest."""
    root = Path(scenario_set_dir)
    manifest = load_scenario_set_manifest(root / "manifest.yaml")
    scenarios = load_scenarios(root)
    validate_scenario_set_manifest(
        manifest,
        scenarios,
        expected_base_count=expected_base_count,
    )
    return scenarios, manifest
