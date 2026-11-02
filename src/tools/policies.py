"""RAG over the store policies PDF using TF-IDF + cosine similarity."""

import re
from pathlib import Path
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import POLICIES_PDF


def _extract_text(pdf_path: Path) -> str:
    """Extract all text from the policies PDF."""
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """
    Split text into chunks by section headings (## or numbered sections)
    and cap chunk size. Keeps semantic boundaries where possible.
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Split by section-like patterns (e.g., "4.1", "5.2", "6.")
    raw_chunks = re.split(r"(?=\b\d+(?:\.\d+)*\.?\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", text)

    chunks = []
    for c in raw_chunks:
        c = c.strip()
        if not c:
            continue
        # If a chunk is too long, split by sentence boundaries
        if len(c) <= max_chars:
            chunks.append(c)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", c)
            buffer = ""
            for s in sentences:
                if len(buffer) + len(s) + 1 <= max_chars:
                    buffer = f"{buffer} {s}".strip()
                else:
                    if buffer:
                        chunks.append(buffer)
                    buffer = s
            if buffer:
                chunks.append(buffer)

    return chunks


class PoliciesIndex:
    """TF-IDF index over policy chunks. Built lazily on first use."""

    def __init__(self):
        self._chunks: list[str] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._ready = False

    def _build(self):
        text = _extract_text(POLICIES_PDF)
        self._chunks = _chunk_text(text)
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            stop_words=None,  # Portuguese: keep stopwords, they matter for grammar
            max_features=5000,
        )
        self._matrix = self._vectorizer.fit_transform(self._chunks)
        self._ready = True

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Return top-k policy chunks most similar to the query."""
        if not self._ready:
            self._build()

        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        top_idx = scores.argsort()[::-1][:top_k]

        results = []
        for i in top_idx:
            if scores[i] <= 0:
                continue
            results.append({
                "chunk": self._chunks[i],
                "score": float(scores[i]),
            })
        return results


# Singleton
_index = PoliciesIndex()


def search_policies(query: str, top_k: int = 3) -> list[dict]:
    """
    Search the store policies for relevant excerpts.
    Use this for questions about: opening hours, payment methods,
    returns/exchanges, shipping, warranty, privacy, promotions rules,
    store address, or general store info.
    """
    return _index.search(query, top_k=top_k)
