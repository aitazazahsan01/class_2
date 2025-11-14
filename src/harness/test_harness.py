"""
test_harness.py

A minimal software-in-the-loop (SIL) test harness. It compiles the firmware
under test (once) and, for each test case, spawns a *fresh* subprocess,
sends a scripted sequence of commands over stdin, and captures the response
lines from stdout -- exactly the shape of interaction a real HIL bench would
have over a serial link, just simulated locally so this runs anywhere
(including a free Colab/Kaggle CPU instance -- no GPU needed for this part).

A fresh subprocess per test case is deliberate: it guarantees no state leaks
between tests, which is what you want from a test harness (a failing test
should never be explained by "the previous test left it in a weird state").
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

FIRMWARE_DIR = Path(__file__).resolve().parents[2] / "firmware"
FIRMWARE_SRC = FIRMWARE_DIR / "thermostat_controller.c"
FIRMWARE_BIN = FIRMWARE_DIR / (
    "thermostat_controller.exe" if sys.platform == "win32" else "thermostat_controller"
)


@dataclass
class TestCase:
    name: str
    commands: list[str]
    expected_outputs: list[str]
    rationale: str = ""


@dataclass
class TestResult:
    name: str
    passed: bool
    actual_outputs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    error: str | None = None


def compile_firmware(force: bool = False) -> Path:
    """Compile the firmware under test if it isn't already built (or if forced)."""
    if FIRMWARE_BIN.exists() and not force:
        return FIRMWARE_BIN
    result = subprocess.run(
        ["gcc", "-O2", "-Wall", "-o", str(FIRMWARE_BIN), str(FIRMWARE_SRC)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Firmware failed to compile:\n{result.stderr}")
    return FIRMWARE_BIN


def run_test_case(test: TestCase, timeout: float = 5.0) -> TestResult:
    """Spawn a fresh firmware process, feed it the test's commands, and compare
    the captured output lines against what the test expects."""
    compile_firmware()
    input_text = "\n".join(test.commands + ["QUIT"]) + "\n"
    try:
        proc = subprocess.run(
            [str(FIRMWARE_BIN)],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return TestResult(
            name=test.name,
            passed=False,
            expected_outputs=test.expected_outputs,
            error="firmware process timed out (possible infinite loop or hang)",
        )

    actual_outputs = [line for line in proc.stdout.splitlines() if line]
    passed = actual_outputs == test.expected_outputs
    return TestResult(
        name=test.name,
        passed=passed,
        actual_outputs=actual_outputs,
        expected_outputs=test.expected_outputs,
        error=None if proc.returncode == 0 else f"firmware exited with code {proc.returncode}: {proc.stderr}",
    )


def run_suite(tests: list[TestCase]) -> list[TestResult]:
    return [run_test_case(t) for t in tests]


def print_results(results: list[TestResult]) -> None:
    passed = sum(1 for r in results if r.passed)
    print(f"\n{'='*60}\nTest results: {passed}/{len(results)} passed\n{'='*60}")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name}")
        if not r.passed:
            print(f"    expected: {r.expected_outputs}")
            print(f"    actual:   {r.actual_outputs}")
            if r.error:
                print(f"    error:    {r.error}")
