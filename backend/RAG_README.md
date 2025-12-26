# RAG-Enhanced AI Career Agents

This system enhances your AI Career Agents with **real-world job examples** using Retrieval-Augmented Generation (RAG).

## 🎯 What This Does

Your AI agents will now cite **actual job descriptions** and **company examples** when providing career advice, making their guidance more concrete and actionable.

**Before RAG:**
> "You could become a Financial Analyst working with data..."

**After RAG:**
> "Based on roles at companies like Stripe and Google, FP&A analysts typically spend 40% of their time on forecasting models, 30% on stakeholder presentations..."

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│  Step A: Data Collection                    │
│  ├─ Search for job descriptions            │
│  ├─ Fetch webpage content                  │
│  └─ Extract clean text (trafilatura)       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Step B: Storage                            │
│  └─ Save to JSONL files                    │
│     ├─ finance.jsonl                       │
│     ├─ healthcare.jsonl                    │
│     └─ consultant.jsonl                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Step C: RAG Indexing                       │
│  ├─ Generate embeddings (sentence-trans)   │
│  ├─ Store in ChromaDB                      │
│  └─ Enable semantic search                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Step D: Agent Integration                  │
│  └─ CrewAI agents query RAG for context    │
│     └─ Cite real examples in responses     │
└─────────────────────────────────────────────┘
```

## 📦 Dependencies

### Web Scraping & HTTP
- **httpx**: Modern async HTTP client with retry support
- **tenacity**: Retry logic with exponential backoff
- **trafilatura**: Extracts clean article text from webpages
- **beautifulsoup4**: HTML parsing (backup/custom extraction)

### RAG & Embeddings
- **chromadb**: Local persistent vector database
- **sentence-transformers**: Local embeddings (all-MiniLM-L6-v2)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
source ../venv/bin/activate
pip install -r ../requirements.txt
```

### 2. Run Setup (Automated)

```bash
python setup_rag.py
```

This will:
- ✅ Collect job examples from the web
- ✅ Index them in ChromaDB
- ✅ Test the search functionality

### 3. Start Your Backend

```bash
python app.py
```

Your AI agents will now automatically use RAG!

## 📚 Manual Setup (Advanced)

### Step A: Collect Data

```bash
python data_collector.py
```

This fetches job descriptions and saves them to `data/company_examples/*.jsonl`

### Step B: Index Data

```bash
python rag_system.py
```

This creates vector embeddings and indexes them in ChromaDB.

### Step C: Customize Data Sources

Edit `data_collector.py` to add your own URLs:

```python
EXAMPLE_URLS = {
    "finance": [
        "https://stripe.com/jobs/listing/financial-analyst",
        "https://levels.fyi/blog/fp-and-a-career-guide"
    ],
    "healthcare": [
        "https://tempus.com/careers/data-scientist",
        "https://www.healthcareit.com/careers"
    ],
    "consultant": [
        "https://mckinsey.com/careers/search-jobs/analyst",
        "https://managementconsulted.com/consultant-job"
    ]
}
```

## 🔍 How It Works

### 1. User Asks for Career Advice

```javascript
// Frontend sends request
fetch('http://localhost:8000/api/agent', {
    mode: 'summary',
    agentType: 'finance',
    profile: 'Python, ML, data analysis...'
})
```

### 2. Backend Retrieves Relevant Examples

```python
# app.py
rag_context = rag_system.get_context_for_agent(
    career_path="finance",
    user_profile=profile,
    top_k=3
)
```

### 3. ChromaDB Performs Semantic Search

```python
# rag_system.py
results = collection.query(
    query_texts=[user_profile],
    n_results=3
)
```

### 4. Agent Receives Context + Generates Response

```python
task = Task(
    description=f"""
    Candidate Profile: {profile}

    REAL-WORLD JOB EXAMPLES:
    {rag_context}

    Create a career story citing these examples...
    """
)
```

## 📁 Directory Structure

```
backend/
├── app.py                    # Main FastAPI server (with RAG integration)
├── rag_system.py            # RAG logic (ChromaDB + embeddings)
├── data_collector.py        # Web scraping script
├── setup_rag.py            # Automated setup
├── data/
│   ├── company_examples/    # JSONL data files
│   │   ├── finance.jsonl
│   │   ├── healthcare.jsonl
│   │   └── consultant.jsonl
│   └── chroma_db/          # ChromaDB persistent storage
│       └── [vector indices]
└── RAG_README.md           # This file
```

## 🧪 Testing

### Test RAG Search

```bash
python -c "
from rag_system import CareerRAG
rag = CareerRAG()

results = rag.search(
    career_path='finance',
    query='Python data analysis forecasting',
    top_k=3
)

for r in results:
    print(f'{r[\"rank\"]}: {r[\"title\"]}')
    print(f'   {r[\"text\"][:100]}...')
"
```

### Test Full Pipeline

```bash
curl -X POST http://localhost:8000/api/agent \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "summary",
    "agentType": "finance",
    "profile": "Python, machine learning, data analysis experience"
  }'
```

## 🎨 Customization

### Change Embedding Model

Edit `rag_system.py`:

```python
self.embedding_model = SentenceTransformer(
    "all-mpnet-base-v2"  # More accurate but slower
    # "all-MiniLM-L6-v2"  # Faster, default
)
```

### Adjust Chunk Size

```python
chunks = self._chunk_text(text, chunk_size=800, overlap=100)
```

### Change Number of Examples Retrieved

```python
rag_context = rag_system.get_context_for_agent(
    career_path=agent_type,
    user_profile=profile,
    top_k=5  # Retrieve 5 examples instead of 3
)
```

## 🐛 Troubleshooting

### No results from RAG search

**Problem**: `rag.search()` returns empty list

**Solution**:
1. Check data files exist: `ls backend/data/company_examples/`
2. Re-run indexing: `python rag_system.py`
3. Check ChromaDB directory: `ls backend/data/chroma_db/`

### Import errors

**Problem**: `ModuleNotFoundError: No module named 'chromadb'`

**Solution**:
```bash
source ../venv/bin/activate
pip install chromadb sentence-transformers
```

### Web scraping fails

**Problem**: `HTTPError: 403 Forbidden`

**Solution**:
- Some sites block automated requests
- Add manual data to JSONL files instead
- Or use different URLs in `EXAMPLE_URLS`

## 📈 Performance

- **Embedding model**: ~50ms per query
- **ChromaDB search**: ~10ms for top-3 results
- **Total overhead**: ~60ms per agent request

## 🔐 Privacy & Data

- All data stored locally (no external APIs for RAG)
- ChromaDB runs locally (no cloud uploads)
- Sentence-transformers runs locally
- Only Claude API is external (for agent responses)

## 📚 Next Steps

1. **Add more data sources**: Edit `EXAMPLE_URLS` in `data_collector.py`
2. **Fine-tune prompts**: Update agent task descriptions in `app.py`
3. **Monitor agent responses**: Check if they cite the examples
4. **Iterate**: Add better sources, adjust chunk sizes, etc.

## 🤝 Contributing

Add your own job description sources by:
1. Finding relevant career pages
2. Adding URLs to `data_collector.py`
3. Running `python data_collector.py`
4. Re-indexing with `python rag_system.py`

---

**Built with**: FastAPI • CrewAI • Claude • ChromaDB • Sentence-Transformers
