# Yuto's Portfolio

Personal portfolio website showcasing my projects and experience with AI-powered career guidance features.

## 🚀 Quick Start

### Option 1: Frontend Only (No AI features)
```bash
# Simply open index.html in your browser
open index.html
```

### Option 2: Full Stack (With AI Career Agents)
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Set up environment variables
cd backend
echo "ANTHROPIC_API_KEY=your_key_here" > .env
cd ..

# 3. Start backend server
cd backend
uvicorn app:app --reload --port 8000

# 4. Open frontend (in new terminal or browser)
open index.html
```

**📖 For detailed setup instructions, see [SETUP.md](SETUP.md)**

## Live Website

Visit the live website at: [**[https://yuto-49.github.io/yuto-portfolio/](https://yuto-49.github.io/yuto-portfolio/)**](https://yuto-portfolio.onrender.com/)

## Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python, FastAPI, Uvicorn
- **Deployment**: Render, AWS (see [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md))

## Features

- ✅ Interactive portfolio showcase
- ✅ Project gallery
- ✅ Resume/CV section
- ✅ Responsive design
- ✅ **AI Career Agents** - Get personalized career advice
- ✅ **Career Path Planning** - Upload resume and company PDFs for personalized guidance
- ✅ **PDF RAG System** - Intelligent document analysis

## Project Structure

```
yuto_portfolio/
├── index.html          # Frontend homepage
├── resume.html         # Resume page
├── script.js           # Frontend JavaScript
├── style.css           # Frontend styles
├── backend/
│   ├── app.py          # FastAPI backend with AI agents
│   ├── rag_system.py   # RAG system for career examples
│   ├── pdf_rag.py      # PDF document RAG system
│   └── .env            # Environment variables (create this)
├── requirements.txt    # Python dependencies
├── start.sh            # Production start script
└── SETUP.md            # Detailed setup guide
```

## Environment Variables

Create `backend/.env` file:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DISABLE_RAG=false          # Set to true to disable RAG (saves memory)
PRELOAD_RAG=false          # Set to true to preload RAG at startup
```

## Development

### Backend
```bash
source venv/bin/activate
cd backend
uvicorn app:app --reload --port 8000
```

### Frontend
```bash
# Option 1: Open directly
open index.html

# Option 2: Use HTTP server
python3 -m http.server 3000
```

## Deployment

- **Render**: See `render.yaml` and `start.sh`
- **AWS**: See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)

## Documentation

- [SETUP.md](SETUP.md) - Complete setup and troubleshooting guide
- [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) - AWS deployment instructions
- [backend/RAG_README.md](backend/RAG_README.md) - RAG system documentation
- [backend/PDF_RAG_GUIDE.md](backend/PDF_RAG_GUIDE.md) - PDF RAG guide
