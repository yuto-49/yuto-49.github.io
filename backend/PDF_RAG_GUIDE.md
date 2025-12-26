# Dual-Source PDF RAG System

Upload **your resume** + **company/project PDFs** → Get **personalized career paths** with gap analysis and learning plans!

## 🎯 What This Does

```
Your Resume PDF          Company/Project PDFs
     ↓                          ↓
  [Your Skills]         [Their Requirements]
     ↓                          ↓
        ← Dual Retrieval →
                ↓
        [Career Path Agent]
                ↓
     ┌──────────────────────┐
     │ Skills Match         │
     │ Gap Analysis         │
     │ Learning Path        │
     │ Timeline & Projects  │
     └──────────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
source ../venv/bin/activate
pip install -r ../requirements.txt
```

### 2. Start Backend

```bash
python app.py
```

### 3. Upload PDFs via API

#### Upload Your Resume:

```bash
curl -X POST http://localhost:8000/api/upload-pdf \
  -F "file=@/path/to/your_resume.pdf" \
  -F "source_type=resume"
```

#### Upload Company/Project PDF:

```bash
curl -X POST http://localhost:8000/api/upload-pdf \
  -F "file=@/path/to/stripe_job_description.pdf" \
  -F "source_type=company_pdf" \
  -F "company=Stripe"
```

### 4. Generate Career Path:

```bash
curl -X POST http://localhost:8000/api/career-path \
  -H "Content-Type: application/json" \
  -d '{
    "target_role": "Data Scientist at Stripe",
    "company": "Stripe"
  }'
```

## 📊 API Endpoints

### 1. Upload PDF

```http
POST /api/upload-pdf
Content-Type: multipart/form-data

Parameters:
- file: PDF file
- source_type: "resume" | "company_pdf" | "project_pdf"
- company: (optional) Company name
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully indexed resume.pdf",
  "doc_id": "abc123",
  "filename": "resume.pdf",
  "source_type": "resume",
  "chunks": 5
}
```

### 2. List All Documents

```http
GET /api/list-documents
```

**Response:**
```json
{
  "success": true,
  "documents": {
    "resume": [
      {
        "doc_id": "abc123",
        "filename": "my_resume.pdf",
        "uploaded_at": "2024-01-15T10:30:00",
        "total_chunks": 5
      }
    ],
    "company_pdf": [
      {
        "doc_id": "def456",
        "filename": "stripe_job.pdf",
        "company": "Stripe",
        "uploaded_at": "2024-01-15T10:35:00",
        "total_chunks": 8
      }
    ],
    "project_pdf": []
  }
}
```

### 3. Delete Document

```http
DELETE /api/delete-document/{doc_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Document abc123 deleted successfully"
}
```

### 4. Generate Career Path

```http
POST /api/career-path
Content-Type: application/json

{
  "target_role": "Data Scientist at Stripe",
  "company": "Stripe"  // optional - filters company PDFs
}
```

**Response:**
```json
{
  "career_path": "## Skills Match\n- Python programming...",
  "skills_match": [...],
  "gaps": [...],
  "learning_steps": [...]
}
```

## 🎨 How It Works

### 1. Dual-Source Indexing

When you upload PDFs, they're indexed with metadata:

```python
{
  "source_type": "resume",        # or "company_pdf", "project_pdf"
  "company": "Stripe",             # optional
  "filename": "resume.pdf",
  "doc_id": "abc123",
  "uploaded_at": "2024-01-15...",
  "chunk_idx": 0,
  "total_chunks": 5
}
```

### 2. Dual Retrieval

When you request a career path:

```python
# Step 1: Retrieve from resume
resume_context = retrieve(
    query="Data Scientist skills",
    where={"source_type": "resume"}
)
# Returns: Your Python, ML, SQL experience

# Step 2: Retrieve from company PDFs
company_context = retrieve(
    query="Data Scientist requirements",
    where={"source_type": "company_pdf", "company": "Stripe"}
)
# Returns: Stripe's requirements for DS role

# Step 3: Agent combines both
agent.plan(resume_context + company_context)
```

### 3. Career Path Generation

The agent creates:

**Skills Match:**
- Python (3 years) → Matches Stripe's Python requirement
- Machine Learning → Aligns with ML pipeline work
- SQL → Needed for data querying

**Gaps:**
- Spark/Airflow experience (Stripe uses these)
- Production ML deployment
- A/B testing frameworks

**Learning Path:**
1. **Spark Fundamentals** (2 months)
   - Course: Databricks Spark Certification
   - Project: Build ETL pipeline on sample dataset
   - Develops: Distributed computing, data engineering

2. **ML Deployment** (3 months)
   - Course: "Deploying ML Models" on Coursera
   - Project: Deploy model with FastAPI + Docker
   - Develops: MLOps, containerization, APIs

3. **Build Stripe-Like Project** (2 months)
   - Project: End-to-end ML pipeline for financial data
   - Use: Spark, Airflow, MLflow
   - Develops: Full-stack ML skills

## 💡 Use Cases

### Use Case 1: Target Specific Company

```bash
# 1. Upload your resume
curl -X POST .../api/upload-pdf -F "file=@resume.pdf" -F "source_type=resume"

# 2. Upload Stripe job description
curl -X POST .../api/upload-pdf \
  -F "file=@stripe_ds_job.pdf" \
  -F "source_type=company_pdf" \
  -F "company=Stripe"

# 3. Get personalized path
curl -X POST .../api/career-path \
  -d '{"target_role": "Data Scientist at Stripe", "company": "Stripe"}'
```

### Use Case 2: Multiple Companies

```bash
# Upload job descriptions from multiple companies
curl -X POST .../api/upload-pdf -F "file=@google_ml.pdf" -F "source_type=company_pdf" -F "company=Google"
curl -X POST .../api/upload-pdf -F "file=@meta_ai.pdf" -F "source_type=company_pdf" -F "company=Meta"

# Compare paths
curl -X POST .../api/career-path -d '{"target_role": "ML Engineer", "company": "Google"}'
curl -X POST .../api/career-path -d '{"target_role": "ML Engineer", "company": "Meta"}'
```

### Use Case 3: Project-Based Learning

```bash
# Upload project documentation
curl -X POST .../api/upload-pdf \
  -F "file=@tensorflow_project.pdf" \
  -F "source_type=project_pdf"

# Get path to contribute
curl -X POST .../api/career-path \
  -d '{"target_role": "Contribute to TensorFlow project"}'
```

## 🔍 Frontend Integration (Example)

```html
<form id="upload-resume-form">
  <input type="file" id="resume-file" accept=".pdf" />
  <button type="submit">Upload Resume</button>
</form>

<form id="upload-company-form">
  <input type="file" id="company-file" accept=".pdf" />
  <input type="text" id="company-name" placeholder="Company name (e.g., Stripe)" />
  <button type="submit">Upload Company PDF</button>
</form>

<button id="generate-path">Generate Career Path</button>
<div id="career-path-output"></div>
```

```javascript
// Upload resume
document.getElementById('upload-resume-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const formData = new FormData();
  formData.append('file', document.getElementById('resume-file').files[0]);
  formData.append('source_type', 'resume');

  const response = await fetch('http://localhost:8000/api/upload-pdf', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  console.log('Resume uploaded:', result);
});

// Upload company PDF
document.getElementById('upload-company-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const formData = new FormData();
  formData.append('file', document.getElementById('company-file').files[0]);
  formData.append('source_type', 'company_pdf');
  formData.append('company', document.getElementById('company-name').value);

  const response = await fetch('http://localhost:8000/api/upload-pdf', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  console.log('Company PDF uploaded:', result);
});

// Generate career path
document.getElementById('generate-path').addEventListener('click', async () => {
  const response = await fetch('http://localhost:8000/api/career-path', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_role: 'Data Scientist at Stripe',
      company: 'Stripe'
    })
  });

  const result = await response.json();
  document.getElementById('career-path-output').innerHTML =
    `<pre>${result.career_path}</pre>`;
});
```

## 🎓 Advanced Features

### Custom Metadata

```python
# Add custom metadata when indexing
result = pdf_rag_system.index_pdf(
    pdf_path=Path("resume.pdf"),
    source_type="resume",
    metadata={
        "years_experience": 5,
        "primary_skills": ["Python", "ML", "SQL"],
        "preferred_role": "Data Scientist"
    }
)
```

### Filtered Retrieval

```python
# Retrieve only from specific company
results = pdf_rag_system.retrieve_from_company(
    query="Data engineering skills",
    company="Stripe",
    top_k=5
)
```

### Dual Retrieval Customization

```python
# Different top_k for each source
context = pdf_rag_system.dual_retrieve(
    query="Machine Learning Engineer",
    company="Google",
    resume_k=10,    # Get more resume context
    company_k=5     # Less company context
)
```

## 🛠️ Troubleshooting

### No text extracted from PDF

**Problem**: Upload returns "No text extracted"

**Solutions:**
- PDF might be image-based (scanned) - use OCR (pytesseract)
- Try converting PDF to text first
- Check if PDF is encrypted

### ChromaDB errors

**Problem**: `chromadb.errors.ChromaError`

**Solution:**
```bash
# Delete and recreate database
rm -rf backend/data/dual_source_chroma
python app.py  # Will recreate on startup
```

### Out of memory

**Problem**: Large PDFs cause memory issues

**Solution:**
- Reduce chunk_size in `pdf_rag.py`
- Process PDFs in batches
- Use smaller embedding model

## 📈 Performance

- **PDF Upload**: ~2-5 seconds per document
- **Indexing**: ~50ms per chunk
- **Dual Retrieval**: ~100ms for both sources
- **Career Path Generation**: ~3-10 seconds (depends on Claude API)

---

**Next Steps**: Add frontend UI for PDF uploads and career path visualization! 🚀
