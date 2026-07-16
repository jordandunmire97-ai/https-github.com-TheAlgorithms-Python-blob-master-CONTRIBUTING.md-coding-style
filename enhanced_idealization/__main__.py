from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import EnhancedIdealizationEngine
from .models import IdealizationRequest
from .reporting import render_text_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the enhanced idealization platform.")
    parser.add_argument("input_path", type=Path, help="Path to a JSON request file.")
    parser.add_argument(
        "--profile",
        help="Optional profile name to apply to the recommendation process.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = json.loads(args.input_path.read_text(encoding="utf-8"))
    request = IdealizationRequest.from_dict(payload)
    result = EnhancedIdealizationEngine().recommend(request, profile_name=args.profile)
    print(render_text_report(result))


if __name__ == "__main__":
    main()
