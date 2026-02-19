"""
Dual-Source RAG System for Resume + Company PDFs
Indexes both user resumes and company/project documents for career path matching.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

from pypdf import PdfReader
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


# ============================================
# PDF Processing
# ============================================

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from a PDF file.
    """
    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            text_parts.append(text)

    return "\n\n".join(text_parts)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    """
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
    """
    RAG system that handles both resume and company/project PDFs.
    """

    def __init__(
        self,
        chroma_dir: Path = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize dual-source RAG system.
        """
        if chroma_dir is None:
            chroma_dir = Path(__file__).parent / "data" / "dual_source_chroma"

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

        # Create collection for all documents (with source metadata)
        self.collection = self.client.get_or_create_collection(
            name="career_documents",
            metadata={"description": "Resume and company/project documents"}
        )

    def index_pdf(
        self,
        pdf_path: Path,
        source_type: Literal["resume", "company_pdf", "project_pdf"],
        company: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index a PDF with source type metadata.

        Args:
            pdf_path: Path to PDF file
            source_type: Type of document ("resume", "company_pdf", "project_pdf")
            company: Optional company name for filtering
            metadata: Additional metadata

        Returns:
            Indexing result with chunk count
        """
        print(f"\n📄 Indexing {source_type}: {pdf_path.name}")

        # Extract text
        text = extract_text_from_pdf(pdf_path)

        if not text.strip():
            return {"error": "No text extracted from PDF", "chunks": 0}

        # Chunk text
        chunks = chunk_text(text, chunk_size=500, overlap=50)

        # Generate document ID
        doc_id = hashlib.md5(pdf_path.name.encode()).hexdigest()[:8]

        # Prepare metadata for each chunk
        documents = []
        metadatas = []
        ids = []

        base_metadata = {
            "source_type": source_type,
            "filename": pdf_path.name,
            "doc_id": doc_id,
            "uploaded_at": datetime.now().isoformat(),
            "total_chunks": len(chunks)
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

        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"   ✓ Indexed {len(chunks)} chunks from {pdf_path.name}")

        return {
            "doc_id": doc_id,
            "filename": pdf_path.name,
            "source_type": source_type,
            "chunks": len(chunks),
            "company": company
        }

    def retrieve_from_resume(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks from resume documents.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"source_type": "resume"}
        )

        return self._format_results(results)

    def retrieve_from_company(
        self,
        query: str,
        company: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks from company/project documents.
        """
        where_filter = {
            "$or": [
                {"source_type": "company_pdf"},
                {"source_type": "project_pdf"}
            ]
        }

        if company:
            where_filter = {
                "$and": [
                    where_filter,
                    {"company": company}
                ]
            }

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )

        return self._format_results(results)

    def dual_retrieve(
        self,
        query: str,
        company: Optional[str] = None,
        resume_k: int = 3,
        company_k: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve from BOTH resume and company sources.

        Returns:
            {
                "resume": [...],  # User's skills/experience
                "company": [...]  # Company's needs/projects
            }
        """
        return {
            "resume": self.retrieve_from_resume(query, top_k=resume_k),
            "company": self.retrieve_from_company(query, company, top_k=company_k)
        }

    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """
        Format ChromaDB results into a list of dicts.
        """
        formatted = []

        if not results['documents'] or not results['documents'][0]:
            return formatted

        for idx, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            formatted.append({
                "rank": idx + 1,
                "text": doc,
                "source_type": metadata.get('source_type'),
                "filename": metadata.get('filename'),
                "company": metadata.get('company'),
                "relevance_score": 1 - distance,
                "metadata": metadata
            })

        return formatted

    def get_career_path_context(
        self,
        target_role: str,
        company: Optional[str] = None,
        resume_k: int = 5,
        company_k: int = 5
    ) -> str:
        """
        Get formatted context for career path planning.

        Args:
            target_role: The role the user is targeting (e.g., "Data Scientist at Stripe")
            company: Optional company name for filtering
            resume_k: Number of resume chunks to retrieve
            company_k: Number of company chunks to retrieve

        Returns:
            Formatted context string for the agent
        """
        # Dual retrieval
        results = self.dual_retrieve(
            query=target_role,
            company=company,
            resume_k=resume_k,
            company_k=company_k
        )

        # Format context
        context_parts = []

        # Resume section
        if results['resume']:
            context_parts.append("=== YOUR BACKGROUND (from resume) ===\n")
            for r in results['resume']:
                context_parts.append(f"• {r['text']}\n")

        # Company section
        if results['company']:
            context_parts.append("\n=== COMPANY/PROJECT REQUIREMENTS ===\n")
            for r in results['company']:
                source = f" ({r['company']})" if r.get('company') else ""
                context_parts.append(f"• {r['text']}{source}\n")

        return "\n".join(context_parts)

    def list_indexed_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all indexed documents grouped by source type.
        """
        all_data = self.collection.get()

        documents = {
            "resume": [],
            "company_pdf": [],
            "project_pdf": []
        }

        seen_docs = set()

        if all_data['metadatas']:
            for metadata in all_data['metadatas']:
                doc_id = metadata.get('doc_id')

                if doc_id not in seen_docs:
                    source_type = metadata.get('source_type')
                    if source_type in documents:
                        documents[source_type].append({
                            "doc_id": doc_id,
                            "filename": metadata.get('filename'),
                            "company": metadata.get('company'),
                            "uploaded_at": metadata.get('uploaded_at'),
                            "total_chunks": metadata.get('total_chunks')
                        })
                    seen_docs.add(doc_id)

        return documents

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete all chunks of a document by doc_id.
        """
        try:
            # Get all IDs for this document
            all_data = self.collection.get()

            ids_to_delete = [
                id for id, meta in zip(all_data['ids'], all_data['metadatas'])
                if meta.get('doc_id') == doc_id
            ]

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                print(f"✓ Deleted {len(ids_to_delete)} chunks for doc_id: {doc_id}")
                return True

            return False
        except Exception as e:
            print(f"✗ Error deleting document: {e}")
            return False


# ============================================
# CLI Testing
# ============================================

if __name__ == "__main__":
    # Example usage
    rag = DualSourceRAG()

    print("\n" + "="*60)
    print("Dual-Source RAG System Initialized")
    print("="*60)

    # List current documents
    docs = rag.list_indexed_documents()
    print(f"\nIndexed documents:")
    print(f"  Resumes: {len(docs['resume'])}")
    print(f"  Company PDFs: {len(docs['company_pdf'])}")
    print(f"  Project PDFs: {len(docs['project_pdf'])}")
