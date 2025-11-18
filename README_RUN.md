# How to Run GrantMate Locally

> **📌 Note:** This is a showcase repository. See [SHOWCASE_NOTICE.md](SHOWCASE_NOTICE.md) for important information about this public version.

## Prerequisites

- Python 3.11+ with pip
- Node.js 18+ with npm
- Gemini API key (get one at https://makersuite.google.com/app/apikey)

## Quick Start (Recommended)

### 1. Set your API key
```bash
export GEMINI_API_KEY='your-api-key-here'
```

### 2. Run the application
```bash
chmod +x run_local.sh
./run_local.sh
```

This will automatically:
- Install Python dependencies
- Install Node dependencies
- Start the backend on http://localhost:8000
- Start the frontend on http://localhost:8080

### 3. Open in Browser
Go to: **http://localhost:8080**

## Manual Method

If you prefer to run backend and frontend separately:

### Backend Only

```bash
# Install dependencies
pip3 install -r requirements.txt

# Set API key
export GEMINI_API_KEY='your-api-key-here'

# Start backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be available at:
- **API**: http://localhost:8000/api/generate
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

### Frontend Only

```bash
# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend will be available at: **http://localhost:8080**

## What You Get

- **Frontend UI**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

## Usage

1. Open http://localhost:8080
2. Paste grant questions in the textarea
3. Optionally add sponsor context
4. Click "Generate Draft"
5. Review and copy the AI-generated answers

## Troubleshooting

**Port already in use?**
```bash
# Backend on different port
uvicorn main:app --host 127.0.0.1 --port 8001 --reload

# Frontend on different port (edit vite.config.ts)
```

**Python dependencies missing?**
```bash
pip3 install -r requirements.txt
```

**Node dependencies missing?**
```bash
npm install
```

**API key not set?**
```bash
export GEMINI_API_KEY='your-api-key-here'
```

**Frontend can't reach backend?**

Make sure the backend is running on port 8000. Configure the API URL:
- Set `VITE_API_URL` environment variable in `.env`
- Default: http://localhost:8000

## Environment Variables

- `GEMINI_API_KEY` (required): Your Google Gemini API key
- `PORT` (optional): Port for backend (default: 8000)

## Development Tips

- Backend auto-reloads on code changes (with `--reload` flag)
- Frontend auto-reloads with Vite HMR
- Check backend logs in terminal where uvicorn is running
- Use browser DevTools to debug frontend

