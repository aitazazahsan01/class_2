"""
human_written_tests.py

The human-authored baseline test suite for the thermostat controller.
This is written BEFORE looking at anything the agent produces -- it is the
"what would a careful engineer test, given the datasheet and the source"
reference point that the agent-generated suite gets compared against later
(see src/compare.py).

Deliberately includes one test (test 4) that only a careful reading of the
firmware SOURCE -- not just the datasheet -- would catch: the latching
shutdown behavior. Whether the agent's own generated suite discovers this
on its own is one of the most interesting things this whole project measures.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.harness.test_harness import TestCase, run_suite, print_results  # noqa: E402


BASELINE_TESTS: list[TestCase] = [
    TestCase(
        name="normal_operation_heater_engages_below_setpoint",
        commands=["SET_TEMP 20", "GET_STATE", "GET_HEATER", "GET_COOLER"],
        expected_outputs=["OK", "STATE NORMAL", "HEATER ON", "COOLER OFF"],
        rationale="Sanity check: mid-range temperature below the default "
                   "setpoint (with hysteresis) should be NORMAL with the "
                   "heater on and cooler off.",
    ),
    TestCase(
        name="lower_boundary_triggers_shutdown_and_forces_actuators_off",
        commands=["SET_TEMP -50", "GET_STATE", "GET_HEATER", "GET_COOLER"],
        expected_outputs=["OK", "STATE SHUTDOWN", "HEATER OFF", "COOLER OFF"],
        rationale="Datasheet-driven: readings at/beyond -40C must shut down "
                   "and force both actuators off as a safety measure.",
    ),
    TestCase(
        name="warning_zone_near_lower_bound",
        commands=["SET_TEMP -37", "GET_STATE", "GET_HEATER"],
        expected_outputs=["OK", "STATE WARNING", "HEATER ON"],
        rationale="Datasheet-driven: within 5C of a safety bound should be "
                   "WARNING, not NORMAL or SHUTDOWN -- and actuators should "
                   "still function normally in WARNING (only SHUTDOWN forces "
                   "them off).",
    ),
    TestCase(
        name="shutdown_is_latched_not_self_clearing",
        commands=["SET_TEMP -50", "SET_TEMP 20", "GET_STATE"],
        expected_outputs=["OK", "OK", "STATE SHUTDOWN"],
        rationale="SOURCE-driven, not in the datasheet: once shut down, "
                   "returning to a safe temperature reading should NOT "
                   "automatically clear the fault -- only RESET should. "
                   "The datasheet only says 'consult the source' for this.",
    ),
    TestCase(
        name="out_of_range_target_setpoint_is_rejected",
        commands=["SET_TARGET 200", "GET_STATE"],
        expected_outputs=["ERROR invalid_target", "STATE NORMAL"],
        rationale="Datasheet-driven: setpoints outside the safe range must "
                   "be rejected, not silently clamped or accepted.",
    ),
    TestCase(
        name="reset_clears_a_latched_shutdown",
        commands=["SET_TEMP -50", "RESET", "SET_TEMP 20", "GET_STATE"],
        expected_outputs=["OK", "OK", "OK", "STATE NORMAL"],
        rationale="Confirms RESET is actually the documented way out of a "
                   "latched fault, completing the pair with test 4.",
    ),
]


if __name__ == "__main__":
    results = run_suite(BASELINE_TESTS)
    print_results(results)
