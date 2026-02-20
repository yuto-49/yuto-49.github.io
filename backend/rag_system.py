"""
RAG System for Career Agents
Uses a lightweight BM25 keyword index (pure Python, no external deps).
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from bm25_engine import BM25Index


# ============================================
# RAG Configuration
# ============================================

class CareerRAG:
    """
    Retrieval-Augmented Generation system for career examples.
    """

    def __init__(
        self,
        data_dir: Path = None,
        index_dir: Path = None,
    ):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data" / "company_examples"

        if index_dir is None:
            index_dir = Path(__file__).parent / "data" / "bm25_index"

        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        print(f"[RAG] Initializing BM25 indexes at: {self.index_dir}")

        # One BM25Index per career path
        self.indexes: Dict[str, BM25Index] = {}
        for career_path in ["finance", "healthcare", "consultant"]:
            self.indexes[career_path] = BM25Index(
                self.index_dir / f"{career_path}_index.json"
            )

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better retrieval."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def index_career_path(self, career_path: str) -> int:
        """Index all examples for a specific career path."""
        jsonl_file = self.data_dir / f"{career_path}.jsonl"

        if not jsonl_file.exists():
            print(f"Warning: No data file found for {career_path} at {jsonl_file}")
            return 0

        print(f"\nIndexing {career_path} examples from {jsonl_file}")

        index = self.indexes[career_path]
        documents = []
        metadatas = []
        ids = []

        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line)
                    chunks = self._chunk_text(example["text"])

                    for chunk_idx, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({
                            "url": example["url"],
                            "title": example.get("title", "Unknown"),
                            "author": example.get("author", ""),
                            "date": example.get("date", ""),
                            "chunk_idx": chunk_idx,
                            "total_chunks": len(chunks),
                        })
                        ids.append(f"{career_path}_{line_num}_{chunk_idx}")

                except json.JSONDecodeError as e:
                    print(f"   Error parsing line {line_num}: {e}")
                    continue

        if documents:
            index.add_documents(documents=documents, metadatas=metadatas, ids=ids)
            print(f"   Indexed {len(documents)} chunks from {jsonl_file}")
        else:
            print(f"   Warning: No documents found in {jsonl_file}")

        return len(documents)

    def index_all(self) -> Dict[str, int]:
        """Index all career paths."""
        print("\n" + "=" * 60)
        print("Starting RAG Indexing (BM25)")
        print("=" * 60)

        results = {}
        for career_path in ["finance", "healthcare", "consultant"]:
            count = self.index_career_path(career_path)
            results[career_path] = count

        print("\n" + "=" * 60)
        print("Indexing Complete!")
        print("=" * 60)
        print(f"   Finance: {results.get('finance', 0)} chunks")
        print(f"   Healthcare: {results.get('healthcare', 0)} chunks")
        print(f"   Consultant: {results.get('consultant', 0)} chunks")
        print("=" * 60 + "\n")

        return results

    def search(
        self,
        career_path: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for relevant examples for a given career path and query."""
        if career_path not in self.indexes:
            print(f"Warning: Unknown career path: {career_path}")
            return []

        index = self.indexes[career_path]
        results = index.search(query=query, top_k=top_k)

        formatted_results = []
        for idx, r in enumerate(results):
            formatted_results.append({
                "rank": idx + 1,
                "text": r["text"],
                "url": r["metadata"].get("url", ""),
                "title": r["metadata"].get("title", ""),
                "relevance_score": r["score"],
                "metadata": r["metadata"],
            })

        return formatted_results

    def get_context_for_agent(
        self,
        career_path: str,
        user_profile: str,
        top_k: int = 3,
    ) -> str:
        """Get formatted context for an LLM agent."""
        results = self.search(career_path, user_profile, top_k)

        if not results:
            return ""

        context_parts = ["Here are some relevant real-world job examples:\n"]
        for result in results:
            context_parts.append(f"\n--- Example {result['rank']} (from {result['title']}) ---")
            context_parts.append(result["text"])
            context_parts.append(f"Source: {result['url']}\n")

        return "\n".join(context_parts)


# ============================================
# CLI Entry Point
# ============================================

def main():
    """Build and index the RAG system."""
    rag = CareerRAG()
    rag.index_all()

    print("\nTesting search functionality...\n")
    test_query = "Python data analysis machine learning experience"

    for career_path in ["finance", "healthcare", "consultant"]:
        print(f"\n--- Searching {career_path} ---")
        results = rag.search(career_path, test_query, top_k=2)

        for result in results:
            print(f"\n  [{result['rank']}] {result['title']}")
            print(f"      Relevance: {result['relevance_score']:.3f}")
            print(f"      {result['text'][:200]}...")


if __name__ == "__main__":
    main()
