"""
real_agent.py

The actual LLM-backed test-generation agent, built on `langchain.agents.create_agent`
(LangGraph under the hood) with tool use and structured output. Requires a
real API key -- see README.md "Running the real agent" for setup.

Architecture (v1 -- see README "Research design" for the comparison this
sets up against a second architecture later):
  A single ReAct-style agent loop with two tools (read_docs, read_source)
  and a Pydantic `response_format` so the final output is a validated,
  directly-usable TestPlan rather than free text you'd have to parse
  yourself.

This was validated against the actually-installed library versions in this
project's environment (LangGraph 1.2.9 / LangChain 1.3.14 / langchain-anthropic)
by constructing (not invoking) the agent graph -- see the git history / dev
notes for that check. You still need your own API key to actually invoke it.
"""

from __future__ import annotations

import os
from typing import List

from pydantic import BaseModel, Field

from src.agent.tools import ALL_TOOLS
from src.harness.test_harness import TestCase

SYSTEM_PROMPT = """You are a hardware-in-the-loop test engineer for embedded firmware.

You are testing a thermostat/safety-cutoff controller. You interact with it
by proposing test cases; each test case is a sequence of commands sent to
the firmware, and the exact sequence of response lines you expect back.

Available commands: SET_TEMP <float>, SET_TARGET <float>, GET_STATE,
GET_HEATER, GET_COOLER, RESET.
Possible responses: OK, ERROR <reason>, STATE <NORMAL|WARNING|SHUTDOWN>,
HEATER <ON|OFF>, COOLER <ON|OFF>.

Use read_docs first to understand the documented interface contract. Then
use read_source to check for any safety-relevant behavior the documentation
explicitly says to verify against the source rather than assuming standard
semantics. Do not guess at exact response text -- ground every expected
output in what you actually read from the docs or source.

Propose a diverse set of 5-8 test cases covering: normal operation, both
safety boundaries, the warning zone, invalid input handling, and any
stateful/fault-recovery behavior you find in the source. For each test,
give a short rationale citing whether it came from the docs or the source.
"""


class ProposedTestCase(BaseModel):
    name: str = Field(description="A short, descriptive snake_case test name")
    commands: List[str] = Field(description="Exact command sequence to send to the firmware")
    expected_outputs: List[str] = Field(
        description="Exact expected response lines, in order, one per output-producing command"
    )
    rationale: str = Field(
        description="Why this test matters, and whether it's grounded in the docs or the source"
    )


class TestPlan(BaseModel):
    tests: List[ProposedTestCase] = Field(description="The proposed HIL test suite")


def _build_model(provider: str, model_name: str):
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name)
    raise ValueError(f"Unknown provider: {provider!r} (use 'anthropic' or 'openai')")


def build_agent(provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929"):
    from langchain.agents import create_agent

    model = _build_model(provider, model_name)
    return create_agent(
        model,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        response_format=TestPlan,
    )


def propose_tests(provider: str = "anthropic", model_name: str = "claude-sonnet-4-5-20250929") -> list[TestCase]:
    """Run the real agent and convert its structured output into harness TestCase objects."""
    agent = build_agent(provider, model_name)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Propose a HIL test suite for the thermostat controller."}]}
    )
    plan: TestPlan = result["structured_response"]
    return [
        TestCase(
            name=t.name,
            commands=t.commands,
            expected_outputs=t.expected_outputs,
            rationale=t.rationale,
        )
        for t in plan.tests
    ]


def _check_api_key(provider: str) -> None:
    key_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if not os.environ.get(key_var):
        raise EnvironmentError(
            f"{key_var} is not set. Set it before running the real agent, e.g.:\n"
            f"  export {key_var}=your-key-here   (Colab: use the Secrets panel)"
        )
