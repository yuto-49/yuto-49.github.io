# How to Activate/Run Your Portfolio Website

This guide will help you run your portfolio website locally with both frontend and backend.

## Quick Start (Local Development)

### Option 1: Frontend Only (Static Website)
If you just want to see the website without AI features:

```bash
# Simply open index.html in your browser
open index.html
# or
python3 -m http.server 3000
# Then visit http://localhost:3000
```

### Option 2: Full Stack (Frontend + Backend with AI)
For full functionality including AI Career Agents:

## Step-by-Step Setup

### 1. Activate Virtual Environment

```bash
# Navigate to project directory
cd /Users/maruyamayuto/Desktop/coding/yuto_portfolio

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

### 2. Set Up Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cd backend
nano .env  # or use any text editor
```

Add your API key:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DISABLE_RAG=false
PRELOAD_RAG=false
```

**To get an Anthropic API key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste it into your `.env` file

### 3. Start the Backend Server

```bash
# Make sure you're in the project root
cd /Users/maruyamayuto/Desktop/coding/yuto_portfolio

# Activate venv if not already activated
source venv/bin/activate

# Start backend server
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
🚀 Yuto Portfolio AI Backend started successfully!
```

**Keep this terminal window open!**

### 4. Open the Frontend

In a **new terminal window** (keep backend running):

```bash
# Option A: Open directly in browser
open index.html

# Option B: Use Python's simple HTTP server
python3 -m http.server 3000
# Then visit http://localhost:3000 in your browser
```

**Or simply double-click `index.html` in Finder**

### 5. Verify It's Working

1. **Backend Health Check**: Visit http://localhost:8000/health
   - Should return: `{"status":"healthy"}`

2. **Frontend**: Open http://localhost:3000 (if using HTTP server) or the file directly
   - You should see your portfolio website
   - Try the "AI Career Agents" section to test backend connection

## Troubleshooting

### Backend won't start

**Error: Module not found**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Error: Port 8000 already in use**
```bash
# Use a different port
uvicorn app:app --reload --host 0.0.0.0 --port 8001

# Then update script.js line 352 and 512:
# Change 'http://localhost:8000' to 'http://localhost:8001'
```

**Error: ANTHROPIC_API_KEY not set**
- Make sure you created `.env` file in `backend/` directory
- Check that the file contains: `ANTHROPIC_API_KEY=your_key_here`

### Frontend can't connect to backend

**CORS errors in browser console:**
- Backend already has CORS enabled, but make sure backend is running
- Check that backend URL in `script.js` matches your backend port

**404 errors:**
- Verify backend is running on port 8000
- Check browser console for exact error messages

### RAG system issues

**Out of memory errors:**
- Set `DISABLE_RAG=true` in `.env` file
- Or use lazy loading (default) - models load on first use

**RAG models not loading:**
- First request will be slower (2-5 seconds) as models load
- Check backend logs for error messages
- Make sure you have enough RAM (2GB+ recommended)

## Development Workflow

### Running Both Frontend and Backend

**Terminal 1 (Backend):**
```bash
cd /Users/maruyamayuto/Desktop/coding/yuto_portfolio
source venv/bin/activate
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend - Optional HTTP server):**
```bash
cd /Users/maruyamayuto/Desktop/coding/yuto_portfolio
python3 -m http.server 3000
```

**Browser:**
- Visit http://localhost:3000 or open `index.html` directly

### Making Changes

- **Frontend changes**: Just refresh the browser
- **Backend changes**: Uvicorn will auto-reload (thanks to `--reload` flag)
- **Environment variables**: Restart backend after changing `.env`

## Production Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect repository to Render
3. Set environment variables in Render dashboard:
   - `ANTHROPIC_API_KEY`
   - `DISABLE_RAG=false` (or `true` if memory limited)
4. Deploy!

See `render.yaml` for configuration.

### Deploy to AWS

See `AWS_DEPLOYMENT.md` for detailed AWS setup instructions.

## Quick Reference Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Start backend
cd backend && uvicorn app:app --reload --port 8000

# Start frontend server (optional)
python3 -m http.server 3000

# Check backend health
curl http://localhost:8000/health

# Deactivate virtual environment
deactivate
```

## File Structure

```
yuto_portfolio/
├── index.html          # Frontend (open in browser)
├── script.js           # Frontend JavaScript
├── style.css           # Frontend styles
├── backend/
│   ├── app.py          # FastAPI backend
│   ├── .env            # Environment variables (create this)
│   └── ...
├── requirements.txt    # Python dependencies
├── start.sh            # Production start script
└── venv/               # Virtual environment
```

## Need Help?

- Check backend logs in the terminal where uvicorn is running
- Check browser console (F12) for frontend errors
- Verify `.env` file exists and has correct API key
- Make sure virtual environment is activated

