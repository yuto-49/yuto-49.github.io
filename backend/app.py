import os
from typing import Literal, Optional, List
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# ============================================
# Lazy imports for heavy dependencies
# LangChain and RAG are loaded on first use, not at startup,
# so uvicorn can bind the port immediately on Render.
# ============================================

LANGCHAIN_AVAILABLE = None  # None = not yet checked
RAG_ENABLED = None
PDF_RAG_ENABLED = None

_lazy_modules = {}


def _ensure_langchain():
    """Lazy-load LangChain on first use."""
    global LANGCHAIN_AVAILABLE, _lazy_modules
    if LANGCHAIN_AVAILABLE is not None:
        return LANGCHAIN_AVAILABLE
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import SystemMessage, HumanMessage
        _lazy_modules["ChatAnthropic"] = ChatAnthropic
        _lazy_modules["SystemMessage"] = SystemMessage
        _lazy_modules["HumanMessage"] = HumanMessage
        LANGCHAIN_AVAILABLE = True
        print("[backend] LangChain loaded successfully.")
    except ImportError:
        print("[backend] Warning: LangChain not available. AI agent features will be disabled.")
        LANGCHAIN_AVAILABLE = False
    return LANGCHAIN_AVAILABLE


def _ensure_rag():
    """Lazy-load RAG systems on first use."""
    global RAG_ENABLED, PDF_RAG_ENABLED
    if RAG_ENABLED is not None:
        return
    try:
        from rag_system import CareerRAG
        _lazy_modules["CareerRAG"] = CareerRAG
        RAG_ENABLED = True
    except ImportError:
        print("[backend] Warning: RAG system not available.")
        RAG_ENABLED = False
    try:
        from pdf_rag import DualSourceRAG
        _lazy_modules["DualSourceRAG"] = DualSourceRAG
        PDF_RAG_ENABLED = True
    except ImportError:
        print("[backend] Warning: PDF RAG system not available.")
        PDF_RAG_ENABLED = False

# ============================================
# Environment & LLM setup
# ============================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if ANTHROPIC_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

# Model to use — Claude 3 Haiku is fast and affordable
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-haiku-20240307")

if not ANTHROPIC_API_KEY:
    print("[backend] Warning: ANTHROPIC_API_KEY is not set. AI agent features will fail.")
else:
    print(f"[backend] Using model: {LLM_MODEL}")


# ============================================
# LLM instance (lazy-loaded)
# ============================================

_llm_instance = None


def get_llm():
    """Get or create the LangChain ChatAnthropic instance."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    if not _ensure_langchain():
        return None
    ChatAnthropic = _lazy_modules["ChatAnthropic"]
    _llm_instance = ChatAnthropic(
        model=LLM_MODEL,
        temperature=0.7,
        max_tokens=2048,
    )
    print(f"[backend] LLM initialized: {LLM_MODEL}")
    return _llm_instance


# ============================================
# RAG System Initialization (Lazy Loading)
# ============================================

_rag_system_instance = None
_pdf_rag_system_instance = None


def get_rag_system():
    """Lazy-load RAG system on first use."""
    global _rag_system_instance
    _ensure_rag()
    if _rag_system_instance is None and RAG_ENABLED:
        try:
            print("[backend] Loading RAG system...")
            CareerRAG = _lazy_modules.get("CareerRAG")
            if CareerRAG:
                _rag_system_instance = CareerRAG()
                print("[backend] RAG system ready!")
        except Exception as e:
            print(f"[backend] Warning: Could not initialize RAG system: {e}")
            _rag_system_instance = None
    return _rag_system_instance


def get_pdf_rag_system():
    """Lazy-load PDF RAG system on first use."""
    global _pdf_rag_system_instance
    _ensure_rag()
    if _pdf_rag_system_instance is None and PDF_RAG_ENABLED:
        try:
            print("[backend] Loading PDF RAG system...")
            DualSourceRAG = _lazy_modules.get("DualSourceRAG")
            if DualSourceRAG:
                _pdf_rag_system_instance = DualSourceRAG()
                print("[backend] PDF RAG system ready!")
        except Exception as e:
            print(f"[backend] Warning: Could not initialize PDF RAG system: {e}")
            _pdf_rag_system_instance = None
    return _pdf_rag_system_instance


# ============================================
# Agent System Prompts
# ============================================

AGENT_SYSTEM_PROMPTS = {
    "finance": (
        "You are a senior finance career advisor with 15+ years of experience. "
        "You understand roles such as investment banking, equity research, FP&A, fintech, "
        "and quantitative analysis. You are mentoring a candidate who wants "
        "to explore a career in finance. Analyze their uploaded resume carefully and base all advice "
        "on THEIR specific background, skills, and experience — not on any other person. "
        "Be clear, practical, and encouraging. "
        "Use short paragraphs and bullet points. Cite real-world examples when available."
    ),
    "healthcare": (
        "You are an expert in healthcare technology, digital health, bioinformatics, and medical AI. "
        "You help candidates see how their skills translate into roles at hospitals, "
        "health-tech startups, research labs, and public health organizations. "
        "Analyze their uploaded resume carefully and base all advice "
        "on THEIR specific background, skills, and experience — not on any other person. "
        "Be specific about roles, tools, and career paths. Use short paragraphs and bullet points."
    ),
    "consultant": (
        "You are a senior management consultant with experience in MBB-style firms and tech consulting. "
        "You specialize in helping candidates understand consulting work, case interviews, and long-term growth. "
        "Analyze their uploaded resume carefully and base all advice "
        "on THEIR specific background, skills, and experience — not on any other person. "
        "Be realistic about the work, specific about skills needed, and encouraging about their potential."
    ),
}

DOMAIN_NAMES = {
    "finance": "finance",
    "healthcare": "healthcare and health-tech",
    "consultant": "strategy and technology consulting",
}


# ============================================
# Agent Execution Logic (LangChain)
# ============================================

def run_agent_summary(agent_type: str, profile: str) -> str:
    """
    Uses LangChain ChatAnthropic to generate a 'future you' career story.
    """
    llm = get_llm()
    if llm is None:
        raise ValueError("LangChain is not available. Please install: pip install langchain-anthropic")

    SystemMessage = _lazy_modules["SystemMessage"]
    HumanMessage = _lazy_modules["HumanMessage"]

    system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type)
    domain = DOMAIN_NAMES.get(agent_type)
    if not system_prompt:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # Get RAG context if available
    rag_context = ""
    rag_system = get_rag_system()
    if rag_system:
        try:
            rag_context = rag_system.get_context_for_agent(
                career_path=agent_type,
                user_profile=profile,
                top_k=3
            )
            if rag_context:
                rag_context = f"\n\nREAL-WORLD JOB EXAMPLES:\n{rag_context}\n"
        except Exception as e:
            print(f"[backend] Warning: Could not fetch RAG context: {e}")

    user_prompt = f"""Analyze the following candidate's resume and create a detailed 'future you' career story in {domain}.
IMPORTANT: Base your entire analysis on the resume content below. Use the candidate's actual name, skills, experience, and education from their resume. Do NOT reference any other person.

Candidate Resume:
{profile}
{rag_context}

Your response MUST include:
1. Address the candidate by their name (extracted from the resume)
2. 2-3 possible job titles they might hold in 3-5 years (cite specific examples from job examples if available)
3. The kind of companies or teams they might work with (reference actual companies from examples)
4. What a typical week looks like (base on real responsibilities from job examples)
5. The main skills and tools they would lean on from their current background as shown in the resume
6. 3-5 specific skill-building steps they should focus on next (courses, projects, internships, etc.)

Use short paragraphs and bullet points. Keep the tone realistic but encouraging.
When citing examples, mention the source (e.g., "At companies like X..." or "Similar to roles at Y...")."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    return response.content


def run_agent_chat(agent_type: str, profile: str, question: str) -> str:
    """
    Uses LangChain ChatAnthropic to answer follow-up questions about the career path.
    """
    llm = get_llm()
    if llm is None:
        raise ValueError("LangChain is not available. Please install: pip install langchain-anthropic")

    SystemMessage = _lazy_modules["SystemMessage"]
    HumanMessage = _lazy_modules["HumanMessage"]

    system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type)
    domain = DOMAIN_NAMES.get(agent_type)
    if not system_prompt:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # Get RAG context if available
    rag_context = ""
    rag_system = get_rag_system()
    if rag_system:
        try:
            rag_context = rag_system.get_context_for_agent(
                career_path=agent_type,
                user_profile=f"{profile}\nQuestion: {question}",
                top_k=2
            )
            if rag_context:
                rag_context = f"\n\nREAL-WORLD EXAMPLES:\n{rag_context}\n"
        except Exception as e:
            print(f"[backend] Warning: Could not fetch RAG context: {e}")

    user_prompt = f"""You are mentoring a candidate in {domain}.
IMPORTANT: Base your entire response on the candidate's resume below. Use their actual name, skills, and experience. Do NOT reference any other person.

Candidate Resume:
{profile}
{rag_context}

The candidate is asking a follow-up question. Answer with clear, plain language,
concrete examples from {domain}, and use short paragraphs or bullet points.
If relevant examples are provided above, cite them in your answer.

Question:
{question}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    return response.content


def run_career_path_agent(context: str, target_role: str) -> str:
    """
    Uses LangChain ChatAnthropic to generate a career path plan from dual-source RAG context.
    """
    llm = get_llm()
    if llm is None:
        raise ValueError("LangChain is not available. Please install: pip install langchain-anthropic")

    SystemMessage = _lazy_modules["SystemMessage"]
    HumanMessage = _lazy_modules["HumanMessage"]

    system_prompt = (
        "You are an expert career strategist who analyzes candidate backgrounds "
        "and company requirements to create actionable career development plans. "
        "You excel at identifying skill gaps and creating practical learning paths. "
        "Be specific, practical, and actionable. Reference actual tools, courses, or projects."
    )

    user_prompt = f"""Create a personalized career path plan for this target role: {target_role}

CONTEXT (from uploaded documents):
{context}

Your response MUST include:
1. SKILLS MATCH: List 3-5 skills/experiences from the resume that align with company needs
2. GAP ANALYSIS: Identify 3-5 specific gaps between current skills and role requirements
3. LEARNING PATH: Provide 5-7 concrete, actionable steps to bridge the gaps:
   - Specific courses, certifications, or learning resources
   - Hands-on projects to build
   - Timeline estimates (e.g., "2-3 months")
   - Which skills each step develops

Format your response clearly with sections:
## Skills Match
- [skill 1]
- [skill 2]
...

## Gaps to Address
- [gap 1]
- [gap 2]
...

## Learning Path
1. [Step 1] (Timeline: X months) - Develops: [skills]
2. [Step 2] ...
..."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    return response.content


# ============================================
# FastAPI app & schema
# ============================================

class AgentRequest(BaseModel):
    mode: Literal["summary", "chat"]
    agentType: Literal["finance", "healthcare", "consultant"]
    profile: str
    question: Optional[str] = None


class SummaryResponse(BaseModel):
    summary: str


class ChatResponse(BaseModel):
    answer: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    print("=" * 50)
    print("Yuto Portfolio AI Backend started successfully!")
    print(f"   Model: {LLM_MODEL}")
    print(f"   LangChain: lazy-loaded on first request")
    print(f"   RAG: lazy-loaded on first request (BM25)")
    print("=" * 50)
    yield
    print("Shutting down Yuto Portfolio AI Backend...")


app = FastAPI(title="Yuto Portfolio AI Backend", version="0.2.0", lifespan=lifespan)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend static files directory (one level up from backend/)
FRONTEND_DIR = Path(__file__).parent.parent


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    """Health check endpoint for Render"""
    return {"status": "healthy"}


@app.post("/api/agent", response_model=SummaryResponse | ChatResponse)
def agent_endpoint(payload: AgentRequest):
    if not _ensure_langchain():
        raise HTTPException(
            status_code=503,
            detail="LangChain is not available. Please install: pip install langchain-anthropic",
        )

    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not configured on the server.",
        )

    try:
        if payload.mode == "summary":
            text = run_agent_summary(payload.agentType, payload.profile)
            return SummaryResponse(summary=text)

        if payload.mode == "chat":
            if not payload.question:
                raise HTTPException(status_code=400, detail="question is required for mode='chat'")
            text = run_agent_chat(payload.agentType, payload.profile, payload.question)
            return ChatResponse(answer=text)

        raise HTTPException(status_code=400, detail="Unsupported mode.")
    except HTTPException:
        raise
    except Exception as exc:
        print("[backend] Unhandled error:", exc)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")


@app.post("/api/agent/upload-resume")
async def agent_upload_resume(
    file: UploadFile = File(...),
):
    """Upload a resume PDF and return extracted text for the AI career agent."""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        uploads_dir = Path(__file__).parent / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        file_path = uploads_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Extract text from the PDF
        try:
            from pdf_rag import extract_text_from_pdf
        except ImportError:
            from backend.pdf_rag import extract_text_from_pdf

        resume_text = extract_text_from_pdf(file_path)

        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF")

        return {
            "success": True,
            "filename": file.filename,
            "resumeText": resume_text,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[backend] Error processing resume: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


# ============================================
# PDF Upload & Management Endpoints
# ============================================

@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    source_type: Literal["resume", "company_pdf", "project_pdf"] = Form(...),
    company: Optional[str] = Form(None)
):
    """Upload and index a PDF file."""
    print(f"[backend] Upload request received: {file.filename}, type: {source_type}, company: {company}")

    pdf_rag_system = get_pdf_rag_system()
    if not pdf_rag_system:
        raise HTTPException(
            status_code=500,
            detail="PDF RAG system is not available. Install dependencies: pip install pypdf python-multipart"
        )

    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        uploads_dir = Path(__file__).parent / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        file_path = uploads_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        result = pdf_rag_system.index_pdf(
            pdf_path=file_path,
            source_type=source_type,
            company=company
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        print(f"[backend] Successfully indexed {file.filename}")
        return {
            "success": True,
            "message": f"Successfully indexed {file.filename}",
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[backend] Error uploading PDF: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.get("/api/list-documents")
async def list_documents():
    """List all indexed PDF documents."""
    pdf_rag_system = get_pdf_rag_system()
    if not pdf_rag_system:
        return {"success": True, "documents": {"resume": [], "company_pdf": [], "project_pdf": []}}

    try:
        documents = pdf_rag_system.list_indexed_documents()
        return {"success": True, "documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.delete("/api/delete-document/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by its ID."""
    pdf_rag_system = get_pdf_rag_system()
    if not pdf_rag_system:
        raise HTTPException(status_code=500, detail="PDF RAG system is not available")

    try:
        success = pdf_rag_system.delete_document(doc_id)
        if success:
            return {"success": True, "message": f"Document {doc_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


class CareerPathRequest(BaseModel):
    target_role: str
    company: Optional[str] = None


class CareerPathResponse(BaseModel):
    career_path: str
    skills_match: List[str]
    gaps: List[str]
    learning_steps: List[str]


@app.post("/api/career-path", response_model=CareerPathResponse)
async def generate_career_path(payload: CareerPathRequest):
    """Generate a personalized career path by matching resume with company needs."""
    if not _ensure_langchain():
        raise HTTPException(
            status_code=503,
            detail="LangChain is not available. Please install: pip install langchain-anthropic",
        )

    pdf_rag_system = get_pdf_rag_system()
    if not pdf_rag_system:
        raise HTTPException(status_code=500, detail="PDF RAG system is not available")

    try:
        context = pdf_rag_system.get_career_path_context(
            target_role=payload.target_role,
            company=payload.company,
            resume_k=5,
            company_k=5
        )

        if not context.strip():
            raise HTTPException(
                status_code=400,
                detail="No resume or company documents found. Please upload PDFs first."
            )

        result = run_career_path_agent(context, payload.target_role)

        return CareerPathResponse(
            career_path=result,
            skills_match=["Extracted from result"],
            gaps=["Extracted from result"],
            learning_steps=["Extracted from result"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[backend] Error generating career path: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating career path: {str(e)}")


# ============================================
# Static Frontend Serving
# Must be AFTER all API routes.
# ============================================

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    """Serve the frontend index.html"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"status": "ok", "message": "Yuto Portfolio AI Backend is running"}


@app.get("/resume.html")
def serve_resume():
    """Serve resume page"""
    return FileResponse(FRONTEND_DIR / "resume.html")


if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")


@app.get("/{filename:path}")
def serve_static(filename: str):
    """Catch-all: serve static files from the frontend directory"""
    file_path = FRONTEND_DIR / filename
    if file_path.is_file() and file_path.suffix in {".css", ".js", ".html", ".png", ".jpg", ".ico", ".svg", ".pdf"}:
        return FileResponse(file_path)
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
