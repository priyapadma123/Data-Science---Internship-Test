"""Tracks conversation state within a session:
- the running chat history (for the LLM's context window)
- which document sections have already been surfaced, so the assistant can
  avoid repeating itself verbatim on a later turn
"""


class ConversationMemory:
    def __init__(self, system_prompt: str):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.covered_sections = set()  # e.g. {"support_manual.md::2.3"}

    def add_user(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str):
        self.messages.append({"role": "assistant", "content": text})

    def mark_covered(self, chunks: list[dict]):
        for c in chunks:
            self.covered_sections.add(f"{c['doc']}::{c['section']}")

    def already_covered_note(self, chunks: list[dict]) -> str:
        """For sections retrieved THIS turn that were already shown before,
        produce a note telling the model not to re-explain them from scratch.
        """
        repeats = [
            c["section"] for c in chunks if f"{c['doc']}::{c['section']}" in self.covered_sections
        ]
        if not repeats:
            return ""
        return (
            f"Note: you already explained {', '.join(repeats)} earlier in this "
            "conversation. Don't repeat the full explanation again - briefly "
            "reference what was already said and add only new/relevant detail."
        )
