# LLM Test-Generation Agent for Embedded Firmware

**Research Domain:** Agentic AI for Embedded Software Testing, Source-Grounded Inspection, and Hardware-in-the-Loop (HIL) Validation

**Status:** Scaffold built, compiled, and verified end-to-end in mock mode. Real-agent mode is implemented and construction-tested against actual library dependencies, ready for execution with an API key. See [Status](#status--whats-actually-verified) for verification details.

## What this is

A research framework and LLM agent that reads embedded C firmware source and technical documentation, autonomously proposes hardware-in-the-loop (HIL) test suites, executes tests against the firmware, and compares findings against a human-written baseline suite — measuring not just pass rates, but whether the agent discovers safety-critical edge cases visible only in source code.

This directly addresses core research questions in AI-driven software engineering: *(1) what agent architecture and tool setups produce effective HIL test suites, and (2) how does LLM-generated test coverage compare to human-authored baselines on safety-critical firmware.* Everything here is built to produce measurable empirical numbers.

## The firmware under test

A simulated thermostat/safety-cutoff controller (`firmware/thermostat_controller.c`), standing in for a real target so the entire pipeline works without physical hardware or complex RTOS builds. It communicates via a line-based serial command protocol (`SET_TEMP`, `SET_TARGET`, `GET_STATE`, `RESET`, ...) simulating a HIL link.

It incorporates a safety-critical behavior: **shutdown latches**. Once the controller shuts down (temperature exceeding safety bounds), it does **not** automatically recover when the temperature returns to a safe range — only an explicit `RESET` command clears it. The datasheet (`firmware/datasheet.md`) notes that latching exists but directs the reader to consult the source code for exact behavior details. This design evaluates whether a test agent relying solely on documentation misses critical edge cases compared to one that actively inspects source code via dedicated tools (`src/compare.py`).

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Firmware under test | C, compiled with `gcc` | Lightweight, realistic, no hardware dependency; swappable for Zephyr/FreeRTOS/Arduino targets |
| Test execution | Python `subprocess`, fresh process per test | Simulates a HIL serial link; fresh process isolation prevents state leakage between tests |
| Agent framework | `langchain.agents.create_agent` (LangGraph 1.2.9) | Prebuilt agent API providing tool-calling and structured output with minimal boilerplate |
| LLM providers | Anthropic (`langchain-anthropic`) or OpenAI (`langchain-openai`) | Fully supported via configurable `--provider` flag |
| Structured output | Pydantic (`TestPlan` / `ProposedTestCase`) | Validated schema enforcing structured test output rather than unparsed text |
| Retrieval ("RAG grounded in documentation") | Keyword-overlap retrieval over `datasheet.md` | Lightweight baseline retrieval; upgradeable to vector embeddings for multi-document sets |
| Testing | `pytest` for harness sanity checks | Verifies firmware and harness reliability before evaluating agent-generated tests |

All components (except API-gated model calls) have been executed and verified in this environment — see [Status](#status--whats-actually-verified).

## Architecture

```
                    ┌─────────────────────┐
 datasheet.md ─────►│   read_docs tool    │──┐
                    └─────────────────────┘  │
                                              ▼
thermostat_controller.c ──────────────►┌───────────────┐      ┌──────────────┐      ┌──────────────┐
                    │   read_source tool  │──►│  LLM agent    │─────►│ TestPlan      │─────►│ HIL harness   │
                    └─────────────────────┘   │ (ReAct loop,  │      │ (Pydantic,    │      │ (subprocess,  │
                                               │  create_agent)│      │  structured)  │      │  per test)    │
                                               └───────────────┘      └──────────────┘      └───────┬──────┘
                                                                                                        │
                                                                           ┌────────────────────────────┘
                                                                           ▼
                                                             ┌─────────────────────────┐
 baseline/human_written_tests.py ────────────────────────► │  src/compare.py          │
                                                             │  (pass rate + category   │
                                                             │   coverage vs baseline)  │
                                                             └─────────────────────────┘
```

## Repo structure

```
firmware/
  thermostat_controller.c   the firmware under test
  datasheet.md               its documentation (deliberately incomplete on latching behavior)
src/
  harness/test_harness.py    compiles + runs firmware, scores test cases
  agent/tools.py              read_docs, read_source, list_firmware_files
  agent/mock_agent.py         deterministic mock agent for zero-API execution
  agent/real_agent.py         LLM agent (create_agent + tools + structured output)
  compare.py                  baseline vs candidate scoring and category coverage
baseline/
  human_written_tests.py      hand-authored reference suite (6 tests, including latching case)
tests/
  test_harness_sanity.py      pytest checks on harness and firmware behavior
configs/agent_config.yaml     provider and model configuration
run_baseline.py                entry point: baseline suite evaluation
run_agent.py                   entry point: mock or real agent + comparative report
```

## How to run

```bash
pip install -r requirements.txt

# 1. Sanity-check the harness and firmware (no API key required)
python -m pytest tests/ -v

# 2. Run the human-written baseline suite
python run_baseline.py

# 3. Run the full pipeline in mock mode (proves harness & tool integration end-to-end)
python run_agent.py --mock

# 4. Run with a live LLM provider (requires API key)
export ANTHROPIC_API_KEY=your-key-here      # or OPENAI_API_KEY
python run_agent.py --provider anthropic --model claude-sonnet-4-5-20250929
python run_agent.py --provider openai --model gpt-4o
```

## Status — what's actually verified

Everything listed below was executed and verified during development:

- ✅ Firmware **compiles cleanly** with `gcc -O2 -Wall` and behaves as designed, including the latching-shutdown edge case.
- ✅ The 6-test **human baseline suite passes 6/6** against the compiled firmware.
- ✅ All 6 **pytest harness sanity checks pass** (compile checks, boundary conditions, unknown command handling, and process isolation).
- ✅ **Agent tools** (`read_docs`, `read_source`, `list_firmware_files`) verified directly — `read_docs` surfaces relevant datasheet sections for fault-recovery queries.
- ✅ **Full pipeline runs end-to-end in mock mode** (`python run_agent.py --mock`):

  ```
  Baseline suite:  6/6 passed against firmware (100%)
  Mock_agent suite: 5/5 passed against firmware (100%)

  Behavior categories covered:
    [x] baseline   [x] mock_agent boundary_shutdown
    [x] baseline   [ ] mock_agent latching_fault_recovery
    [x] baseline   [x] mock_agent warning_zone
    [x] baseline   [x] mock_agent target_validation
    [x] baseline   [ ] mock_agent reset_behavior
    [x] baseline   [x] mock_agent normal_operation

  Mock_agent MISSED categories the baseline covered: ['latching_fault_recovery', 'reset_behavior']
  ```

  This demonstrates the core evaluation capability: a documentation-only testing approach (simulated by the mock agent) passes its own suite but **misses edge cases requiring source code inspection**.

- ✅ **Agent construction** (`create_agent(model, tools=[...], response_format=TestPlan)`) verified against installed packages (`langgraph`==1.2.9, `langchain`==1.3.14, `langchain-anthropic`).
- ⏳ **Live LLM invocation:** (`run_agent.py` without `--mock`) requires user API credentials.

## Research design

1. **Evaluate source-grounded agents:** Measure whether autonomous agents independently discover latching behavior via `read_source` compared to docs-only baselines.
2. **Architecture comparison:** Compare single ReAct agent loops against structured multi-stage flows (e.g., compulsory source inspection prior to test synthesis).
3. **Model benchmark:** Compare test generation quality and edge-case discovery across different foundation models using `configs/agent_config.yaml`.
4. **Empirical reporting:** Quantify pass rates and behavior category coverage metrics objectively across human and AI test suites.

## Project Summary

*"An end-to-end research benchmark and agent framework for evaluating LLM-driven Hardware-in-the-Loop (HIL) test generation against embedded firmware, featuring empirical coverage scoring against human-authored baselines."*
