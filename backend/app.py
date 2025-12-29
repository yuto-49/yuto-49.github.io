import os
from typing import Literal, Optional, List
from pathlib import Path
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from crewai import Agent, Task, Crew

# Import RAG systems
try:
    from rag_system import CareerRAG
    RAG_ENABLED = True
except ImportError:
    print("[backend] Warning: RAG system not available. Install dependencies: pip install chromadb sentence-transformers")
    RAG_ENABLED = False

try:
    from pdf_rag import DualSourceRAG
    PDF_RAG_ENABLED = True
except ImportError:
    print("[backend] Warning: PDF RAG system not available. Install dependencies: pip install pypdf")
    PDF_RAG_ENABLED = False

# Load environment variables from .env file
load_dotenv()

# ============================================
# Environment & LLM setup
# ============================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    print("[backend] Warning: ANTHROPIC_API_KEY is not set. Set it in your environment before using the API.")

# Configure LLM for CrewAI using LiteLLM format
# CrewAI uses LiteLLM under the hood, so we specify the model with provider prefix
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY or ""

# For CrewAI, we pass the model string directly and it uses LiteLLM
# Use the format "anthropic/model-name" for Anthropic models
LLM_MODEL = "anthropic/claude-3-haiku-20240307"

# ============================================
# RAG System Initialization
# ============================================

# Initialize RAG system if available
rag_system = None
if RAG_ENABLED:
    try:
        print("[backend] Initializing RAG system...")
        rag_system = CareerRAG()
        print("[backend] RAG system ready!")
    except Exception as e:
        print(f"[backend] Warning: Could not initialize RAG system: {e}")
        rag_system = None

# Initialize PDF RAG system if available
pdf_rag_system = None
if PDF_RAG_ENABLED:
    try:
        print("[backend] Initializing PDF RAG system...")
        pdf_rag_system = DualSourceRAG()
        print("[backend] PDF RAG system ready!")
    except Exception as e:
        print(f"[backend] Warning: Could not initialize PDF RAG system: {e}")
        pdf_rag_system = None


# ============================================
# CrewAI Agent Definitions
# ============================================

def create_finance_agent():
    """Create a finance career advisor agent"""
    return Agent(
        role="Finance Career Advisor",
        goal="Design a realistic and inspiring finance career path for this candidate",
        backstory=(
            "You are a senior finance professional and career mentor with 15+ years of experience. "
            "You understand roles such as investment banking, equity research, FP&A, fintech, "
            "and quantitative analysis. You focus on clarity and practicality while being encouraging."
        ),
        llm=LLM_MODEL,
        verbose=False,
        allow_delegation=False
    )


def create_healthcare_agent():
    """Create a healthcare data & technology career advisor agent"""
    return Agent(
        role="Healthcare Data & Technology Career Advisor",
        goal="Map out how this candidate could impact healthcare using data, software, and AI",
        backstory=(
            "You are an expert in healthcare, digital health, bioinformatics, and medical AI. "
            "You help technical students see how their skills can translate into roles at "
            "hospitals, health-tech startups, research labs, and public health organizations."
        ),
        llm=LLM_MODEL,
        verbose=False,
        allow_delegation=False
    )


def create_consultant_agent():
    """Create a strategy & technology consultant career advisor agent"""
    return Agent(
        role="Strategy & Technology Consultant Career Advisor",
        goal="Explain how this candidate could become a consultant using their CS and analytical skills",
        backstory=(
            "You are a senior management consultant with experience in MBB-style firms and tech consulting. "
            "You specialize in helping students understand consulting work, cases, and long-term growth."
        ),
        llm=LLM_MODEL,
        verbose=False,
        allow_delegation=False
    )


# ============================================
# CrewAI Execution Logic
# ============================================

def run_agent_summary(agent_type: str, profile: str) -> str:
    """
    Uses CrewAI to generate a 'future you' career story for the candidate.
    """
    # Select the appropriate agent
    if agent_type == "finance":
        agent = create_finance_agent()
        domain = "finance"
    elif agent_type == "healthcare":
        agent = create_healthcare_agent()
        domain = "healthcare and health-tech"
    elif agent_type == "consultant":
        agent = create_consultant_agent()
        domain = "strategy and technology consulting"
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # Get RAG context if available
    rag_context = ""
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
            rag_context = ""

    # Create the task
    task = Task(
        description=f"""
        Analyze this candidate profile and create a detailed 'future you' career story in {domain}.

        Candidate Profile:
        {profile}
        {rag_context}

        Your response MUST include:
        1. 2-3 possible job titles they might hold in 3-5 years (cite specific examples from the job examples if available)
        2. The kind of companies or teams they might work with (reference actual companies from examples)
        3. What a typical week looks like (base on real responsibilities from job examples)
        4. The main skills and tools they would lean on from their current background
        5. 3-5 specific skill-building steps they should focus on next (courses, projects, internships, etc.)

        Use short paragraphs and bullet points. Keep the tone realistic but encouraging.
        When citing examples, mention the source (e.g., "At companies like X..." or "Similar to roles at Y...")
        """,
        expected_output="A structured, readable career story with specific job titles, company types, weekly activities, relevant skills, and an actionable development plan, citing real-world examples where applicable",
        agent=agent
    )

    # Create and run the crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False
    )

    result = crew.kickoff()
    return str(result)


def run_agent_chat(agent_type: str, profile: str, question: str) -> str:
    """
    Uses CrewAI agent to answer follow-up questions about the career path.
    """
    # Select the appropriate agent
    if agent_type == "finance":
        agent = create_finance_agent()
        domain = "finance"
    elif agent_type == "healthcare":
        agent = create_healthcare_agent()
        domain = "healthcare and health-tech"
    elif agent_type == "consultant":
        agent = create_consultant_agent()
        domain = "strategy and technology consulting"
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # Get RAG context if available
    rag_context = ""
    if rag_system:
        try:
            # Use the question for more relevant context retrieval
            rag_context = rag_system.get_context_for_agent(
                career_path=agent_type,
                user_profile=f"{profile}\nQuestion: {question}",
                top_k=2
            )
            if rag_context:
                rag_context = f"\n\nREAL-WORLD EXAMPLES:\n{rag_context}\n"
        except Exception as e:
            print(f"[backend] Warning: Could not fetch RAG context: {e}")
            rag_context = ""

    # Create the chat task
    task = Task(
        description=f"""
        You are mentoring a candidate in {domain}.

        Candidate Profile:
        {profile}
        {rag_context}

        The candidate is asking a follow-up question. Answer with clear, plain language,
        concrete examples from the {domain} context, and use short paragraphs or bullet points.
        If relevant examples are provided above, cite them in your answer.

        Question:
        {question}
        """,
        expected_output="A clear, helpful answer with concrete examples and actionable advice, citing real-world examples when relevant",
        agent=agent
    )

    # Create and run the crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False
    )

    result = crew.kickoff()
    return str(result)


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


app = FastAPI(title="Yuto Portfolio AI Backend", version="0.1.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Yuto Portfolio AI Backend is running"}


@app.get("/health")
def health():
    """Health check endpoint for Render"""
    return {"status": "healthy"}


@app.post("/api/agent", response_model=SummaryResponse | ChatResponse)
def agent_endpoint(payload: AgentRequest):
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
    except Exception as exc:  # noqa: BLE001
        print("[backend] Unhandled error:", exc)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")


# ============================================
# PDF Upload & Management Endpoints
# ============================================

@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    source_type: Literal["resume", "company_pdf", "project_pdf"] = Form(...),
    company: Optional[str] = Form(None)
):
    """
    Upload and index a PDF file.

    Args:
        file: PDF file to upload
        source_type: Type of document (resume, company_pdf, project_pdf)
        company: Optional company name (for company/project PDFs)

    Returns:
        Indexing result
    """
    print(f"[backend] Upload request received: {file.filename}, type: {source_type}, company: {company}")

    if not pdf_rag_system:
        raise HTTPException(
            status_code=500,
            detail="PDF RAG system is not available. Install dependencies: pip install pypdf python-multipart"
        )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Create uploads directory
        uploads_dir = Path(__file__).parent / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        print(f"[backend] Uploads directory: {uploads_dir}")

        # Save uploaded file
        file_path = uploads_dir / file.filename
        print(f"[backend] Saving file to: {file_path}")

        # Read file content into memory first
        content = await file.read()
        print(f"[backend] File size: {len(content)} bytes")

        # Write to disk
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        print(f"[backend] File saved successfully")

        # Index the PDF
        print(f"[backend] Indexing PDF...")
        result = pdf_rag_system.index_pdf(
            pdf_path=file_path,
            source_type=source_type,
            company=company
        )

        if "error" in result:
            print(f"[backend] Indexing error: {result['error']}")
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
    """
    List all indexed PDF documents.

    Returns:
        Documents grouped by source type
    """
    if not pdf_rag_system:
        raise HTTPException(
            status_code=500,
            detail="PDF RAG system is not available"
        )

    try:
        documents = pdf_rag_system.list_indexed_documents()
        return {
            "success": True,
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.delete("/api/delete-document/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document by its ID.

    Args:
        doc_id: Document ID to delete

    Returns:
        Deletion result
    """
    if not pdf_rag_system:
        raise HTTPException(
            status_code=500,
            detail="PDF RAG system is not available"
        )

    try:
        success = pdf_rag_system.delete_document(doc_id)

        if success:
            return {
                "success": True,
                "message": f"Document {doc_id} deleted successfully"
            }
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
    """
    Generate a personalized career path by matching resume with company needs.

    Args:
        target_role: Target role (e.g., "Data Scientist at Stripe")
        company: Optional company name for filtering

    Returns:
        Personalized career path with gap analysis and learning steps
    """
    if not pdf_rag_system:
        raise HTTPException(
            status_code=500,
            detail="PDF RAG system is not available"
        )

    try:
        # Get dual-source context
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

        # Create career path planning agent
        agent = Agent(
            role="Career Path Strategist",
            goal="Create personalized career development plans matching candidate skills to company needs",
            backstory=(
                "You are an expert career strategist who analyzes candidate backgrounds "
                "and company requirements to create actionable career development plans. "
                "You excel at identifying skill gaps and creating practical learning paths."
            ),
            llm=LLM_MODEL,
            verbose=False,
            allow_delegation=False
        )

        # Create the task
        task = Task(
            description=f"""
            Create a personalized career path plan for this target role: {payload.target_role}

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
            ...

            Be specific, practical, and actionable. Reference actual tools, courses, or projects mentioned in the documents.
            """,
            expected_output="A structured career path plan with skills match, gap analysis, and detailed learning steps",
            agent=agent
        )

        # Run the crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = str(crew.kickoff())

        # Parse the result (simple version - you can make this more sophisticated)
        return CareerPathResponse(
            career_path=result,
            skills_match=["Extracted from result"],  # TODO: Parse from result
            gaps=["Extracted from result"],  # TODO: Parse from result
            learning_steps=["Extracted from result"]  # TODO: Parse from result
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[backend] Error generating career path: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating career path: {str(e)}")


# Convenience for local dev:
#   cd backend
#   uvicorn app:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
