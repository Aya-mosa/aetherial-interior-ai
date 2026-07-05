# ✦ Aetherial — AI Interior Architect

A premium AI-powered interior design platform. Multi-agent pipeline with SDXL + ControlNet.

## Project Structure

```
aetherial-interior-ai/
├── backend/          ← FastAPI multi-agent pipeline
│   ├── main.py
│   ├── agents/       ← 6 AI agents
│   ├── api/routes/   ← REST endpoints
│   ├── services/     ← Pipeline orchestration
│   └── core/         ← Config, logging
└── frontend/         ← Next.js 14 app
    ├── src/
    │   ├── app/      ← Layout + page
    │   ├── components/
    │   │   ├── layout/   ← Navbar, AmbientBackground
    │   │   └── panels/   ← UploadStep, StyleStep, FurnitureStep, GeneratingStep, ResultStep, AIAssistant
    │   ├── lib/      ← types.ts, api.ts
    │   └── store/    ← Zustand store
    └── package.json
```

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # Add GEMINI_API_KEY, HF_SPACE_URL
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

## Features

- **Upload** empty room photo (drag & drop)
- **7 Design Styles** — Modern, Minimal, Scandinavian, Luxury, Japandi, Industrial, Cyberpunk
- **10 Furniture Items** — clickable cards with emoji icons
- **Multi-agent pipeline** — 6 sequential AI agents with real-time progress
- **Before/After slider** — interactive comparison
- **AI Chat Assistant** — natural language design commands
- **3 variations** generated per design
- **Floor plan viewer** — spatial layout visualization

## Environment Variables

Backend `.env`:
```
GEMINI_API_KEY=your_key_here
HF_SPACE_URL=your_huggingface_space_url   # SDXL + ControlNet endpoint
```

Frontend `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
