"""
Built-in tools available to agents.

Each tool is a LangChain StructuredTool / Tool that can be bound to an LLM.
"""

from __future__ import annotations
import math
import datetime
import asyncio
from typing import Optional
from langchain_core.tools import tool


# ─── Web Search ────────────────────────────────────────────────────────────────

@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for up-to-date information. Returns top results with titles and snippets."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"**{r['title']}**\n{r['body']}\nURL: {r['href']}\n")
        return "\n---\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search failed: {e}"


# ─── Calculator ────────────────────────────────────────────────────────────────

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely. Examples: '2+2', 'sqrt(16)', '100 * 0.15'."""
    try:
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
        allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
        result = eval(expression, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


# ─── Date/Time ─────────────────────────────────────────────────────────────────

@tool
def get_current_datetime(timezone: str = "UTC") -> str:
    """Get the current date and time."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S UTC")


# ─── Text Tools ────────────────────────────────────────────────────────────────

@tool
def word_count(text: str) -> str:
    """Count words, sentences, and characters in a text."""
    words = len(text.split())
    sentences = text.count(".") + text.count("!") + text.count("?")
    chars = len(text)
    return f"Words: {words}, Sentences: {sentences}, Characters: {chars}"


# ─── File Tools ────────────────────────────────────────────────────────────────

@tool
def write_output_file(filename: str, content: str) -> str:
    """Save content to a file in the outputs/ directory. Use for reports, notes, etc."""
    import os
    os.makedirs("outputs", exist_ok=True)
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    path = os.path.join("outputs", safe_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved to {path}"


@tool
def read_output_file(filename: str) -> str:
    """Read a file from the outputs/ directory."""
    import os
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    path = os.path.join("outputs", safe_name)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filename}"


# ─── Python REPL ───────────────────────────────────────────────────────────────

@tool
def python_repl(code: str) -> str:
    """Execute Python code and return the output. Good for data analysis and computations.
    Note: For safety, network and file-system access is restricted."""
    import sys
    import io
    import contextlib

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {"__builtins__": {"print": print, "len": len, "range": range,  # noqa: S102
                                          "str": str, "int": int, "float": float,
                                          "list": list, "dict": dict, "set": set,
                                          "enumerate": enumerate, "zip": zip,
                                          "sorted": sorted, "sum": sum, "min": min,
                                          "max": max, "abs": abs, "round": round}})
    except Exception as e:
        return f"Error: {e}"
    return output.getvalue() or "(no output)"


# ─── Registry ──────────────────────────────────────────────────────────────────

ALL_TOOLS = {
    "web_search": web_search,
    "calculator": calculator,
    "get_current_datetime": get_current_datetime,
    "word_count": word_count,
    "write_output_file": write_output_file,
    "read_output_file": read_output_file,
    "python_repl": python_repl,
}

TOOL_DESCRIPTIONS = {
    "web_search": "Search the web for current information",
    "calculator": "Evaluate mathematical expressions",
    "get_current_datetime": "Get current date and time",
    "word_count": "Count words/sentences in text",
    "write_output_file": "Write content to an output file",
    "read_output_file": "Read from an output file",
    "python_repl": "Execute Python code",
}


def get_tools_for_agent(tool_names: list[str]) -> list:
    """Return LangChain tool objects for the given tool names."""
    return [ALL_TOOLS[name] for name in tool_names if name in ALL_TOOLS]
