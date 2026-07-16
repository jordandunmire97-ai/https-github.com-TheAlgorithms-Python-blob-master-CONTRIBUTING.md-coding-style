from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class Criterion:
    name: str
    weight: float
    target: str = "maximize"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Criterion":
        return Criterion(
            name=data["name"],
            weight=float(data.get("weight", 1.0)),
            target=data.get("target", "maximize"),
        )


@dataclass(frozen=True)
class Constraint:
    name: str
    metric: str
    minimum: float | None = None
    maximum: float | None = None
    locked: bool = False

    def is_satisfied(self, metrics: dict[str, float]) -> bool:
        value = metrics.get(self.metric, 0.0)
        if self.minimum is not None and value < self.minimum:
            return False
        if self.maximum is not None and value > self.maximum:
            return False
        return True

    def margin(self, metrics: dict[str, float]) -> float:
        value = metrics.get(self.metric, 0.0)
        lower_margin = value - self.minimum if self.minimum is not None else 1.0
        upper_margin = self.maximum - value if self.maximum is not None else 1.0
        return min(lower_margin, upper_margin)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Constraint":
        return Constraint(
            name=data["name"],
            metric=data["metric"],
            minimum=data.get("minimum"),
            maximum=data.get("maximum"),
            locked=bool(data.get("locked", False)),
        )


@dataclass(frozen=True)
class Scenario:
    name: str
    metric_adjustments: dict[str, float] = field(default_factory=dict)
    probability: float = 1.0
    narrative: str = ""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Scenario":
        return Scenario(
            name=data["name"],
            metric_adjustments={
                key: float(value) for key, value in data.get("metric_adjustments", {}).items()
            },
            probability=float(data.get("probability", 1.0)),
            narrative=data.get("narrative", ""),
        )


@dataclass(frozen=True)
class UserProfile:
    name: str
    weight_adjustments: dict[str, float] = field(default_factory=dict)
    metric_bias: dict[str, float] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "UserProfile":
        return UserProfile(
            name=data["name"],
            weight_adjustments={
                key: float(value) for key, value in data.get("weight_adjustments", {}).items()
            },
            metric_bias={key: float(value) for key, value in data.get("metric_bias", {}).items()},
        )


@dataclass(frozen=True)
class CandidateBlueprint:
    name: str
    description: str
    metrics: dict[str, float]
    assumptions: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    collaboration_notes: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CandidateBlueprint":
        return CandidateBlueprint(
            name=data["name"],
            description=data["description"],
            metrics={key: clamp(float(value)) for key, value in data.get("metrics", {}).items()},
            assumptions=list(data.get("assumptions", [])),
            facts=list(data.get("facts", [])),
            collaboration_notes=list(data.get("collaboration_notes", [])),
        )


@dataclass(frozen=True)
class HistoryEntry:
    label: str
    score: float
    summary: str = ""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "HistoryEntry":
        return HistoryEntry(
            label=data["label"],
            score=float(data["score"]),
            summary=data.get("summary", ""),
        )


@dataclass(frozen=True)
class IdealizationRequest:
    title: str
    domain: str
    objective: str
    success_definition: str
    baseline_metrics: dict[str, float]
    criteria: list[Criterion]
    constraints: list[Constraint]
    scenarios: list[Scenario]
    profiles: list[UserProfile] = field(default_factory=list)
    candidate_blueprints: list[CandidateBlueprint] = field(default_factory=list)
    collaboration_notes: list[str] = field(default_factory=list)
    history: list[HistoryEntry] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "IdealizationRequest":
        return IdealizationRequest(
            title=data["title"],
            domain=data["domain"],
            objective=data["objective"],
            success_definition=data["success_definition"],
            baseline_metrics={
                key: clamp(float(value)) for key, value in data.get("baseline_metrics", {}).items()
            },
            criteria=[Criterion.from_dict(item) for item in data.get("criteria", [])],
            constraints=[Constraint.from_dict(item) for item in data.get("constraints", [])],
            scenarios=[Scenario.from_dict(item) for item in data.get("scenarios", [])],
            profiles=[UserProfile.from_dict(item) for item in data.get("profiles", [])],
            candidate_blueprints=[
                CandidateBlueprint.from_dict(item) for item in data.get("candidate_blueprints", [])
            ],
            collaboration_notes=list(data.get("collaboration_notes", [])),
            history=[HistoryEntry.from_dict(item) for item in data.get("history", [])],
        )


@dataclass(frozen=True)
class Candidate:
    name: str
    description: str
    metrics: dict[str, float]
    strategy: str
    assumptions: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    collaboration_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScenarioAssessment:
    scenario_name: str
    score: float
    adjusted_metrics: dict[str, float]
    notes: list[str]
    constraint_failures: list[str]


@dataclass(frozen=True)
class Recommendation:
    rank: int
    candidate: Candidate
    total_score: float
    base_score: float
    scenario_score: float
    confidence: float
    explanation: str
    tradeoffs: list[str]
    reasoning_trace: list[str]
    scenario_assessments: list[ScenarioAssessment]
    constraint_status: list[str]


@dataclass(frozen=True)
class IdealizationResult:
    request_title: str
    applied_profile: str | None
    recommendations: list[Recommendation]
    comparison_notes: list[str]
    criteria_weights: dict[str, float]
