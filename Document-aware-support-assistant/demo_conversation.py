"""Runs a scripted 10+ turn conversation to demonstrate:
  - remembering earlier turns
  - not repeating info already given
  - handling topic switches gracefully
  - citing the specific section for each claim

Run: python3 demo_conversation.py
"""
from assistant import new_session, run_turn

CONVERSATION = [
    "Hi, how do I cancel my subscription?",                          # topic: billing
    "Will I get a refund if I cancel today?",                        # follow-up, same topic
    "What happens to my files after I downgrade?",                   # follow-up, references 2.3 again -> repeat test
    "Different question - the app keeps crashing on my phone, why?", # topic switch: troubleshooting
    "I tried clearing the cache and it still crashes, what's next?", # follow-up on troubleshooting
    "Quick one - what 2FA options do you support?",                  # topic switch: account setup
    "Going back to billing - what payment methods do you accept?",   # topic switch back to billing
    "Can I export my data before I delete my account?",              # topic switch: privacy
    "How long do you keep my data after I delete the account?",      # follow-up, privacy
    "One more - what's your API rate limit on the Pro plan?",        # topic switch: API
    "And what happens if I go over that limit?",                     # follow-up, API
]


def main():
    memory = new_session()
    for i, question in enumerate(CONVERSATION, 1):
        answer, chunks = run_turn(question, memory)
        cited = ", ".join(c["section"] for c in chunks)
        print(f"\n{'='*70}\nTurn {i}")
        print(f"User: {question}")
        print(f"Retrieved sections: {cited}")
        print(f"Assistant: {answer}")


if __name__ == "__main__":
    main()
