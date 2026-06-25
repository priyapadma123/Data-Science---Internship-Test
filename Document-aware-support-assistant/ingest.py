"""Splits the knowledge-base markdown into section-level chunks (so each
chunk maps to exactly one citable section), embeds them with a free local
model, and saves the result to disk for the retriever to load.

Run this once whenever documents/ changes:
    python3 ingest.py
"""
import json
import re
from pathlib import Path

import numpy as np

DOCS_DIR = Path("documents")
INDEX_PATH = Path("index")


def parse_sections(text: str, doc_name: str) -> list[dict]:
    """Splits on markdown ### headers (subsections) - each becomes one chunk.
    A ## header (top-level section) is carried along as context but isn't
    its own chunk, since ### is the citable granularity in this document.
    """
    lines = text.split("\n")
    chunks = []
    current_section = None
    current_subsection = None
    buffer = []

    def flush():
        if current_subsection and buffer:
            body = "\n".join(buffer).strip()
            if body:
                chunks.append(
                    {
                        "doc": doc_name,
                        "section": current_subsection,
                        "text": body,
                    }
                )

    for line in lines:
        if line.startswith("## "):
            flush()
            buffer = []
            current_section = line[3:].strip()
            current_subsection = None
        elif line.startswith("### "):
            flush()
            buffer = []
            current_subsection = line[4:].strip()
        else:
            buffer.append(line)
    flush()
    return chunks


def load_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def build_index():
    model = load_embedder()
    all_chunks = []
    for path in DOCS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        all_chunks.extend(parse_sections(text, path.name))

    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, normalize_embeddings=True)

    INDEX_PATH.mkdir(exist_ok=True)
    np.save(INDEX_PATH / "embeddings.npy", embeddings)
    with open(INDEX_PATH / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"Indexed {len(all_chunks)} sections from {len(list(DOCS_DIR.glob('*.md')))} document(s).")
    for c in all_chunks:
        print(f"  - [{c['doc']}] {c['section']}")


if __name__ == "__main__":
    build_index()
