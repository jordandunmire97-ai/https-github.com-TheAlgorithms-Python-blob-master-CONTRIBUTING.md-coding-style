from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from .engine import EnhancedIdealizationEngine
from .models import HistoryEntry, IdealizationRequest
from .reporting import render_json_report, render_text_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the enhanced idealization platform.")
    parser.add_argument("input_path", type=Path, help="Path to a JSON request file.")
    parser.add_argument(
        "--profile",
        help="Optional profile name to apply to the recommendation process.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format (default: text).",
    )
    parser.add_argument("--output", type=Path, help="Optional path for the rendered report.")
    parser.add_argument(
        "--history",
        type=Path,
        help="Optional prior JSON result to include in the comparison.",
    )
    parser.add_argument(
        "--save-result",
        type=Path,
        help="Optional path for saving the JSON result for a later comparison.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = json.loads(args.input_path.read_text(encoding="utf-8"))
    request = IdealizationRequest.from_dict(payload)
    if args.history:
        previous = json.loads(args.history.read_text(encoding="utf-8"))
        recommendations = previous.get("recommendations", [])
        if recommendations:
            previous_score = max(item["total_score"] for item in recommendations)
            request = replace(
                request,
                history=request.history
                + [HistoryEntry(label=args.history.name, score=previous_score)],
            )
    result = EnhancedIdealizationEngine().recommend(request, profile_name=args.profile)
    rendered = render_json_report(result) if args.format == "json" else render_text_report(result)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    if args.save_result:
        saved = rendered if args.format == "json" else render_json_report(result)
        args.save_result.write_text(saved + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
