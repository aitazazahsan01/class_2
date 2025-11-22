#!/usr/bin/env python
"""Run just the human-authored baseline suite and print pass/fail."""
from baseline.human_written_tests import BASELINE_TESTS
from src.harness.test_harness import run_suite, print_results

if __name__ == "__main__":
    print_results(run_suite(BASELINE_TESTS))
