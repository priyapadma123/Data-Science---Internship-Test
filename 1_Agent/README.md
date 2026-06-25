# Inventory Q&A Agent

A chat agent that answers questions about `inventory_data.xlsx` by writing and
executing pandas code, and falls back to a web search for definitions/context
not contained in the spreadsheet.

## How it works

- **data_loader.py** — reads the Excel file (skips the title rows, starts at
  the real header) into a clean DataFrame.
- **tools.py** — two tools the agent can call:
  - `query_data`: the agent writes pandas code, which runs in an isolated
    subprocess (separate Python process, 10s timeout) so a bad snippet can't
    crash or hang the main app. Always returns the literal `print()` output —
    the agent never invents numbers itself.
  - `web_search`: looks up terms/context not in the data (e.g. "what's a good
    inventory turnover ratio") using DuckDuckGo (no API key needed).
- **agent.py** — the agent loop: sends the question + tool definitions to
  Claude, runs whichever tool Claude calls, feeds the result back, repeats
  until Claude gives a final plain-English answer.
- **app.py** — Streamlit chat UI on top of the agent.

## Setup — completely free, no credit card

This uses **Groq** (console.groq.com) instead of a paid API. Groq's free tier
needs no credit card, ever, and gives access to Llama 3.3 70B which supports
tool calling.

```bash
pip install groq ddgs streamlit pandas openpyxl
```

Get a free key:
1. Go to console.groq.com and sign up with email/Google/GitHub
2. Click "API Keys" in the sidebar → "Create API Key"
3. Copy it (starts with `gsk_`)

Set it as an environment variable:

```bash
setx GROQ_API_KEY "gsk_..."            # Windows (then close & reopen terminal)
```

## Run

Chat UI:
```bash
streamlit run app.py
```

## Example questions to demo

- "Which 3 products have the highest total cost value?"
- "What does 'hand-in-stock' typically mean in inventory management?" (web_search)
- "Which products are close to running out of stock relative to opening stock?"
- "What's the total value of all inventory currently on hand?"
- "List products where units sold is more than half the opening stock."
