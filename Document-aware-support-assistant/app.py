import streamlit as st
from assistant import new_session, run_turn

st.set_page_config(page_title="CloudSync Support Assistant", page_icon="💬")
st.title("💬 CloudSync Support Assistant")
st.caption("Ask anything about the CloudSync support manual. Answers cite the exact section they're drawn from.")

if "memory" not in st.session_state:
    st.session_state.memory = new_session()
if "display_history" not in st.session_state:
    st.session_state.display_history = []

for msg in st.session_state.display_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sections"):
            st.caption("📄 Sections used: " + ", ".join(msg["sections"]))

if prompt := st.chat_input("e.g. How do I cancel my subscription?"):
    st.session_state.display_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, chunks = run_turn(prompt, st.session_state.memory)
        st.markdown(answer)
        sections = [c["section"] for c in chunks]
        st.caption("📄 Sections used: " + ", ".join(sections))

    st.session_state.display_history.append(
        {"role": "assistant", "content": answer, "sections": [c["section"] for c in chunks]}
    )
