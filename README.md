# 🚨 RapidCare AI — AI Emergency Medical Assistant

<div align="center">

![RapidCare AI Banner](https://img.shields.io/badge/RapidCare-AI%20Emergency%20Assistant-ef4444?style=for-the-badge&logo=heart&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**A production-grade AI system that guides bystanders during road accidents and medical emergencies through intelligent multi-modal analysis, real-time first-aid guidance, and hospital routing.**

[🚀 Quick Start](#-quick-start) · [🏗️ Architecture](#️-architecture) · [🤖 AI Pipeline](#-ai-pipeline) · [📡 API Reference](#-api-reference) · [🐳 Docker](#-docker-deployment) · [📊 Datasets](DATASETS.md) · [🧠 Technical Deep Dive](TECHNICAL.md)

</div>

---

## 🎯 Real-World Problem

In road accidents and medical emergencies, bystanders don't know:
- ❓ What **first aid** to give the victim
- ❓ Which **hospital** has the required facilities nearby
- ❓ Whether an **ambulance** has been dispatched
- ❓ How to **communicate** effectively with emergency services

Existing emergency apps mainly focus on **calling for help** — not providing intelligent, actionable guidance.

## 💡 Solution

RapidCare AI is an **end-to-end AI system** that:

| Feature | Description |
|---------|-------------|
| 🔍 **Multi-modal Detection** | Analyzes emergency from text, image (camera), or voice |
| 📊 **Severity Estimation** | Scores injury severity 0–100 with contributing factors |
| 🩺 **First-Aid Guidance** | Step-by-step RAG-based first-aid instructions |
| 🏥 **Hospital Routing** | Finds nearest suitable hospitals using Haversine + specialty matching |
| 📈 **Survival Prediction** | Estimates survival probability with immediate care |
| 📋 **Emergency Reports** | Generates structured reports (JSON + PDF) |
| 🚑 **Live Ambulance Tracking** | Real-time status updates via WebSocket |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│              React Frontend (Vite + Leaflet.js)                  │
│   Voice Input · Image Upload · Live Dashboard · Hospital Map     │
└─────────────────────────┬────────────────────────────────────────┘
                          │ REST + WebSocket
┌─────────────────────────▼────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  POST /api/emergency/analyze  ·  GET /api/hospitals/nearby       │
│  POST /api/reports/generate   ·  WS  /ws/live/{incident_id}      │
└──────┬──────────┬──────────┬──────────┬────────────────────────--┘
       │          │          │          │
   AI Engine  Hospital   Report    Redis Cache
   Pipeline   Service    Service   (Redis 7)
       │
┌──────▼─────────────────────────────────────────┐
│          AI Pipeline (Python / PyTorch)        │
│  ┌─────────────┐  ┌──────────────┐             │
│  │ NLP Service │  │Vision Service│             │
│  │ (keywords/  │  │  (YOLOv8n    │             │
│  │  distilbert)│  │  / mocked)   │             │
│  └─────────────┘  └──────────────┘             │
│  ┌─────────────┐  ┌──────────────┐             │
│  │Speech (STT) │  │ Severity Est │             │
│  │  Whisper    │  │ (Rule + MLP) │             │
│  └─────────────┘  └──────────────┘             │
│  ┌────────────────────────────────┐            │
│  │  First-Aid RAG (TF-IDF + KB)   │            │
│  └────────────────────────────────┘            │
└────────────────────────────────────────────────┘
                    │
         PostgreSQL 15 (Incidents, Hospitals, Reports)
```

---

## 🤖 AI Pipeline

| Component | Technology | Mode |
|-----------|-----------|------|
| Emergency detection (text) | Keyword NLP → `distilbert` zero-shot | Demo / Full |
| Injury detection (image) | `YOLOv8n` object detection | Demo / Full |
| Speech transcription | `openai/whisper-small` (local) | Demo / Full |
| Severity scoring | Rule-based keyword modifier + survival sigmoid | Always |
| First-aid retrieval | TF-IDF RAG over JSON knowledge base | Always |
| Hospital matching | Haversine distance + specialty scoring | Always |
| Report generation | JSON + PDF (`reportlab`) | Always |

> **Demo mode** (`AI_MODE=demo` in `.env`) returns mock AI responses instantly — no model downloads required. Perfect for portfolio presentations.

---

## 🗂️ Project Structure

```
rapidcare-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, lifespan, routers
│   │   ├── config.py                # Pydantic settings
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── incident.py          # Incident model
│   │   │   ├── hospital.py          # Hospital model
│   │   │   └── report.py            # Report model
│   │   ├── api/                     # Route handlers
│   │   │   ├── emergency.py         # POST /api/emergency/analyze
│   │   │   ├── hospitals.py         # GET /api/hospitals/nearby
│   │   │   ├── reports.py           # POST /api/reports/generate[-pdf]
│   │   │   └── ws.py                # WS /ws/live/{incident_id}
│   │   ├── services/                # AI service layer
│   │   │   ├── ai_engine.py         # Pipeline orchestrator
│   │   │   ├── nlp_service.py       # Text emergency classification
│   │   │   ├── vision_service.py    # Image analysis (YOLOv8)
│   │   │   ├── speech_service.py    # Whisper STT
│   │   │   ├── severity_service.py  # Severity + survival estimation
│   │   │   ├── firstaid_service.py  # RAG first-aid retrieval
│   │   │   ├── hospital_service.py  # Nearest hospital routing
│   │   │   └── report_service.py    # JSON + PDF report generation
│   │   ├── db/
│   │   │   ├── database.py          # Async SQLAlchemy engine
│   │   │   └── seed_hospitals.py    # Seeds 50 Indian hospitals
│   │   └── knowledge_base/
│   │       └── first_aid_protocols.json  # 8 emergency protocols
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Router + Navbar
│   │   ├── pages/
│   │   │   ├── EmergencyInput.jsx   # Text/Image/Voice input
│   │   │   ├── Dashboard.jsx        # Analysis results + first-aid
│   │   │   ├── HospitalMap.jsx      # Leaflet map + hospital list
│   │   │   └── ReportView.jsx       # Structured report + PDF export
│   │   ├── components/
│   │   │   ├── SeverityGauge.jsx    # Animated SVG gauge
│   │   │   ├── FirstAidGuide.jsx    # Interactive step checklist
│   │   │   ├── AmbulanceTracker.jsx # WebSocket live tracker
│   │   │   └── EmergencyAlert.jsx   # Severity-colored banner
│   │   └── services/api.js          # Axios API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Option 1: Local Development (Recommended for dev)

#### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15 running locally (or use Docker just for DB)

#### 1. Clone & Configure
```bash
git clone https://github.com/yourusername/rapidcare-ai.git
cd rapidcare-ai
cp .env.example .env
# Edit .env — set AI_MODE=demo for instant startup without model downloads
```

#### 2. Start Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend starts at **http://localhost:8000**
API docs at **http://localhost:8000/docs**

#### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend starts at **http://localhost:5173**

---

### Option 2: Docker (One command)

```bash
cd rapidcare-ai
cp .env.example .env
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 📡 API Reference

### `POST /api/emergency/analyze`
Multi-modal emergency analysis.

**Request** (multipart/form-data):
| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Emergency description |
| `image` | file | Injury photo (JPG/PNG) |
| `audio` | file | Voice description (WebM/MP3) |
| `latitude` | float | GPS latitude |
| `longitude` | float | GPS longitude |

**Response:**
```json
{
  "incident_id": "uuid",
  "emergency_type": "road_accident",
  "severity_score": 78.5,
  "severity_level": "SEVERE",
  "survival_probability": 0.55,
  "confidence": 0.87,
  "first_aid_steps": ["Step 1...", "Step 2..."],
  "warnings": ["Warning..."],
  "nearest_hospitals": [{ "name": "...", "distance_km": 2.3 }],
  "report": { ... }
}
```

---

### `GET /api/hospitals/nearby`
Find nearest hospitals.

**Query params:** `latitude`, `longitude`, `specialties` (comma-separated), `limit`

---

### `POST /api/reports/generate-pdf`
Generate downloadable PDF emergency report.

---

### `WS /ws/live/{incident_id}`
WebSocket — streams ambulance status updates every 5 seconds.

---

## 🔧 Configuration

Edit `.env`:

```env
AI_MODE=demo          # demo (instant mock) | full (load real models)
WHISPER_MODEL=small   # tiny | base | small | medium
DATABASE_URL=postgresql+asyncpg://rapidcare:rapidcare123@localhost:5432/rapidcare_db
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=       # Optional — enhances LLM responses
```

### AI Mode Comparison

| Feature | Demo Mode | Full Mode |
|---------|-----------|-----------|
| Startup time | < 2s | 30–120s (model download) |
| Emergency detection | Keyword matching | distilbert zero-shot |
| Image analysis | Mock detections | YOLOv8n |
| Speech STT | Mock transcription | Whisper (local) |
| Internet required | No | For first model download |

---

## 🏥 Hospital Database

The system seeds **50 real Indian hospitals** across:
Mumbai · New Delhi · Bangalore · Chennai · Hyderabad · Pune · Kolkata · Ahmedabad · Jaipur · Chandigarh · Lucknow · Gurugram · Bhopal · Kochi · and more...

Each hospital includes: coordinates, specialties, ICU beds, trauma center, helipad, blood bank, rating.

---

## 🧠 Emergency Types Supported

| Type | Keywords | Required Specialties |
|------|---------|---------------------|
| Road Accident | accident, crash, collision | trauma |
| Cardiac Arrest | heart attack, chest pain | cardiac |
| Stroke | slurred speech, face drooping | neurology |
| Bleeding | hemorrhage, deep cut | trauma |
| Fracture | broken bone, deformity | orthopedic, trauma |
| Burn | fire, scald, chemical burn | burn, trauma |
| Drowning | submerged, water rescue | trauma, cardiac |
| Head Injury | concussion, skull fracture | neurology, trauma |

---

## 🧪 Testing

```bash
# Install test dependencies
cd backend
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v

# Test the API directly
curl -X POST http://localhost:8000/api/emergency/analyze \
  -F "text=Road accident on highway, person unconscious and bleeding" \
  -F "latitude=19.0760" \
  -F "longitude=72.8777"
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, React Router, Leaflet.js, Axios |
| **Backend** | FastAPI, Python 3.11, Uvicorn |
| **Database** | PostgreSQL 15, SQLAlchemy 2 (async) |
| **Cache** | Redis 7, aioredis |
| **AI/ML** | PyTorch 2.3, HuggingFace Transformers, YOLOv8, Whisper, scikit-learn |
| **Report** | ReportLab (PDF generation) |
| **Infra** | Docker, docker-compose |
| **Styling** | Custom CSS (glassmorphism dark mode) |

---

## 📈 Deep Learning Architecture

```
Input (Text / Image / Audio)
         │
    ┌────▼────┐      ┌────────────┐      ┌─────────────┐
    │ Whisper │      │  YOLOv8n   │      │  distilbert │
    │  (STT)  │      │  (Vision)  │      │    (NLP)    │
    └────┬────┘      └─────┬──────┘      └──────┬──────┘
         │                 │                     │
         └─────────────────▼─────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  AI Engine  │
                    │ Orchestrator│
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼──────┐  ┌──────▼────┐  ┌───────▼──────┐
    │  Severity  │  │  RAG KnB  │  │   Hospital   │
    │  Estimator │  │ (TF-IDF)  │  │   Finder     │
    └─────┬──────┘  └──────┬────┘  └───────┬──────┘
          │                │                │
          └────────────────▼────────────────┘
                    Emergency Report
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**RapidCare AI** — Built for placement showcase ⭐⭐⭐⭐⭐

> *"In emergencies, every second counts. AI can save lives."*

---

<div align="center">

**Emergency Contacts India** 🇮🇳

| Service | Number |
|---------|--------|
| Emergency | **112** |
| Ambulance | **108** |
| Police | **100** |
| Fire | **101** |

</div>
