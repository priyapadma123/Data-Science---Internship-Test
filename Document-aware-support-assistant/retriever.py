"""Loads the pre-built embeddings index and retrieves the top-k most
relevant sections for a query."""
import json
from pathlib import Path

import numpy as np

INDEX_PATH = Path("index")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


class Retriever:
    def __init__(self):
        self.embeddings = np.load(INDEX_PATH / "embeddings.npy")
        with open(INDEX_PATH / "metadata.json", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def search(self, query: str, k: int = 3) -> list[dict]:
        model = _get_model()
        q_emb = model.encode([query], normalize_embeddings=True)[0]
        scores = self.embeddings @ q_emb  # cosine similarity (vectors are normalized)
        top_idx = np.argsort(scores)[::-1][:k]
        results = []
        for i in top_idx:
            chunk = dict(self.metadata[i])
            chunk["score"] = float(scores[i])
            results.append(chunk)
        return results


if __name__ == "__main__":
    r = Retriever()
    for q in ["how do I get my money back", "app keeps closing", "limit on API calls"]:
        print(f"\nQuery: {q}")
        for hit in r.search(q, k=2):
            print(f"  [{hit['score']:.3f}] {hit['doc']} :: {hit['section']}")
