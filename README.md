# 🏥 Hospital Operations AI

**An AI-powered operations intelligence platform for hospitals** — real-time bed occupancy tracking, demand forecasting, overload risk prediction, and an in-app assistant, built to help hospital administrators plan capacity before problems happen.

> ⚠️ **Operations decision-support only** — this is not a medical diagnosis or treatment system.

🔗 **[Live Demo](https://hospital-ops-ai-1.onrender.com)**

---

## 🎬 Demo Access

Try it instantly with any of these demo accounts:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@hospital-ops.demo` | `Admin@123` |
| Hospital Manager | `manager@hospital-ops.demo` | `Manager@123` |
| Department Manager | `deptmanager@hospital-ops.demo` | `DeptMgr@123` |
| Staff | `staff@hospital-ops.demo` | `Staff@123` |

> Hosted on free-tier infrastructure — the first load after inactivity may take a few seconds to spin up.

---

## ✨ Features

- **Live Operations Dashboard** — real-time bed occupancy, department-level analytics, and hospital-wide KPIs
- **AI Demand & Overload Forecasting** — machine learning models predict department overload risk and expected patient demand ahead of time
- **Bed Availability Predictions** — forecasts available beds per department using historical and live data
- **Waiting-Time & No-Show Predictions** — helps staff anticipate patient flow bottlenecks
- **Smart Alerts** — automatic risk alerts (normal / moderate / high / critical) per department
- **In-App AI Assistant (Chatbot)** — ask natural-language questions about beds, alerts, and predictions
- **Role-Based Access Control** — Admin, Hospital Manager, Department Manager, and Staff roles with JWT authentication
- **Patient & Appointment Management** — track patients, appointments, and hospital events
- **Audit Logs** — full activity trail for accountability
- **Model Performance Monitoring** — visibility into how the underlying ML models are performing

---

## 🛠️ Tech Stack

**Backend**
- FastAPI (Python) — REST API
- SQLAlchemy + Alembic — ORM & migrations
- PostgreSQL ([Neon](https://neon.tech)) — production database
- Redis ([Upstash](https://upstash.com)) — caching / background task support
- JWT (python-jose) + Passlib/Bcrypt — authentication & security

**Machine Learning**
- XGBoost, scikit-learn — demand & overload prediction models
- Pandas, NumPy — data processing

**Frontend**
- HTML5, Tailwind CSS, vanilla JavaScript
- Chart.js — data visualizations
- Nginx — static file serving

**Infrastructure**
- Docker — containerized backend & frontend
- Render — hosting (backend + frontend as separate web services)
- Neon — managed Postgres
- Upstash — managed Redis

---

## 🏗️ Architecture

```
┌──────────────────┐        HTTPS         ┌───────────────────┐
│   Frontend (SPA)  │ ───────────────────▶ │   Backend (API)    │
│  Nginx + JS/Chart │ ◀─────────────────── │      FastAPI        │
└──────────────────┘        JSON           └─────────┬──────────┘
                                                       │
                                   ┌───────────────────┼───────────────────┐
                                   ▼                   ▼                   ▼
                            ┌────────────┐      ┌────────────┐     ┌─────────────┐
                            │  PostgreSQL │      │    Redis    │     │  ML Models   │
                            │   (Neon)    │      │  (Upstash)  │     │ (XGBoost etc)│
                            └────────────┘      └────────────┘     └─────────────┘
```

Both frontend and backend are deployed as independent Dockerized services, communicating over HTTPS with CORS-restricted access.

---

## 🚀 Running Locally

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (if running without Docker)

### With Docker (recommended)

```bash
git clone https://github.com/umani6481-dev/hospital-ops-ai.git
cd hospital-ops-ai
docker-compose up --build
```

This spins up Postgres, Redis, the backend API, and the frontend together.

### Manual Setup (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env       # then fill in your DB/Redis credentials
python scripts/seed_database.py   # optional: seed demo data
uvicorn app.main:app --reload
```

### Manual Setup (frontend)

Serve the `frontend/` folder with any static file server (or open `index.html` directly), and set the backend URL:

```html
<script>
  window.HOSPITAL_API_BASE = "http://localhost:8000";
</script>
```

---

## 📊 Sample Data

The live demo runs on **synthetic, AI-generated data** — thousands of simulated patient visits, appointments, and hospital events — so it's safe to explore without any real patient information involved.

---

## 📄 License

This project is available for portfolio and demonstration purposes. Contact for licensing/commercial use.

---

**Built by [Muhammad Usman]** — full-stack development, ML integration, and cloud deployment.