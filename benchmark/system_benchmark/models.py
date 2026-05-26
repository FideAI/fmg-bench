"""Core types for the FMG-Bench."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ScenarioFamily(str, Enum):
    """Top-level scenario families for the system benchmark."""

    PREFERENCE_FIDELITY = "preference_fidelity"
    GROUNDING_AND_PROOF = "grounding_and_proof"
    COMPARATIVE_HONESTY = "comparative_honesty"
    EMBODIMENT_AND_ESCALATION = "embodiment_and_escalation"
    MULTI_TURN_PASTORAL = "multi_turn_pastoral"


class BenchmarkMode(str, Enum):
    """Response-generation modes compared by the benchmark."""

    RAW_MODEL = "raw_model"
    GUIDED_DEFAULT = "guided_default"
    PREFERENCE_CONFIGURED = "preference_configured"
    PERSPECTIVE_COMPARE = "perspective_compare"


class FailureTag(str, Enum):
    """Failure modes tracked separately from numeric scores."""

    IGNORES_USER_PREFERENCES = "ignores_user_preferences"
    FABRICATES_GROUNDING = "fabricates_grounding"
    OVERSTATES_CERTAINTY = "overstates_certainty"
    FLATTENS_DISAGREEMENT = "flattens_disagreement"
    UNSAFE_ESCALATION = "unsafe_escalation"
    MISSED_ESCALATION = "missed_escalation"
    DROPS_CONTEXT = "drops_context"
    UNHELPFUL_GENERICITY = "unhelpful_genericity"
    FABRICATED_SCRIPTURE = "fabricated_scripture"
    VERSE_CONTEXT_MISUSE = "verse_context_misuse"
    HALLUCINATED_THEOLOGY = "hallucinated_theology"
    HALLUCINATED_SOURCE_CLAIM = "hallucinated_source_claim"
    FALSE_PREMISE_ACCEPTANCE = "false_premise_acceptance"
    DENOMINATIONAL_OVERCLAIMING = "denominational_overclaiming"
    DENIES_CREEDAL_ORTHODOXY = "denies_creedal_orthodoxy"
    RELATIVIZES_PRIMARY_DOCTRINE = "relativizes_primary_doctrine"
    MISREPRESENTS_NAMED_TRADITION = "misrepresents_named_tradition"
    COLLAPSES_SECONDARY_DISAGREEMENT = "collapses_secondary_disagreement"
    OVERSTATES_TERTIARY_CERTAINTY = "overstates_tertiary_certainty"
    ANSWERS_FROM_WRONG_TRADITION = "answers_from_wrong_tradition"
    CONFUSES_DOCTRINE_AND_PASTORAL_APPLICATION = "confuses_doctrine_and_pastoral_application"


class TriageLevel(str, Enum):
    """Doctrinal severity layer used for adjusted benchmark interpretation."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    PASTORAL_APPLICATION = "pastoral_application"


class TraditionScope(str, Enum):
    """How broadly a scenario's theological claims are scoped."""

    CREEDAL = "creedal"
    TRADITION_SPECIFIC = "tradition_specific"
    COMPARATIVE = "comparative"
    PASTORAL = "pastoral"


class PerturbationFamily(str, Enum):
    """Robustness perturbation families for scenario variants."""

    PARAPHRASE = "paraphrase"
    POINT_OF_VIEW_SHIFT = "point_of_view_shift"
    SOCIAL_PRESSURE = "social_pressure"
    FALSE_PREMISE = "false_premise"
    PROMPT_TEMPLATE = "prompt_template"
    EMOTIONAL_INTENSITY = "emotional_intensity"


SCORE_DIMENSIONS = (
    "theological_pastoral_quality",
    "grounding_and_evidence",
    "preference_fidelity",
    "comparative_honesty",
    "escalation_appropriateness",
)


def model_slug(model_id: str) -> str:
    """Return a filesystem-safe model identifier for benchmark artifacts."""
    return model_id.replace("/", "_").replace(":", "_")


def normalize_call_result(result: Any) -> tuple[str, dict[str, Any]]:
    """Return response text plus metadata from string or rich model call records."""
    if isinstance(result, str):
        return result, {}
    if isinstance(result, dict):
        content = result.get("content")
        if isinstance(content, str):
            return content, {key: value for key, value in result.items() if key != "content"}
        raw_response = result.get("raw_response")
        if isinstance(raw_response, dict):
            choices = raw_response.get("choices") or []
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content")
                if isinstance(content, str):
                    return content, dict(result)
    raise TypeError(f"Unsupported LLM call result type: {type(result).__name__}")


@dataclass
class ConversationTurn:
    """A prior turn rendered into multi-turn benchmark prompts."""

    role: str
    content: str


@dataclass
class PerturbationVariant:
    """A robustness variant rendered as a separate benchmark instance."""

    id: str
    family: PerturbationFamily
    user_ask: str | None = None
    conversation_history: list[ConversationTurn] | None = None
    preference_context: dict[str, str] | None = None
    expected_behaviors: list[str] = field(default_factory=list)
    evaluator_notes: str = ""


@dataclass
class ScenarioWeights:
    """Scenario-specific score weights."""

    theological_pastoral_quality: float
    grounding_and_evidence: float
    preference_fidelity: float
    comparative_honesty: float
    escalation_appropriateness: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return asdict(self)

    def active_dimensions(self) -> list[str]:
        return [name for name, weight in self.as_dict().items() if weight > 0]

    def normalized(self) -> dict[str, float]:
        raw = self.as_dict()
        total = sum(value for value in raw.values() if value > 0)
        if total <= 0:
            raise ValueError("At least one scoring weight must be positive")
        return {name: value / total if value > 0 else 0.0 for name, value in raw.items()}


@dataclass
class SystemBenchmarkScenario:
    """One benchmark scenario."""

    id: str
    title: str
    family: ScenarioFamily
    user_ask: str
    triage_level: TriageLevel
    doctrine_loci: list[str]
    tradition_scope: TraditionScope
    base_scenario_id: str | None = None
    perturbation_id: str | None = None
    perturbation_family: PerturbationFamily | None = None
    conversation_history: list[ConversationTurn] = field(default_factory=list)
    preference_context: dict[str, str] = field(default_factory=dict)
    source_pack: list[str] = field(default_factory=list)
    expected_grounding_anchors: list[str] = field(default_factory=list)
    grounding_anchors: list[str] = field(default_factory=list)
    false_premise_traps: list[str] = field(default_factory=list)
    requires_escalation_check: bool = False
    weights: ScenarioWeights = field(
        default_factory=lambda: ScenarioWeights(0.35, 0.25, 0.15, 0.15, 0.10)
    )
    expected_behaviors: list[str] = field(default_factory=list)
    disallowed_failure_modes: list[FailureTag] = field(default_factory=list)
    perturbations: list[PerturbationVariant] = field(default_factory=list)
    evaluator_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["family"] = self.family.value
        payload["triage_level"] = self.triage_level.value
        payload["tradition_scope"] = self.tradition_scope.value
        payload["perturbation_family"] = (
            self.perturbation_family.value if self.perturbation_family else None
        )
        payload["conversation_history"] = [asdict(turn) for turn in self.conversation_history]
        payload["weights"] = self.weights.as_dict()
        payload["disallowed_failure_modes"] = [tag.value for tag in self.disallowed_failure_modes]
        payload["perturbations"] = [
            {
                **asdict(variant),
                "family": variant.family.value,
                "conversation_history": (
                    [asdict(turn) for turn in variant.conversation_history]
                    if variant.conversation_history is not None
                    else None
                ),
            }
            for variant in self.perturbations
        ]
        return payload


@dataclass
class EvaluationConfig:
    """Configuration for a system benchmark run."""

    model_id: str
    judge_model: str = "openai/gpt-5.4-mini"
    judge_models: list[str] = field(default_factory=list)
    scenarios_dir: str = "test_cases/system_benchmark/scenarios"
    output_dir: str = "results/system_benchmark"
    max_scenarios: int | None = None
    scenario_family: ScenarioFamily | None = None
    resume: bool = False
    save_raw_results: bool = True
    concurrency: int = 8
    judge_concurrency: int | None = None
    model_timeout_seconds: float = 180.0
    judge_timeout_seconds: float = 180.0
    max_retries: int = 2
    retry_backoff_seconds: float = 1.0
    fail_fast: bool = False
    rejudge: bool = False

    def resolved_judge_models(self) -> list[str]:
        if self.judge_models:
            return list(self.judge_models)
        return [self.judge_model]


@dataclass
class ModeResponse:
    """Prompt and response artifact for one scenario mode."""

    scenario_id: str
    family: str
    mode: BenchmarkMode
    prompt: str
    response: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        return payload


@dataclass
class JudgeRecord:
    """One judge model's verdict for a scenario-mode pair."""

    judge_model: str
    scores: dict[str, float]
    failure_tags: list[FailureTag]
    judge_summary: str
    raw_response: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failure_tags"] = [tag.value for tag in self.failure_tags]
        return payload


@dataclass
class ScenarioModeEvaluation:
    """Normalized evaluation for one scenario-mode pair."""

    scenario_id: str
    family: str
    mode: BenchmarkMode
    triage_level: TriageLevel
    doctrine_loci: list[str]
    tradition_scope: TraditionScope
    scores: dict[str, float]
    weighted_score: float
    triage_adjusted_score: float
    failure_tags: list[FailureTag]
    judge_summary: str
    judge_records: list[JudgeRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        payload["triage_level"] = self.triage_level.value
        payload["tradition_scope"] = self.tradition_scope.value
        payload["failure_tags"] = [tag.value for tag in self.failure_tags]
        payload["judge_records"] = [record.to_dict() for record in self.judge_records]
        return payload


@dataclass
class DeltaRecord:
    """Pairwise delta between benchmark modes."""

    scenario_id: str
    family: str
    triage_level: TriageLevel
    from_mode: BenchmarkMode
    to_mode: BenchmarkMode
    weighted_score_delta: float
    triage_adjusted_score_delta: float
    score_deltas: dict[str, float]
    new_failure_tags: list[FailureTag]
    removed_failure_tags: list[FailureTag]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["triage_level"] = self.triage_level.value
        payload["from_mode"] = self.from_mode.value
        payload["to_mode"] = self.to_mode.value
        payload["new_failure_tags"] = [tag.value for tag in self.new_failure_tags]
        payload["removed_failure_tags"] = [tag.value for tag in self.removed_failure_tags]
        return payload


@dataclass
class SystemBenchmarkRun:
    """Top-level benchmark run artifact."""

    model_id: str
    judge_model: str
    scenario_count: int
    responses: list[ModeResponse]
    evaluations: list[ScenarioModeEvaluation]
    deltas: list[DeltaRecord]
    summary: dict[str, Any]
    failed_items: list[dict[str, Any]] = field(default_factory=list)
