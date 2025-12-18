#!/usr/bin/env python
"""
Entry point: generate a HIL test suite (mock or real LLM agent), run it
against the firmware, and compare it to the human-authored baseline.

Usage:
    python run_agent.py --mock                       # no API key needed
    python run_agent.py --provider anthropic --model claude-sonnet-4-5-20250929
    python run_agent.py --provider openai --model gpt-4o
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from baseline.human_written_tests import BASELINE_TESTS
from src.compare import compare, print_report

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Use the deterministic mock agent (no API key needed).")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openai"])
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929")
    args = parser.parse_args()

    if args.mock:
        from src.agent.mock_agent import propose_tests
        candidate_tests = propose_tests()
        label = "mock_agent"
    else:
        from src.agent.real_agent import propose_tests, _check_api_key
        _check_api_key(args.provider)
        candidate_tests = propose_tests(provider=args.provider, model_name=args.model)
        label = f"{args.provider}_{args.model}"

    report = compare(BASELINE_TESTS, candidate_tests)
    print_report(report, candidate_label=label)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"{label}_run.json"
    out_path.write_text(
        json.dumps(
            {
                "candidate_label": label,
                "candidate_tests": [t.__dict__ for t in candidate_tests],
                "baseline_pass_rate": report.baseline_pass_rate,
                "candidate_pass_rate": report.candidate_pass_rate,
                "baseline_categories": sorted(report.baseline_categories),
                "candidate_categories": sorted(report.candidate_categories),
                "categories_missed_by_candidate": sorted(report.categories_missed_by_candidate),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSaved run to {out_path}")


if __name__ == "__main__":
    main()
