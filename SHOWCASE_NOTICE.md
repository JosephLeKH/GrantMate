# 🎓 Hackathon Project Showcase

> **Note:** This is a public showcase repository for a hackathon project. Some configuration details have been removed for security purposes.

## About This Repository

This repository demonstrates a **Grant Writing Assistant** built with:
- **Backend:** FastAPI + Google Gemini API
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **AI/ML:** Vector embeddings, semantic search, RAG (Retrieval-Augmented Generation)

## 🚀 What It Does

An AI-powered assistant that helps nonprofit organizations write grant applications by:
1. **Semantic Search** - Finds relevant information from a knowledge base using vector embeddings
2. **Context-Aware Generation** - Uses Google Gemini to generate tailored responses
3. **Source Attribution** - Cites sources for all generated content
4. **Sponsor Alignment** - Adapts responses to match specific grant requirements

## 🏗️ Architecture

```
Frontend (React/TypeScript)
    ↓
FastAPI Backend
    ↓
Google Gemini API
    ↓
Knowledge Base (Markdown files)
```

## ⚙️ To Run This Project

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup

1. **Clone and Install**
```bash
git clone <your-repo>
cd GrantMateRepo

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install
```

2. **Configure Environment**
```bash
# Create .env file
echo "GEMINI_API_KEY=your-api-key-here" > .env

# Optional: Set frontend API URL
echo "VITE_API_URL=http://localhost:8000/api/generate" >> .env
```

3. **Run**
```bash
# Quick start (both backend + frontend)
chmod +x run_local.sh
./run_local.sh

# Or run separately:
# Backend: uvicorn main:app --reload
# Frontend: npm run dev
```

4. **Access**
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI backend server |
| `qa_system.py` | RAG system with vector search |
| `src/App.tsx` | React frontend application |
| `knowledge_base/` | Grant data and organization info |
| `requirements.txt` | Python dependencies |
| `package.json` | Node dependencies |

## 🔒 Security Note

**This is a showcase repository.** For security reasons:
- ❌ Production API endpoints have been removed
- ❌ Deployment configurations are not included
- ❌ API keys are not included (use your own)
- ✅ The code demonstrates the architecture and approach

## 💡 Features Demonstrated

- ✨ **Vector Embeddings** - Semantic search using Google's text-embedding-004
- 🎯 **Smart Caching** - Embeddings cached on disk for performance
- 📝 **Prompt Engineering** - Sophisticated prompts for high-quality grant writing
- 🎨 **Modern UI** - Clean, responsive React interface
- 🔄 **Streaming-Ready** - Architecture supports streaming responses
- 📊 **Source Attribution** - Transparent sourcing of information

## 📚 Technology Stack

**Backend:**
- FastAPI (Python web framework)
- Google Generative AI (Gemini)
- NumPy (vector operations)
- Pydantic (data validation)

**Frontend:**
- React 19
- TypeScript
- Vite (build tool)
- Tailwind CSS 4

**AI/ML:**
- Google Gemini 2.0 Flash (LLM)
- text-embedding-004 (embeddings)
- RAG (Retrieval-Augmented Generation)
- Vector similarity search

## 🎯 Hackathon Goals

This project was built to:
1. Demonstrate practical AI/ML application
2. Solve a real problem for nonprofit organizations
3. Showcase full-stack development skills
4. Implement modern web technologies

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

This is a showcase repository. The production version is maintained privately.

## 📧 Contact

For questions about this project, please open an issue or contact the repository owner.

---

**Built with ❤️ for [Hackathon Name]**

