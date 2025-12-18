"""
compare.py

Compares a candidate test suite (agent-generated, mock or real) against the
human-written baseline suite -- both on correctness (do the tests actually
pass against the real firmware?) and on COVERAGE (did the candidate suite
independently discover the same categories of behavior the human tester
thought to check?).

Coverage is computed with a simple, transparent heuristic rather than exact
command-sequence matching (two suites will rarely phrase a test identically,
even when they're testing the same underlying behavior). This is intentionally
inspectable -- read `categorize()` and judge for yourself whether you'd
categorize things the same way; that's a more honest approach than a coverage
number you can't audit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.harness.test_harness import TestCase, TestResult, run_suite

CATEGORIES = [
    "boundary_shutdown",
    "latching_fault_recovery",
    "warning_zone",
    "target_validation",
    "reset_behavior",
    "normal_operation",
]


def categorize(test: TestCase) -> str:
    cmds = test.commands
    set_temps = [float(c.split()[1]) for c in cmds if c.startswith("SET_TEMP")]

    has_reset = any(c == "RESET" for c in cmds)
    has_bad_target = any(
        c.startswith("SET_TARGET") and (float(c.split()[1]) < -40 or float(c.split()[1]) > 85)
        for c in cmds
    )

    def is_boundary(t: float) -> bool:
        return t <= -40 or t >= 85

    def is_warning(t: float) -> bool:
        return (-40 < t <= -35) or (80 <= t < 85)

    # Latching/fault-recovery: goes into shutdown range, then back to a safe
    # range, WITHOUT a RESET in between -- and checks state afterward.
    if len(set_temps) >= 2:
        for i in range(len(set_temps) - 1):
            if is_boundary(set_temps[i]) and not is_boundary(set_temps[i + 1]):
                reset_between = False  # commands are interleaved; approximate: any RESET at all before the 2nd SET_TEMP after the boundary one
                return "latching_fault_recovery" if not (has_reset and _reset_before_recovery(cmds)) else "reset_behavior"

    if has_reset:
        return "reset_behavior"
    if has_bad_target:
        return "target_validation"
    if any(is_boundary(t) for t in set_temps):
        return "boundary_shutdown"
    if any(is_warning(t) for t in set_temps):
        return "warning_zone"
    return "normal_operation"


def _reset_before_recovery(cmds: list[str]) -> bool:
    """True if a RESET command appears anywhere between a boundary SET_TEMP
    and a later non-boundary SET_TEMP -- meaning it's testing the documented
    recovery path, not the latching behavior itself."""
    seen_boundary = False
    for c in cmds:
        if c.startswith("SET_TEMP"):
            t = float(c.split()[1])
            if t <= -40 or t >= 85:
                seen_boundary = True
        if c == "RESET" and seen_boundary:
            return True
    return False


@dataclass
class ComparisonReport:
    baseline_results: list[TestResult]
    candidate_results: list[TestResult]
    baseline_categories: set[str]
    candidate_categories: set[str]

    @property
    def baseline_pass_rate(self) -> float:
        return sum(r.passed for r in self.baseline_results) / len(self.baseline_results)

    @property
    def candidate_pass_rate(self) -> float:
        return sum(r.passed for r in self.candidate_results) / max(len(self.candidate_results), 1)

    @property
    def categories_missed_by_candidate(self) -> set[str]:
        return self.baseline_categories - self.candidate_categories

    @property
    def categories_found_by_candidate_only(self) -> set[str]:
        return self.candidate_categories - self.baseline_categories


def compare(baseline: list[TestCase], candidate: list[TestCase]) -> ComparisonReport:
    return ComparisonReport(
        baseline_results=run_suite(baseline),
        candidate_results=run_suite(candidate),
        baseline_categories={categorize(t) for t in baseline},
        candidate_categories={categorize(t) for t in candidate},
    )


def print_report(report: ComparisonReport, candidate_label: str = "candidate") -> None:
    print(f"\n{'#'*64}\nBASELINE vs {candidate_label.upper()}\n{'#'*64}")
    print(f"\nBaseline suite:  {sum(r.passed for r in report.baseline_results)}/"
          f"{len(report.baseline_results)} passed against firmware "
          f"({report.baseline_pass_rate:.0%})")
    print(f"{candidate_label.capitalize()} suite: "
          f"{sum(r.passed for r in report.candidate_results)}/"
          f"{len(report.candidate_results)} passed against firmware "
          f"({report.candidate_pass_rate:.0%})")

    print(f"\nBehavior categories covered:")
    for cat in CATEGORIES:
        in_base = "x" if cat in report.baseline_categories else " "
        in_cand = "x" if cat in report.candidate_categories else " "
        print(f"  [{in_base}] baseline   [{in_cand}] {candidate_label:<10} {cat}")

    if report.categories_missed_by_candidate:
        print(f"\n{candidate_label.capitalize()} MISSED categories the baseline covered: "
              f"{sorted(report.categories_missed_by_candidate)}")
    else:
        print(f"\n{candidate_label.capitalize()} covered every category the baseline did.")

    if report.categories_found_by_candidate_only:
        print(f"{candidate_label.capitalize()} found categories the baseline did NOT cover: "
              f"{sorted(report.categories_found_by_candidate_only)}")
