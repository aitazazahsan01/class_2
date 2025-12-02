"""
mock_agent.py

A deterministic stand-in for the real LLM agent. It calls the exact same
tools (read_docs, read_source) the real agent will use, then proposes a
FIXED set of test cases meant to resemble what a "docs-only, surface-level"
test generator would produce -- i.e., it deliberately does NOT include the
one test that requires actually reading and reasoning about the firmware
source (the latching-shutdown behavior).

Why this exists: it lets you run and verify the ENTIRE pipeline --
tool calls, test proposal, harness execution, and comparison against the
human baseline -- with zero API cost and zero API key, before spending any
real LLM budget. It also gives you a concrete, worked example of exactly
the kind of coverage gap (docs-only vs. source-aware testing) the real
agent should ideally do better on. Run it with:  python run_agent.py --mock
"""

from __future__ import annotations

from src.agent.tools import read_docs, read_source
from src.harness.test_harness import TestCase


def propose_tests() -> list[TestCase]:
    # Exercise the real tools first, exactly like the real agent would --
    # this is what makes it a genuine pipeline smoke test, not just a
    # hardcoded fixture.
    _ = read_docs.invoke({"query": "safe operating range warning margin"})
    _ = read_docs.invoke({"query": "target setpoint validation"})
    # Note: a docs-only strategy stops here and never calls read_source --
    # that's the exact gap this mock is designed to demonstrate.

    return [
        TestCase(
            name="mock_temp_in_normal_range",
            commands=["SET_TEMP 20", "GET_STATE"],
            expected_outputs=["OK", "STATE NORMAL"],
            rationale="[mock, docs-only] Basic in-range sanity check.",
        ),
        TestCase(
            name="mock_lower_bound_exact_triggers_shutdown",
            commands=["SET_TEMP -40", "GET_STATE"],
            expected_outputs=["OK", "STATE SHUTDOWN"],
            rationale="[mock, docs-only] Datasheet says -40C is the lower "
                       "safety bound; testing the exact boundary value.",
        ),
        TestCase(
            name="mock_upper_bound_exact_triggers_shutdown",
            commands=["SET_TEMP 85", "GET_STATE"],
            expected_outputs=["OK", "STATE SHUTDOWN"],
            rationale="[mock, docs-only] Same idea at the upper bound.",
        ),
        TestCase(
            name="mock_reject_out_of_range_target",
            commands=["SET_TARGET -100", "GET_STATE"],
            expected_outputs=["ERROR invalid_target", "STATE NORMAL"],
            rationale="[mock, docs-only] Datasheet says out-of-range "
                       "setpoints must be rejected.",
        ),
        TestCase(
            name="mock_warning_zone_upper",
            commands=["SET_TEMP 82", "GET_STATE"],
            expected_outputs=["OK", "STATE WARNING"],
            rationale="[mock, docs-only] Within 5C of the upper bound "
                       "should be WARNING per the datasheet's margin.",
        ),
        # Deliberately absent: a test that sets temp into shutdown range,
        # then back to normal range, and checks whether STATE latches.
        # A docs-only strategy has no way to know to test this -- read_source
        # is required. Whether the REAL agent finds this on its own is the
        # single most interesting thing to look at once you run it for real.
    ]
