"""Document-aware support assistant.

Each turn: retrieve relevant sections -> build a context block with explicit
section labels -> ask the model to answer using ONLY that context and to
cite the section(s) it drew from -> update memory.
"""
import os

from dotenv import load_dotenv
from groq import Groq

from memory import ConversationMemory
from retriever import Retriever

load_dotenv()

MODEL = "openai/gpt-oss-120b"  # free on Groq, reliable instruction-following
TOP_K = 3

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
retriever = Retriever()

SYSTEM_PROMPT = """You are a support assistant for CloudSync, answering questions
using ONLY the provided document context for each turn - never invent facts
not present in the context.

Rules:
1. Every factual claim you make MUST be attributed to a section, written like:
   "(Section 2.3 - Cancelling a Subscription)" right after the claim.
2. If the retrieved context doesn't actually answer the question, say so
   plainly instead of guessing.
3. If a note says you already explained something earlier in this
   conversation, don't repeat the full explanation - briefly acknowledge it
   and add only new detail relevant to the current question.
4. If the user switches topics, just answer the new topic directly - don't
   force a connection to the previous topic.
5. Keep answers concise and conversational, like a real support agent, not a
   wall of bullet points.
"""


def format_context(chunks: list[dict]) -> str:
    blocks = []
    for c in chunks:
        blocks.append(f"[Section {c['section']}]\n{c['text']}")
    return "\n\n".join(blocks)


def run_turn(user_message: str, memory: ConversationMemory) -> tuple:
    """Returns (answer_text, cited_chunks) and mutates memory in place."""
    chunks = retriever.search(user_message, k=TOP_K)
    context_block = format_context(chunks)
    repeat_note = memory.already_covered_note(chunks)

    turn_content = f"Context:\n{context_block}\n\n"
    if repeat_note:
        turn_content += f"{repeat_note}\n\n"
    turn_content += f"User question: {user_message}"

    memory.add_user(turn_content)

    response = client.chat.completions.create(
        model=MODEL,
        messages=memory.messages,
        temperature=0.3,
        max_tokens=600,
    )
    answer = response.choices[0].message.content
    memory.add_assistant(answer)
    memory.mark_covered(chunks)
    return answer, chunks


def new_session() -> ConversationMemory:
    return ConversationMemory(SYSTEM_PROMPT)
