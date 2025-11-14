"""
Sanity tests for the harness and firmware itself -- run these BEFORE trusting
any agent output. If these fail, nothing downstream (baseline or agent
comparison) is meaningful.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.harness.test_harness import TestCase, compile_firmware, run_test_case  # noqa: E402


def test_firmware_compiles():
    binary = compile_firmware(force=True)
    assert binary.exists()


def test_default_state_is_normal():
    result = run_test_case(TestCase("default_state", ["GET_STATE"], ["STATE NORMAL"]))
    assert result.passed, result.actual_outputs


def test_lower_boundary_is_inclusive():
    result = run_test_case(TestCase("lower_inclusive", ["SET_TEMP -40", "GET_STATE"], ["OK", "STATE SHUTDOWN"]))
    assert result.passed, result.actual_outputs


def test_just_above_lower_boundary_is_warning_not_shutdown():
    result = run_test_case(TestCase("just_above", ["SET_TEMP -39.9", "GET_STATE"], ["OK", "STATE WARNING"]))
    assert result.passed, result.actual_outputs


def test_unknown_command_returns_error():
    result = run_test_case(TestCase("unknown_cmd", ["FOO_BAR"], ["ERROR unknown_command"]))
    assert result.passed, result.actual_outputs


def test_fresh_process_per_test_has_no_state_leakage():
    # Run a shutdown-inducing test, then a completely independent test --
    # if state leaked between subprocess runs, this second test would fail.
    run_test_case(TestCase("induce_shutdown", ["SET_TEMP -50"], ["OK"]))
    result = run_test_case(TestCase("should_be_fresh", ["GET_STATE"], ["STATE NORMAL"]))
    assert result.passed, result.actual_outputs
