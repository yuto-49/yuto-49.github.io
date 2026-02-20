"""
Dual-Source RAG System for Resume + Company PDFs
Indexes both user resumes and company/project documents for career path matching.
Uses lightweight BM25 keyword search instead of ChromaDB.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

from pypdf import PdfReader

from bm25_engine import BM25Index


# ============================================
# PDF Processing
# ============================================

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            text_parts.append(text)
    return "\n\n".join(text_parts)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


# ============================================
# Dual-Source RAG System
# ============================================

class DualSourceRAG:
    """RAG system that handles both resume and company/project PDFs."""

    def __init__(self, index_dir: Path = None):
        if index_dir is None:
            index_dir = Path(__file__).parent / "data" / "bm25_pdf_index"

        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        print(f"[PDF-RAG] Initializing BM25 index at: {self.index_dir}")
        self.index = BM25Index(self.index_dir / "career_documents_index.json")

    def index_pdf(
        self,
        pdf_path: Path,
        source_type: Literal["resume", "company_pdf", "project_pdf"],
        company: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Index a PDF with source type metadata."""
        print(f"\nIndexing {source_type}: {pdf_path.name}")

        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            return {"error": "No text extracted from PDF", "chunks": 0}

        chunks = chunk_text(text, chunk_size=500, overlap=50)
        doc_id = hashlib.md5(pdf_path.name.encode()).hexdigest()[:8]

        documents = []
        metadatas = []
        ids = []

        base_metadata = {
            "source_type": source_type,
            "filename": pdf_path.name,
            "doc_id": doc_id,
            "uploaded_at": datetime.now().isoformat(),
            "total_chunks": len(chunks),
        }
        if company:
            base_metadata["company"] = company
        if metadata:
            base_metadata.update(metadata)

        for idx, chunk in enumerate(chunks):
            documents.append(chunk)
            chunk_metadata = base_metadata.copy()
            chunk_metadata["chunk_idx"] = idx
            metadatas.append(chunk_metadata)
            ids.append(f"{doc_id}_{idx}")

        self.index.add_documents(documents=documents, metadatas=metadatas, ids=ids)
        print(f"   Indexed {len(chunks)} chunks from {pdf_path.name}")

        return {
            "doc_id": doc_id,
            "filename": pdf_path.name,
            "source_type": source_type,
            "chunks": len(chunks),
            "company": company,
        }

    def retrieve_from_resume(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from resume documents."""
        results = self.index.search(
            query=query, top_k=top_k, where={"source_type": "resume"}
        )
        return self._format_results(results)

    def retrieve_from_company(
        self, query: str, company: Optional[str] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from company/project documents."""
        where_filter: Dict[str, Any] = {
            "$or": [
                {"source_type": "company_pdf"},
                {"source_type": "project_pdf"},
            ]
        }
        if company:
            where_filter = {"$and": [where_filter, {"company": company}]}

        results = self.index.search(query=query, top_k=top_k, where=where_filter)
        return self._format_results(results)

    def dual_retrieve(
        self,
        query: str,
        company: Optional[str] = None,
        resume_k: int = 3,
        company_k: int = 3,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve from BOTH resume and company sources."""
        return {
            "resume": self.retrieve_from_resume(query, top_k=resume_k),
            "company": self.retrieve_from_company(query, company, top_k=company_k),
        }

    def _format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format BM25 results into the expected list of dicts."""
        formatted = []
        for idx, r in enumerate(results):
            formatted.append({
                "rank": idx + 1,
                "text": r["text"],
                "source_type": r["metadata"].get("source_type"),
                "filename": r["metadata"].get("filename"),
                "company": r["metadata"].get("company"),
                "relevance_score": r["score"],
                "metadata": r["metadata"],
            })
        return formatted

    def get_career_path_context(
        self,
        target_role: str,
        company: Optional[str] = None,
        resume_k: int = 5,
        company_k: int = 5,
    ) -> str:
        """Get formatted context for career path planning."""
        results = self.dual_retrieve(
            query=target_role, company=company,
            resume_k=resume_k, company_k=company_k,
        )

        context_parts = []

        if results["resume"]:
            context_parts.append("=== YOUR BACKGROUND (from resume) ===\n")
            for r in results["resume"]:
                context_parts.append(f"• {r['text']}\n")

        if results["company"]:
            context_parts.append("\n=== COMPANY/PROJECT REQUIREMENTS ===\n")
            for r in results["company"]:
                source = f" ({r['company']})" if r.get("company") else ""
                context_parts.append(f"• {r['text']}{source}\n")

        return "\n".join(context_parts)

    def list_indexed_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all indexed documents grouped by source type."""
        all_data = self.index.get_all()

        documents: Dict[str, List[Dict[str, Any]]] = {
            "resume": [],
            "company_pdf": [],
            "project_pdf": [],
        }
        seen_docs: set = set()

        for item in all_data:
            meta = item["metadata"]
            doc_id = meta.get("doc_id")
            if doc_id not in seen_docs:
                source_type = meta.get("source_type")
                if source_type in documents:
                    documents[source_type].append({
                        "doc_id": doc_id,
                        "filename": meta.get("filename"),
                        "company": meta.get("company"),
                        "uploaded_at": meta.get("uploaded_at"),
                        "total_chunks": meta.get("total_chunks"),
                    })
                seen_docs.add(doc_id)

        return documents

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks of a document by doc_id."""
        try:
            self.index.delete_by_metadata("doc_id", doc_id)
            print(f"Deleted chunks for doc_id: {doc_id}")
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False


# ============================================
# CLI Testing
# ============================================

if __name__ == "__main__":
    rag = DualSourceRAG()
    print("\n" + "=" * 60)
    print("Dual-Source RAG System Initialized")
    print("=" * 60)
    docs = rag.list_indexed_documents()
    print(f"\nIndexed documents:")
    print(f"  Resumes: {len(docs['resume'])}")
    print(f"  Company PDFs: {len(docs['company_pdf'])}")
    print(f"  Project PDFs: {len(docs['project_pdf'])}")
