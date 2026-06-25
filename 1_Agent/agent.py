"""Agent loop: the model decides when to call query_data / web_search,
we execute the tool, feed the result back, repeat until it gives a
final plain-English answer.

Uses Groq's free API (https://console.groq.com) - no credit card required,
ever. Groq's API is OpenAI-compatible, so tool calling uses the standard
"functions" format rather than Anthropic's.
"""
import json
import os

from dotenv import load_dotenv
from groq import Groq
from data_loader import load_inventory, schema_description
from tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS, to_openai_format

load_dotenv()  # reads GROQ_API_KEY from a .env file in this same folder

MODEL = "openai/gpt-oss-120b"  # free on Groq, supports tool calling
MAX_TURNS = 6  # safety cap on tool-call round-trips

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
OPENAI_TOOLS = to_openai_format(TOOL_DEFINITIONS)

_df = load_inventory()
SYSTEM_PROMPT = f"""You are a data analyst assistant for an inventory spreadsheet.

{schema_description(_df)}

Rules:
- For ANY question involving numbers, totals, comparisons, filtering, or ranking,
  call query_data and write pandas code. Never compute or guess numbers yourself.
- For questions about terms/definitions/context not in the data (e.g. "what does
  reorder point mean", "what's a good stock turnover ratio"), call web_search.
- After getting tool results, ALWAYS summarise the answer in clear, plain English
  for a non-technical user. Don't just dump raw numbers without explanation.
- If a question needs both a calculation AND a definition, use both tools before answering.
- IMPORTANT: in pandas code passed to query_data, always use double quotes for
  strings (e.g. df.nlargest(3, "cost_price_total_usd")), never single quotes.
  Keep code on as few lines as possible.
"""


def _call_with_retry(history, max_retries=2):
    """Calls the Groq API, retrying if the model produces a malformed tool
    call (a known intermittent quirk with Llama on Groq, usually triggered
    by quote-heavy code arguments)."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=history,
                tools=OPENAI_TOOLS,
                tool_choice="auto",
                temperature=0,
                max_tokens=1500,
            )
        except Exception as e:
            if "tool_use_failed" in str(e) and attempt < max_retries:
                last_error = e
                continue
            raise
    raise last_error


def run_agent(user_message: str, history: list) -> tuple:
    """Runs one user turn through the agent loop.

    `history` is the running list of {role, content, ...} chat-completion
    messages. Returns (final_text_answer, updated_history).
    """
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
    history.append({"role": "user", "content": user_message})

    for _ in range(MAX_TURNS):
        try:
            response = _call_with_retry(history)
        except Exception as e:
            return (
                "I had trouble formatting a query for that question — could you "
                "try rephrasing it more simply (e.g. break it into smaller steps)?"
                f"\n\n[debug: {e}]"
            ), history
        msg = response.choices[0].message
        history.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content, history

        for call in msg.tool_calls:
            fn = TOOL_FUNCTIONS.get(call.function.name)
            args = json.loads(call.function.arguments)
            output = fn(args) if fn else f"Unknown tool: {call.function.name}"
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": output,
                }
            )

    return "I couldn't finish reasoning about this in time. Try rephrasing your question.", history


if __name__ == "__main__":
    hist = []
    for q in [
        "Which 3 products have the highest total cost value?",
        "What does 'hand-in-stock' typically mean in inventory management?",
        "Which products are sold out or close to it relative to opening stock?",
    ]:
        print(f"\nQ: {q}")
        answer, hist = run_agent(q, hist)
        print(f"A: {answer}")