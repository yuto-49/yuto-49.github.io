"""
RAG System for Career Agents
Uses ChromaDB + SentenceTransformers for semantic search over job examples.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


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
        chroma_dir: Path = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the RAG system.

        Args:
            data_dir: Directory containing JSONL files with career examples
            chroma_dir: Directory for ChromaDB persistent storage
            embedding_model: SentenceTransformer model name
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "data" / "company_examples"

        if chroma_dir is None:
            chroma_dir = Path(__file__).parent / "data" / "chroma_db"

        self.data_dir = Path(data_dir)
        self.chroma_dir = Path(chroma_dir)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        print(f"📦 Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB
        print(f"🗄️  Initializing ChromaDB at: {self.chroma_dir}")
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Create collections for each career path
        self.collections = {}
        for career_path in ["finance", "healthcare", "consultant"]:
            self.collections[career_path] = self.client.get_or_create_collection(
                name=f"{career_path}_examples",
                metadata={"description": f"Job examples for {career_path} career path"}
            )

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval.
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def index_career_path(self, career_path: str) -> int:
        """
        Index all examples for a specific career path.

        Returns:
            Number of documents indexed
        """
        jsonl_file = self.data_dir / f"{career_path}.jsonl"

        if not jsonl_file.exists():
            print(f"⚠️  Warning: No data file found for {career_path} at {jsonl_file}")
            return 0

        print(f"\n📚 Indexing {career_path} examples from {jsonl_file}")

        collection = self.collections[career_path]
        documents = []
        metadatas = []
        ids = []

        doc_id = 0

        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    example = json.loads(line)

                    # Chunk the text
                    chunks = self._chunk_text(example['text'])

                    for chunk_idx, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({
                            "url": example['url'],
                            "title": example.get('title', 'Unknown'),
                            "author": example.get('author', ''),
                            "date": example.get('date', ''),
                            "chunk_idx": chunk_idx,
                            "total_chunks": len(chunks)
                        })
                        ids.append(f"{career_path}_{line_num}_{chunk_idx}")
                        doc_id += 1

                except json.JSONDecodeError as e:
                    print(f"   ✗ Error parsing line {line_num}: {e}")
                    continue

        if documents:
            # Add to ChromaDB
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            print(f"   ✓ Indexed {len(documents)} chunks from {jsonl_file}")
        else:
            print(f"   ⚠️  No documents found in {jsonl_file}")

        return len(documents)

    def index_all(self) -> Dict[str, int]:
        """
        Index all career paths.

        Returns:
            Dictionary mapping career_path -> number of chunks indexed
        """
        print("\n" + "="*60)
        print("🚀 Starting RAG Indexing")
        print("="*60)

        results = {}
        for career_path in ["finance", "healthcare", "consultant"]:
            count = self.index_career_path(career_path)
            results[career_path] = count

        print("\n" + "="*60)
        print("✅ Indexing Complete!")
        print("="*60)
        print(f"   Finance: {results.get('finance', 0)} chunks")
        print(f"   Healthcare: {results.get('healthcare', 0)} chunks")
        print(f"   Consultant: {results.get('consultant', 0)} chunks")
        print("="*60 + "\n")

        return results

    def search(
        self,
        career_path: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant examples for a given career path and query.

        Args:
            career_path: One of "finance", "healthcare", "consultant"
            query: Search query (e.g., user's skills and interests)
            top_k: Number of results to return

        Returns:
            List of relevant examples with metadata
        """
        if career_path not in self.collections:
            print(f"⚠️  Unknown career path: {career_path}")
            return []

        collection = self.collections[career_path]

        # Search
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )

        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for idx, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                formatted_results.append({
                    "rank": idx + 1,
                    "text": doc,
                    "url": metadata.get('url', ''),
                    "title": metadata.get('title', ''),
                    "relevance_score": 1 - distance,  # Convert distance to similarity
                    "metadata": metadata
                })

        return formatted_results

    def get_context_for_agent(
        self,
        career_path: str,
        user_profile: str,
        top_k: int = 3
    ) -> str:
        """
        Get formatted context for a CrewAI agent.

        Args:
            career_path: Career path
            user_profile: User's profile/resume text
            top_k: Number of examples to retrieve

        Returns:
            Formatted context string
        """
        results = self.search(career_path, user_profile, top_k)

        if not results:
            return ""

        context_parts = ["Here are some relevant real-world job examples:\n"]

        for result in results:
            context_parts.append(f"\n--- Example {result['rank']} (from {result['title']}) ---")
            context_parts.append(result['text'])
            context_parts.append(f"Source: {result['url']}\n")

        return "\n".join(context_parts)


# ============================================
# CLI Entry Point
# ============================================

def main():
    """
    Build and index the RAG system.
    """
    rag = CareerRAG()

    # Index all data
    rag.index_all()

    # Test search
    print("\n🧪 Testing search functionality...\n")

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
