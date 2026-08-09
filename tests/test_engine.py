from __future__ import annotations

import unittest

from enhanced_idealization.engine import EnhancedIdealizationEngine
from enhanced_idealization.models import IdealizationRequest
from enhanced_idealization.reporting import render_json_report


def build_request() -> IdealizationRequest:
    return IdealizationRequest.from_dict(
        {
            "title": "Platform strategy",
            "domain": "product",
            "objective": "Recommend the best future-state platform direction.",
            "success_definition": "Produce explainable, resilient, and scalable options.",
            "baseline_metrics": {
                "feasibility": 0.65,
                "efficiency": 0.63,
                "goal_alignment": 0.69,
                "risk_resilience": 0.56,
                "adaptability": 0.61,
                "collaboration": 0.58,
                "cost_efficiency": 0.57,
                "innovation": 0.66,
            },
            "criteria": [
                {"name": "feasibility", "weight": 0.17},
                {"name": "efficiency", "weight": 0.15},
                {"name": "goal_alignment", "weight": 0.2},
                {"name": "risk_resilience", "weight": 0.16},
                {"name": "adaptability", "weight": 0.11},
                {"name": "collaboration", "weight": 0.08},
                {"name": "cost_efficiency", "weight": 0.07},
                {"name": "innovation", "weight": 0.06},
            ],
            "constraints": [
                {
                    "name": "minimum feasibility",
                    "metric": "feasibility",
                    "minimum": 0.55,
                    "locked": True,
                },
                {
                    "name": "minimum resilience",
                    "metric": "risk_resilience",
                    "minimum": 0.5,
                },
            ],
            "scenarios": [
                {
                    "name": "scale pressure",
                    "probability": 0.5,
                    "metric_adjustments": {
                        "adaptability": 0.06,
                        "efficiency": -0.03,
                        "collaboration": 0.04,
                    },
                },
                {
                    "name": "budget squeeze",
                    "probability": 0.5,
                    "metric_adjustments": {
                        "cost_efficiency": 0.08,
                        "feasibility": -0.04,
                        "innovation": -0.05,
                    },
                },
            ],
            "profiles": [
                {
                    "name": "enterprise",
                    "weight_adjustments": {"risk_resilience": 0.08, "collaboration": 0.03},
                    "metric_bias": {"risk_resilience": 0.05, "collaboration": 0.03},
                },
                {
                    "name": "innovation",
                    "weight_adjustments": {"innovation": 0.08, "adaptability": 0.03},
                    "metric_bias": {"innovation": 0.05, "adaptability": 0.04},
                },
            ],
            "candidate_blueprints": [
                {
                    "name": "Safety Mesh",
                    "description": "Resilient operating model for regulated growth.",
                    "metrics": {
                        "feasibility": 0.75,
                        "efficiency": 0.61,
                        "goal_alignment": 0.73,
                        "risk_resilience": 0.8,
                        "adaptability": 0.65,
                        "collaboration": 0.7,
                        "cost_efficiency": 0.55,
                        "innovation": 0.58,
                    },
                    "facts": ["Proven governance workflow."],
                    "assumptions": ["Regulated clients dominate adoption."],
                },
                {
                    "name": "Vision Sprint",
                    "description": "Higher upside model with more innovation leverage.",
                    "metrics": {
                        "feasibility": 0.58,
                        "efficiency": 0.64,
                        "goal_alignment": 0.72,
                        "risk_resilience": 0.51,
                        "adaptability": 0.75,
                        "collaboration": 0.57,
                        "cost_efficiency": 0.54,
                        "innovation": 0.84,
                    },
                    "facts": ["Strong prototype signal."],
                    "assumptions": ["Teams accept more delivery volatility."],
                },
            ],
            "history": [{"label": "previous state", "score": 0.67}],
        }
    )


class EnhancedIdealizationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = EnhancedIdealizationEngine()
        self.request = build_request()

    def test_returns_ranked_recommendations(self) -> None:
        result = self.engine.recommend(self.request, profile_name="enterprise")
        self.assertGreaterEqual(len(result.recommendations), 5)
        self.assertEqual(result.recommendations[0].rank, 1)
        self.assertGreaterEqual(
            result.recommendations[0].total_score, result.recommendations[-1].total_score
        )
        self.assertTrue(result.comparison_notes)

    def test_personalization_changes_recommendation_weights(self) -> None:
        enterprise_result = self.engine.recommend(self.request, profile_name="enterprise")
        innovation_result = self.engine.recommend(self.request, profile_name="innovation")
        self.assertNotEqual(
            enterprise_result.criteria_weights["innovation"],
            innovation_result.criteria_weights["innovation"],
        )
        enterprise_scores = {
            item.candidate.name: item.total_score for item in enterprise_result.recommendations
        }
        innovation_scores = {
            item.candidate.name: item.total_score for item in innovation_result.recommendations
        }
        self.assertGreater(
            innovation_scores["Vision Sprint"],
            enterprise_scores["Vision Sprint"],
        )

    def test_scenario_stress_testing_is_included(self) -> None:
        result = self.engine.recommend(self.request)
        top = result.recommendations[0]
        self.assertEqual(len(top.scenario_assessments), 2)
        self.assertTrue(any("Objective:" in item for item in top.reasoning_trace))

    def test_low_margin_candidates_reduce_confidence(self) -> None:
        result = self.engine.recommend(self.request, profile_name="enterprise")
        recommendation_by_name = {
            item.candidate.name: item for item in result.recommendations
        }
        self.assertLess(
            recommendation_by_name["Vision Sprint"].confidence,
            recommendation_by_name["Safety Mesh"].confidence,
        )

    def test_tradeoff_builder_handles_sparse_metrics(self) -> None:
        self.assertEqual(
            self.engine._build_tradeoffs({}),
            [
                "Strength data is not available yet.",
                "Tradeoff data is not available yet.",
            ],
        )
        self.assertEqual(
            self.engine._build_tradeoffs({"feasibility": 0.8}),
            [
                "Strength currently centers on feasibility.",
                "Tradeoff analysis needs additional metrics beyond feasibility.",
            ],
        )

    def test_minimize_criterion_prefers_lower_metric(self) -> None:
        request = IdealizationRequest.from_dict(
            {
                "title": "Cost choice",
                "domain": "finance",
                "objective": "Reduce operating cost.",
                "success_definition": "Lower cost is better.",
                "baseline_metrics": {"cost": 0.2},
                "criteria": [{"name": "cost", "weight": 1, "target": "minimize"}],
                "candidate_blueprints": [
                    {"name": "low", "description": "low", "metrics": {"cost": 0.1}},
                    {"name": "high", "description": "high", "metrics": {"cost": 0.8}},
                ],
            }
        )
        result = self.engine.recommend(request)
        self.assertEqual(result.recommendations[0].candidate.name, "low")

    def test_request_validation_rejects_invalid_shapes(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one criterion"):
            IdealizationRequest.from_dict(
                {
                    "title": "Invalid",
                    "domain": "test",
                    "objective": "test",
                    "success_definition": "test",
                }
            )
        with self.assertRaisesRegex(ValueError, "minimum or maximum"):
            IdealizationRequest.from_dict(
                {
                    "title": "Invalid",
                    "domain": "test",
                    "objective": "test",
                    "success_definition": "test",
                    "criteria": [{"name": "metric", "weight": 1}],
                    "constraints": [{"name": "empty", "metric": "metric"}],
                }
            )

    def test_json_report_is_serializable(self) -> None:
        report = render_json_report(self.engine.recommend(self.request))
        self.assertIn('"recommendations"', report)


if __name__ == "__main__":
    unittest.main()
