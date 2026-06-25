import streamlit as st
from agent import run_agent

st.set_page_config(page_title="Inventory Q&A Agent", page_icon="📦")
st.title("📦 Inventory Data Agent")
st.caption("Ask questions about the inventory spreadsheet. The agent writes pandas code to compute answers and can search the web for definitions/context.")

if "history" not in st.session_state:
    st.session_state.history = []          # Anthropic API format (for the agent)
if "display_history" not in st.session_state:
    st.session_state.display_history = []  # simple list for rendering chat bubbles

for msg in st.session_state.display_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Which product has the lowest stock right now?"):
    st.session_state.display_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, st.session_state.history = run_agent(prompt, st.session_state.history)
        st.markdown(answer)

    st.session_state.display_history.append({"role": "assistant", "content": answer})
