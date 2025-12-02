"""
tools.py

The tools available to the test-generation agent. Kept deliberately small
and dependency-light:

  - list_firmware_files : discover what's available to read
  - read_source          : read the firmware C source directly
  - read_docs             : lightweight keyword-retrieval over the datasheet
                             (a real RAG-over-embeddings setup is the obvious
                             upgrade once this pipeline is proven -- see the
                             README's "Scale it up" section)

The datasheet deliberately does NOT fully document the latching-shutdown
behavior (see firmware/datasheet.md) -- it explicitly tells the reader to
consult the source for exact fault-recovery semantics. That is intentional:
it gives the agent a real reason to use BOTH tools, not just one, which is
the actual thing this project is trying to observe.
"""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.tools import tool

FIRMWARE_DIR = Path(__file__).resolve().parents[2] / "firmware"


def _split_into_chunks(text: str) -> list[str]:
    """Split markdown into paragraph-ish chunks for retrieval."""
    chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
    return chunks


@tool
def list_firmware_files() -> str:
    """List the files available in the firmware directory under test."""
    files = sorted(p.name for p in FIRMWARE_DIR.iterdir() if p.is_file())
    return "\n".join(files)


@tool
def read_source(filename: str) -> str:
    """Read the full contents of a firmware source file by name
    (e.g. 'thermostat_controller.c'). Use this to check exact behavior
    that isn't fully spelled out in the datasheet."""
    path = FIRMWARE_DIR / filename
    if not path.exists() or path.resolve().parent != FIRMWARE_DIR.resolve():
        return f"ERROR: no such firmware file '{filename}'"
    return path.read_text(encoding="utf-8")


@tool
def read_docs(query: str, top_k: int = 3) -> str:
    """Search the firmware datasheet for passages relevant to `query` and
    return the top matches. Use this first for interface-level questions
    (safe ranges, commands, expected states) before reading raw source."""
    datasheet = FIRMWARE_DIR / "datasheet.md"
    if not datasheet.exists():
        return "ERROR: no datasheet found."
    chunks = _split_into_chunks(datasheet.read_text(encoding="utf-8"))
    query_terms = set(re.findall(r"[a-zA-Z]+", query.lower()))

    scored = []
    for chunk in chunks:
        chunk_terms = set(re.findall(r"[a-zA-Z]+", chunk.lower()))
        overlap = len(query_terms & chunk_terms)
        if overlap > 0:
            scored.append((overlap, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [chunk for _, chunk in scored[:top_k]]
    if not top:
        return "No relevant passages found in the datasheet for that query."
    return "\n\n---\n\n".join(top)


ALL_TOOLS = [list_firmware_files, read_source, read_docs]
