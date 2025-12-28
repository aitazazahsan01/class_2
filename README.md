# LLM Test-Generation Agent for Embedded Firmware

**Target application:** Mitacs posting 51907, *Agentic AI for Embedded Software Testing and Hardware-in-the-Loop Validation* (Algoma University, Md Al Maruf)

**Status:** scaffold built, compiled, and verified end-to-end in mock mode. Real-agent mode is implemented and construction-tested against the actual library versions below, but needs your own API key to run for real. See [Status](#status--whats-actually-verified) for exactly what that means.

## What this is

A small agent that reads embedded C firmware source and its documentation, proposes a hardware-in-the-loop (HIL) test suite, executes those tests against the firmware, and compares what it found against a human-written baseline suite — measuring not just "did the tests pass" but "did the agent discover the same categories of important behavior a careful engineer would test for."

This directly mirrors the posting's own research questions: *(1) what agent architecture/prompting produces effective HIL test suites, and (2) how does agent coverage compare to human-authored baselines.* Everything here is built to make both questions answerable with real numbers, not vibes.

## The firmware under test

A small (~150 line) simulated thermostat/safety-cutoff controller (`firmware/thermostat_controller.c`), standing in for a real target so the whole pipeline works without needing actual hardware or a real Zephyr/FreeRTOS project to start. It talks over a line-based command protocol (`SET_TEMP`, `SET_TARGET`, `GET_STATE`, `RESET`, ...) simulating a serial/HIL link.

It has one deliberately subtle, safety-critical behavior: **shutdown latches**. Once the controller shuts down (temperature at/beyond a safety bound), it does **not** automatically recover when the temperature returns to a safe range — only an explicit `RESET` clears it. The datasheet (`firmware/datasheet.md`) mentions this exists but explicitly says to consult the source for the exact behavior, rather than documenting it directly. This is the whole point of the setup: it creates a real, measurable difference between a test suite that only reads documentation and one that actually reads and reasons about the source — which is exactly what the agent has both tools to do, and exactly what the comparison in `src/compare.py` is built to detect.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Firmware under test | C, compiled with `gcc` | Small, realistic, no hardware dependency; swappable for a real Zephyr/FreeRTOS/Arduino target later |
| Test execution | Python `subprocess`, fresh process per test | Simulates a HIL serial link without needing real hardware; fresh-process-per-test avoids state leakage between tests |
| Agent framework | `langchain.agents.create_agent` (LangGraph 1.2.9 under the hood) | Current (non-deprecated) prebuilt agent API — gives tool-calling + structured output with minimal boilerplate |
| LLM providers | Anthropic (`langchain-anthropic`) or OpenAI (`langchain-openai`) | Both named explicitly in the posting; the code supports either via a `--provider` flag |
| Structured output | Pydantic (`TestPlan` / `ProposedTestCase`) | The agent's final output is validated, directly-usable data, not free text you'd have to regex out |
| Retrieval ("RAG grounded in documentation") | Lightweight keyword-overlap retrieval over `datasheet.md` | Deliberately minimal for a small single-file datasheet — see "Scale it up" for the real-embeddings upgrade path |
| Testing | `pytest` for harness sanity checks | Confirms the firmware/harness themselves are trustworthy before any agent output is judged against them |

All of the above (except the two API-key-gated calls) was actually run in this environment during development — see [Status](#status--whats-actually-verified).

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
  datasheet.md               its documentation (deliberately incomplete on the latching behavior)
src/
  harness/test_harness.py    compiles + runs the firmware, scores test cases
  agent/tools.py              read_docs, read_source, list_firmware_files
  agent/mock_agent.py         deterministic stand-in, no API key needed
  agent/real_agent.py         the actual LLM agent (create_agent + tools + structured output)
  compare.py                  baseline-vs-candidate scoring and category coverage
baseline/
  human_written_tests.py      the hand-authored reference suite (6 tests, includes the latching case)
tests/
  test_harness_sanity.py      pytest checks on the harness/firmware themselves
configs/agent_config.yaml     provider/model config for real-agent runs
run_baseline.py                entry point: baseline suite only
run_agent.py                   entry point: mock or real agent, + comparison report
```

## How to run

```bash
pip install -r requirements.txt

# 1. Sanity-check the harness and firmware themselves (no API key needed)
python -m pytest tests/ -v

# 2. Run just the human baseline
python run_baseline.py

# 3. Run the FULL pipeline in mock mode -- no API key, proves everything's wired up
python run_agent.py --mock

# 4. Run it for real (needs an API key)
export ANTHROPIC_API_KEY=your-key-here      # or OPENAI_API_KEY
python run_agent.py --provider anthropic --model claude-sonnet-4-5-20250929
python run_agent.py --provider openai --model gpt-4o
```

On Colab: put your key in the Secrets panel and `os.environ["ANTHROPIC_API_KEY"] = ...` at the top of a cell instead of `export`.

## Status — what's actually verified

Everything below was actually executed during development of this repo, not just written and assumed to work:

- ✅ Firmware **compiles cleanly** with `gcc -O2 -Wall` and behaves exactly as designed, including the latching-shutdown edge case, confirmed by direct manual test.
- ✅ The 6-test **human baseline suite passes 6/6** against the compiled firmware.
- ✅ All 6 **pytest harness sanity checks pass** (compile check, boundary-inclusivity check, unknown-command handling, and a specific check that fresh-process-per-test really does prevent state leakage).
- ✅ The **agent tools** (`read_docs`, `read_source`, `list_firmware_files`) were called directly and confirmed to return correct content — `read_docs` correctly surfaces the "consult the source" passage as the top hit for fault-recovery queries.
- ✅ The **full pipeline runs end-to-end in mock mode** (`python run_agent.py --mock`) — real output from an actual run:

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

  This is exactly the result the setup was designed to be able to produce: a docs-only test strategy (which is what the mock agent deliberately simulates) passes all its own tests but **misses the one behavior class that required reading source code**, not just documentation.

- ✅ **Agent construction** (`create_agent(model, tools=[...], response_format=TestPlan)`) was verified to build correctly against the exact installed versions of `langgraph`==1.2.9, `langchain`==1.3.14, and `langchain-anthropic`.
- ⏳ **Not yet run:** an actual LLM invocation (`run_agent.py` without `--mock`) — this needs a real API key, which is yours to add. Everything it depends on has been verified up to the point of the actual API call.

## Research design (what to actually measure once you have a key)

1. **Run the real agent** and see whether it independently discovers the latching-shutdown behavior via `read_source`, the way the mock agent (by construction) cannot.
2. **Architecture comparison** (the posting's research question 1): implement a second architecture — e.g., a multi-step LangGraph flow that's forced to call `read_source` before finalizing tests, vs. the current single ReAct loop that decides tool use on its own — and compare category coverage between them.
3. **Model comparison**: run the same agent with a couple of different models (`configs/agent_config.yaml` has candidates queued) and compare coverage and cost.
4. **Report honestly**: if the real agent also misses the latching case, that's a real, useful finding about current tool-using agents' default behavior on undocumented-but-source-visible logic — not a failed experiment.

## Scale it down / up
- **Down:** if you're short on API budget, run once with a cheap/fast model (e.g., a Haiku-class model) before spending on a larger one.
- **Up:** swap the keyword-retrieval `read_docs` for real embedding-based RAG once you have more than one small datasheet file; swap the simulated C firmware for a real small Zephyr/FreeRTOS sample project (the harness's subprocess-based design transfers directly, you'd just point `FIRMWARE_SRC`/`FIRMWARE_BIN` at the real build).

## Application pitch line

*"I built a small agent that reads embedded C firmware and its documentation, proposes HIL test cases, and runs them against the real firmware — then measured, category by category, whether it discovers safety-relevant behavior that's only visible in source, not docs. A deliberately naive baseline agent misses it, as expected; I'm now running the real LLM agent to see whether it does better. Repo here: [link]."*
