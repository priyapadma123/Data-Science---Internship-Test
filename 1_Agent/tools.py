"""Tools available to the agent.

1. query_data  -> writes pandas code, executes it against the inventory
   DataFrame in an isolated subprocess (so a buggy/odd snippet can't crash
   or reach into the main chat process), returns whatever was printed.
2. web_search  -> looks up external definitions/context the spreadsheet
   itself doesn't contain (e.g. "what is a reorder point").
"""
import subprocess
import sys
import textwrap

from data_loader import load_inventory

TIMEOUT_SECONDS = 10


def query_data(code: str) -> str:
    """Run pandas code against the inventory data in a separate process.

    The code must produce its answer via `print(...)`. `df` is preloaded.
    """
    wrapped = textwrap.dedent(f"""
        import pandas as pd
        from data_loader import load_inventory
        df = load_inventory({load_inventory.__defaults__[0]!r})
        {textwrap.indent(code, "        ").strip()}
    """)
    try:
        result = subprocess.run(
            [sys.executable, "-c", wrapped],
            cwd=".",
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: code took too long to run (possible infinite loop)."

    if result.returncode != 0:
        return f"ERROR while executing code:\n{result.stderr[-1500:]}"
    output = result.stdout.strip()
    return output if output else "Code ran but produced no printed output. Make sure to use print()."


def web_search(query: str) -> str:
    """Search the web for definitions/context not present in the spreadsheet."""
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS  # fallback for older package name

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "No search results found."

    formatted = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        formatted.append(f"- {title}: {body}")
    return "\n".join(formatted)


TOOL_DEFINITIONS = [
    {
        "name": "query_data",
        "description": (
            "Execute pandas code against the inventory DataFrame `df` to answer "
            "questions that require calculation, filtering, sorting, or aggregation "
            "over the spreadsheet data. ALWAYS use this instead of guessing numbers. "
            "Your code MUST print() the final answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python/pandas code. `df` is already loaded. Must print() the result.",
                }
            },
            "required": ["code"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web for definitions, context, or domain knowledge that is NOT "
            "present in the spreadsheet itself (e.g. what a business term means, industry "
            "benchmarks). Do not use this for anything answerable from the data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."}
            },
            "required": ["query"],
        },
    },
]

TOOL_FUNCTIONS = {
    "query_data": lambda inp: query_data(inp["code"]),
    "web_search": lambda inp: web_search(inp["query"]),
}


def to_openai_format(tool_defs):
    """Converts Anthropic-style tool defs (input_schema) into the OpenAI/Groq
    function-calling format (type: function, function: {parameters: ...}).
    """
    converted = []
    for t in tool_defs:
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
        )
    return converted
