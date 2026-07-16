from __future__ import annotations

from statistics import mean, pstdev

from .models import (
    Candidate,
    CandidateBlueprint,
    Constraint,
    IdealizationRequest,
    IdealizationResult,
    Recommendation,
    Scenario,
    ScenarioAssessment,
    UserProfile,
    clamp,
)

DEFAULT_STRATEGIES: dict[str, dict[str, float]] = {
    "Balanced Horizon": {
        "feasibility": 0.08,
        "efficiency": 0.07,
        "goal_alignment": 0.08,
        "risk_resilience": 0.06,
        "adaptability": 0.06,
        "collaboration": 0.05,
    },
    "Bold Leap": {
        "innovation": 0.14,
        "goal_alignment": 0.08,
        "efficiency": 0.04,
        "risk_resilience": -0.07,
        "cost_efficiency": -0.06,
        "feasibility": -0.03,
    },
    "Resilient Core": {
        "risk_resilience": 0.14,
        "adaptability": 0.11,
        "feasibility": 0.06,
        "collaboration": 0.03,
        "innovation": -0.02,
    },
    "Lean Efficiency": {
        "cost_efficiency": 0.14,
        "efficiency": 0.12,
        "feasibility": 0.05,
        "collaboration": -0.02,
        "innovation": -0.03,
    },
    "Collaborative Orbit": {
        "collaboration": 0.15,
        "adaptability": 0.08,
        "goal_alignment": 0.06,
        "efficiency": 0.03,
        "cost_efficiency": -0.01,
    },
}


class EnhancedIdealizationEngine:
    def recommend(
        self, request: IdealizationRequest, profile_name: str | None = None
    ) -> IdealizationResult:
        profile = self._select_profile(request, profile_name)
        criteria_weights = self._adapt_weights(request, profile)
        candidates = self._build_candidates(request, profile)

        recommendations = []
        for candidate in candidates:
            base_score, constraint_status = self._score_candidate(
                candidate.metrics, request.constraints, criteria_weights
            )
            scenario_assessments = [
                self._simulate(candidate, scenario, request.constraints, criteria_weights)
                for scenario in request.scenarios
            ]
            scenario_score = (
                self._weighted_scenario_score(scenario_assessments, request.scenarios)
                if scenario_assessments
                else base_score
            )
            future_readiness = mean(
                candidate.metrics.get(metric, 0.0)
                for metric in ("adaptability", "innovation", "collaboration")
            )
            total_score = round(
                (base_score * 0.55) + (scenario_score * 0.35) + (future_readiness * 0.10), 4
            )
            confidence = self._compute_confidence(
                candidate.metrics, request.constraints, scenario_assessments, candidate
            )
            tradeoffs = self._build_tradeoffs(candidate.metrics)
            explanation = self._build_explanation(
                candidate.name,
                total_score,
                base_score,
                scenario_score,
                confidence,
                tradeoffs,
                constraint_status,
            )
            reasoning_trace = self._build_reasoning_trace(
                request, profile, candidate, constraint_status, scenario_assessments
            )
            recommendations.append(
                Recommendation(
                    rank=0,
                    candidate=candidate,
                    total_score=total_score,
                    base_score=base_score,
                    scenario_score=scenario_score,
                    confidence=confidence,
                    explanation=explanation,
                    tradeoffs=tradeoffs,
                    reasoning_trace=reasoning_trace,
                    scenario_assessments=scenario_assessments,
                    constraint_status=constraint_status,
                )
            )

        recommendations.sort(key=lambda item: (item.total_score, item.confidence), reverse=True)
        ranked = [
            Recommendation(
                rank=index + 1,
                candidate=item.candidate,
                total_score=item.total_score,
                base_score=item.base_score,
                scenario_score=item.scenario_score,
                confidence=item.confidence,
                explanation=item.explanation,
                tradeoffs=item.tradeoffs,
                reasoning_trace=item.reasoning_trace,
                scenario_assessments=item.scenario_assessments,
                constraint_status=item.constraint_status,
            )
            for index, item in enumerate(recommendations)
        ]
        return IdealizationResult(
            request_title=request.title,
            applied_profile=profile.name if profile else None,
            recommendations=ranked,
            comparison_notes=self._compare_with_history(request, ranked),
            criteria_weights=criteria_weights,
        )

    def _select_profile(
        self, request: IdealizationRequest, profile_name: str | None
    ) -> UserProfile | None:
        if profile_name is None:
            return request.profiles[0] if request.profiles else None
        for profile in request.profiles:
            if profile.name == profile_name:
                return profile
        raise ValueError(f"Unknown profile: {profile_name}")

    def _adapt_weights(
        self, request: IdealizationRequest, profile: UserProfile | None
    ) -> dict[str, float]:
        raw_weights: dict[str, float] = {}
        for criterion in request.criteria:
            weight = criterion.weight
            if profile:
                weight += profile.weight_adjustments.get(criterion.name, 0.0)
            if any(
                constraint.locked and constraint.metric == criterion.name
                for constraint in request.constraints
            ):
                weight += 0.15
            raw_weights[criterion.name] = max(weight, 0.01)

        total = sum(raw_weights.values()) or 1.0
        return {name: round(weight / total, 4) for name, weight in raw_weights.items()}

    def _build_candidates(
        self, request: IdealizationRequest, profile: UserProfile | None
    ) -> list[Candidate]:
        candidates: list[Candidate] = []

        if request.candidate_blueprints:
            for blueprint in request.candidate_blueprints:
                metrics = self._apply_profile_bias(dict(blueprint.metrics), profile)
                candidates.append(
                    Candidate(
                        name=blueprint.name,
                        description=blueprint.description,
                        metrics=metrics,
                        strategy="custom blueprint",
                        assumptions=blueprint.assumptions,
                        facts=blueprint.facts,
                        collaboration_notes=blueprint.collaboration_notes,
                    )
                )

        for strategy, deltas in DEFAULT_STRATEGIES.items():
            metrics = {key: value for key, value in request.baseline_metrics.items()}
            for metric, delta in deltas.items():
                metrics[metric] = clamp(metrics.get(metric, 0.5) + delta)
            metrics = self._apply_profile_bias(metrics, profile)
            assumptions = [
                "Baseline metrics realistically represent the current state.",
                "The chosen strategy can be executed without adding hidden constraints.",
            ]
            facts = [
                f"Generated from the '{strategy}' strategy pattern.",
                f"Objective focus: {request.objective}.",
            ]
            candidates.append(
                Candidate(
                    name=strategy,
                    description=f"{strategy} prioritizes a distinct path toward {request.success_definition}.",
                    metrics=metrics,
                    strategy="generated strategy",
                    assumptions=assumptions,
                    facts=facts,
                    collaboration_notes=list(request.collaboration_notes),
                )
            )

        deduplicated: dict[str, Candidate] = {}
        for candidate in candidates:
            deduplicated[candidate.name] = candidate
        return list(deduplicated.values())

    def _apply_profile_bias(
        self, metrics: dict[str, float], profile: UserProfile | None
    ) -> dict[str, float]:
        if profile is None:
            return {key: clamp(value) for key, value in metrics.items()}
        adjusted = dict(metrics)
        for metric, delta in profile.metric_bias.items():
            adjusted[metric] = clamp(adjusted.get(metric, 0.5) + delta)
        return {key: clamp(value) for key, value in adjusted.items()}

    def _score_candidate(
        self,
        metrics: dict[str, float],
        constraints: list[Constraint],
        criteria_weights: dict[str, float],
    ) -> tuple[float, list[str]]:
        base = sum(metrics.get(name, 0.0) * weight for name, weight in criteria_weights.items())
        status: list[str] = []
        penalty = 0.0
        for constraint in constraints:
            if constraint.is_satisfied(metrics):
                status.append(f"pass: {constraint.name}")
                continue
            severity = 0.35 if constraint.locked else 0.15
            penalty += severity
            status.append(f"fail: {constraint.name}")
        return round(clamp(base - penalty), 4), status

    def _simulate(
        self,
        candidate: Candidate,
        scenario: Scenario,
        constraints: list[Constraint],
        criteria_weights: dict[str, float],
    ) -> ScenarioAssessment:
        adjusted = dict(candidate.metrics)
        for metric, delta in scenario.metric_adjustments.items():
            adjusted[metric] = clamp(adjusted.get(metric, 0.5) + delta)
        score, status = self._score_candidate(adjusted, constraints, criteria_weights)
        failures = [item.replace("fail: ", "") for item in status if item.startswith("fail: ")]
        notes = [scenario.narrative] if scenario.narrative else []
        if failures:
            notes.append("Scenario exposes constraint pressure.")
        return ScenarioAssessment(
            scenario_name=scenario.name,
            score=score,
            adjusted_metrics=adjusted,
            notes=notes,
            constraint_failures=failures,
        )

    def _weighted_scenario_score(
        self, assessments: list[ScenarioAssessment], scenarios: list[Scenario]
    ) -> float:
        total_weight = sum(scenario.probability for scenario in scenarios) or 1.0
        weighted = 0.0
        for assessment, scenario in zip(assessments, scenarios, strict=True):
            weighted += assessment.score * scenario.probability
        return round(weighted / total_weight, 4)

    def _compute_confidence(
        self,
        metrics: dict[str, float],
        constraints: list[Constraint],
        assessments: list[ScenarioAssessment],
        candidate: Candidate,
    ) -> float:
        margins = [constraint.margin(metrics) for constraint in constraints] or [0.5]
        base = clamp(mean(clamp(margin, -1.0, 1.0) for margin in margins) / 1.5 + 0.5)
        scenario_scores = [assessment.score for assessment in assessments] or [0.5]
        stability = 1.0 - clamp(pstdev(scenario_scores) if len(scenario_scores) > 1 else 0.0)
        evidence_total = len(candidate.facts) + len(candidate.assumptions)
        evidence = (
            len(candidate.facts) / evidence_total if evidence_total else 0.5
        )
        confidence = (base * 0.4) + (stability * 0.4) + (evidence * 0.2)
        return round(clamp(confidence), 4)

    def _build_tradeoffs(self, metrics: dict[str, float]) -> list[str]:
        ordered = sorted(metrics.items(), key=lambda item: item[1], reverse=True)
        names = [name for name, _ in ordered]
        if not names:
            return [
                "Strength data is not available yet.",
                "Tradeoff data is not available yet.",
            ]
        strengths = names[:2] if len(names) > 1 else [names[0], names[0]]
        weaknesses = names[-2:] if len(names) > 1 else [names[0], names[0]]
        return [
            f"Strength concentrated in {strengths[0]} and {strengths[1]}.",
            f"Tradeoff pressure remains around {weaknesses[0]} and {weaknesses[1]}.",
        ]

    def _build_explanation(
        self,
        candidate_name: str,
        total_score: float,
        base_score: float,
        scenario_score: float,
        confidence: float,
        tradeoffs: list[str],
        constraint_status: list[str],
    ) -> str:
        constraint_summary = "all constraints satisfied" if all(
            item.startswith("pass:") for item in constraint_status
        ) else "some constraints require attention"
        return (
            f"{candidate_name} scores {total_score:.3f} overall "
            f"(base {base_score:.3f}, scenario {scenario_score:.3f}) with "
            f"{confidence:.3f} confidence; {constraint_summary}. {tradeoffs[0]} {tradeoffs[1]}"
        )

    def _build_reasoning_trace(
        self,
        request: IdealizationRequest,
        profile: UserProfile | None,
        candidate: Candidate,
        constraint_status: list[str],
        assessments: list[ScenarioAssessment],
    ) -> list[str]:
        stressed = [assessment.scenario_name for assessment in assessments if assessment.constraint_failures]
        trace = [
            f"Objective: {request.objective}",
            f"Success definition: {request.success_definition}",
            f"Candidate path: {candidate.name} ({candidate.strategy})",
            f"Profile applied: {profile.name if profile else 'none'}",
            f"Constraint status: {', '.join(constraint_status) if constraint_status else 'none'}",
        ]
        if stressed:
            trace.append(f"Stress scenarios: {', '.join(stressed)}")
        if candidate.collaboration_notes:
            trace.append(
                f"Collaboration inputs: {'; '.join(candidate.collaboration_notes)}"
            )
        return trace

    def _compare_with_history(
        self, request: IdealizationRequest, recommendations: list[Recommendation]
    ) -> list[str]:
        if not request.history or not recommendations:
            return []
        previous_best = max(entry.score for entry in request.history)
        current_best = recommendations[0].total_score
        delta = round(current_best - previous_best, 4)
        if delta >= 0:
            return [f"Current top recommendation improves on prior best by {delta:.3f} points."]
        return [f"Current top recommendation trails prior best by {abs(delta):.3f} points."]
