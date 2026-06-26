import json
from pathlib import Path

import streamlit as st

from pipeline import process_document
from schemas import CONFIDENCE_THRESHOLD, DOCUMENT_TYPES

st.set_page_config(page_title="Document Extraction Pipeline", page_icon="📄", layout="wide")
st.title("📄 Insurance Document Extraction Pipeline")
st.caption(f"Classifies documents into 10 known types, extracts fields, and flags anything below {CONFIDENCE_THRESHOLD} confidence.")

DOCS_DIR = Path("documents")
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

image_files = sorted(p for p in DOCS_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS)

if "results" not in st.session_state:
    st.session_state.results = {}  # filename -> result dict

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Documents")
    selected = st.radio(
        "Pick a document to process",
        options=[p.name for p in image_files],
        label_visibility="collapsed",
    )
    selected_path = DOCS_DIR / selected
    st.image(str(selected_path), use_container_width=True)

    if st.button("🔍 Classify & Extract", type="primary", use_container_width=True):
        with st.spinner("Calling Gemini..."):
            try:
                result = process_document(selected_path)
                st.session_state.results[selected] = result
            except Exception as e:
                st.error(f"Failed: {e}")

    if st.button("▶️ Run ALL documents", use_container_width=True):
        progress = st.progress(0.0)
        for i, p in enumerate(image_files):
            try:
                st.session_state.results[p.name] = process_document(p)
            except Exception as e:
                st.session_state.results[p.name] = {"file": p.name, "document_type": "error", "error": str(e)}
            progress.progress((i + 1) / len(image_files))
        st.success(f"Processed {len(image_files)} documents.")

with col_right:
    st.subheader("Result")
    result = st.session_state.results.get(selected)

    if not result:
        st.info("Click 'Classify & Extract' on the left to process this document.")
    else:
        doc_type = result.get("document_type")
        type_conf = result.get("type_confidence")
        flagged = result.get("document_flagged_for_review")

        c1, c2, c3 = st.columns(3)
        c1.metric("Document Type", DOCUMENT_TYPES.get(doc_type, {}).get("label", doc_type))
        c2.metric("Type Confidence", f"{type_conf:.2f}" if type_conf is not None else "-")
        c3.metric("Status", "🚩 FLAGGED" if flagged else "✅ OK")

        if result.get("flag_reason"):
            st.warning(result["flag_reason"])

        st.markdown("#### Extracted Fields")
        fields = result.get("fields", {})
        if not fields:
            st.write("No fields extracted (unsupported document type).")
        for name, data in fields.items():
            conf = data.get("confidence", 0)
            value = data.get("value")
            is_low = conf < CONFIDENCE_THRESHOLD
            badge = "🔴" if is_low else "🟢"
            note = data.get("validation_note")
            legible = data.get("legible", True)

            with st.container(border=True):
                f1, f2 = st.columns([3, 1])
                f1.markdown(f"**{name}**: {value if value is not None else '_(not found)_'}")
                f2.markdown(f"{badge} {conf:.2f}")
                if not legible:
                    st.caption("⚠️ Marked illegible by the model")
                if note:
                    st.caption(f"⚠️ {note}")

        with st.expander("Raw JSON"):
            st.json(result)

st.divider()
flagged_count = sum(1 for r in st.session_state.results.values() if r.get("document_flagged_for_review"))
st.caption(f"Processed this session: {len(st.session_state.results)} / {len(image_files)}  |  Flagged: {flagged_count}")
