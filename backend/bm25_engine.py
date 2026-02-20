"""
Lightweight BM25-Okapi search engine with JSON-file persistence.
Pure Python — no external dependencies beyond the standard library.
"""

import json
import math
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


# Common English stopwords (kept small — the corpus is tiny)
_STOPWORDS = frozenset(
    "a an and are as at be but by for from has have he her his i in is it its"
    " me my no nor not of on or our own she so than that the their them then"
    " there these they this to up us was we were what when where which who will"
    " with you your".split()
)


def _tokenize(text: str) -> List[str]:
    """Lowercase alphanumeric tokenization with stopword removal."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


class BM25Index:
    """
    BM25-Okapi index backed by a single JSON file.

    Each document is stored as::

        {"id": str, "text": str, "metadata": dict, "tokens": list[str]}

    The index file also contains pre-computed corpus stats so that searches
    don't need a full rescan.
    """

    def __init__(self, path: Path, k1: float = 1.5, b: float = 0.75):
        self.path = Path(path)
        self.k1 = k1
        self.b = b

        # In-memory document store
        self._docs: List[Dict[str, Any]] = []
        self._id_set: set = set()

        # Corpus-level stats
        self._avgdl: float = 0.0
        self._df: Counter = Counter()  # document frequency per token
        self._N: int = 0

        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._docs = data.get("docs", [])
            self._id_set = {d["id"] for d in self._docs}
            self._avgdl = data.get("avgdl", 0.0)
            self._df = Counter(data.get("df", {}))
            self._N = data.get("N", len(self._docs))
        else:
            self._docs = []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "N": self._N,
            "avgdl": self._avgdl,
            "df": dict(self._df),
            "docs": self._docs,
        }
        # Atomic write via temp file + os.replace
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, str(self.path))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ):
        """Add documents to the index (skips duplicates by id)."""
        for doc_text, meta, doc_id in zip(documents, metadatas, ids):
            if doc_id in self._id_set:
                continue
            tokens = _tokenize(doc_text)
            self._docs.append({
                "id": doc_id,
                "text": doc_text,
                "metadata": meta,
                "tokens": tokens,
            })
            self._id_set.add(doc_id)

            # Update DF
            for tok in set(tokens):
                self._df[tok] += 1

        self._N = len(self._docs)
        if self._N > 0:
            self._avgdl = sum(len(d["tokens"]) for d in self._docs) / self._N
        self._save()

    # ------------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------------

    def delete_by_metadata(self, key: str, value: str):
        """Delete all docs whose metadata[key] == value."""
        remaining = []
        for d in self._docs:
            if d["metadata"].get(key) == value:
                self._id_set.discard(d["id"])
                for tok in set(d["tokens"]):
                    self._df[tok] = max(0, self._df[tok] - 1)
            else:
                remaining.append(d)
        self._docs = remaining
        self._N = len(self._docs)
        self._avgdl = (
            sum(len(d["tokens"]) for d in self._docs) / self._N
            if self._N > 0 else 0.0
        )
        self._save()

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        BM25-Okapi ranked search.

        ``where`` supports:
          - ``{"key": "val"}``              — exact match
          - ``{"$or": [filter, ...]}``      — logical OR
          - ``{"$and": [filter, ...]}``     — logical AND
        """
        query_tokens = _tokenize(query)
        if not query_tokens or self._N == 0:
            return []

        candidates = self._docs if where is None else [
            d for d in self._docs if self._match(d["metadata"], where)
        ]

        scored = []
        for doc in candidates:
            score = self._bm25_score(query_tokens, doc["tokens"])
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, doc in scored[:top_k]:
            results.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": score,
            })
        return results

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all stored documents (without token lists)."""
        return [
            {"id": d["id"], "text": d["text"], "metadata": d["metadata"]}
            for d in self._docs
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bm25_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        dl = len(doc_tokens)
        if dl == 0:
            return 0.0
        tf_map = Counter(doc_tokens)
        score = 0.0
        for qt in query_tokens:
            tf = tf_map.get(qt, 0)
            if tf == 0:
                continue
            df = self._df.get(qt, 0)
            idf = math.log((self._N - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / self._avgdl)
            score += idf * numerator / denominator
        return score

    @staticmethod
    def _match(metadata: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Evaluate a ChromaDB-style where filter against metadata."""
        for key, val in where.items():
            if key == "$or":
                if not any(BM25Index._match(metadata, clause) for clause in val):
                    return False
            elif key == "$and":
                if not all(BM25Index._match(metadata, clause) for clause in val):
                    return False
            else:
                if metadata.get(key) != val:
                    return False
        return True
