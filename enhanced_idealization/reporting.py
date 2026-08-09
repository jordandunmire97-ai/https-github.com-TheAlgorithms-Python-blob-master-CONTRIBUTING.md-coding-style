from __future__ import annotations

import json
from dataclasses import asdict

from .models import IdealizationResult


def render_text_report(result: IdealizationResult) -> str:
    lines = [
        f"Enhanced Idealization Report: {result.request_title}",
        f"Applied profile: {result.applied_profile or 'none'}",
        "Adaptive criteria weights:",
    ]
    for name, weight in sorted(result.criteria_weights.items()):
        lines.append(f"  - {name}: {weight:.3f}")

    if result.comparison_notes:
        lines.append("Comparison:")
        lines.extend(f"  - {note}" for note in result.comparison_notes)

    lines.append("Recommendations:")
    for recommendation in result.recommendations:
        lines.append(
            f"{recommendation.rank}. {recommendation.candidate.name} "
            f"(score={recommendation.total_score:.3f}, confidence={recommendation.confidence:.3f})"
        )
        lines.append(f"   {recommendation.explanation}")
        lines.append("   Reasoning trace:")
        for item in recommendation.reasoning_trace:
            lines.append(f"   - {item}")
        lines.append("   Scenario assessments:")
        for assessment in recommendation.scenario_assessments:
            failures = ", ".join(assessment.constraint_failures) if assessment.constraint_failures else "none"
            lines.append(
                f"   - {assessment.scenario_name}: score={assessment.score:.3f}, "
                f"constraint_failures={failures}"
            )
    return "\n".join(lines)


def render_json_report(result: IdealizationResult) -> str:
    """Render a result as stable, machine-readable JSON."""
    return json.dumps(asdict(result), indent=2, sort_keys=True)
