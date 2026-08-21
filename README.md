# Hospital Operations AI — Hospital Operations Intelligence Platform

An AI/ML-powered hospital **operations management** platform: patient demand forecasting, department overload prediction, emergency waiting-time prediction, bed availability forecasting, and appointment no-show prediction — with explainable AI, role-based access control, alerts, and a live operations dashboard.

> ⚠️ **This is an operations-management decision-support tool, NOT a medical diagnosis or treatment system.** It never diagnoses disease, recommends medication/treatment, or makes autonomous clinical decisions. All data in this repository is **synthetic/demo data** — never real patient data.

> **Scope note (read this first):** This repository is a fully working, hands-on prototype covering the core of a much larger product spec — real trained ML models, real APIs, real auth/RBAC, a real dashboard, Docker, and tests. To keep it runnable end-to-end in one build, a few pieces from the full enterprise spec are intentionally simplified for now (see **Future Improvements** at the bottom): background jobs run synchronously on-demand rather than via Celery workers, the frontend is a single-page dashboard rather than a 16-page Next.js app, and Alembic migrations aren't wired up (SQLAlchemy creates tables directly). Everything else described below is implemented and tested.

---

## 1. Features

- **5 trained ML models**, compared across multiple algorithms and selected on time-aware validation:
  1. **Patient Demand Forecasting** (Linear Regression / Random Forest / XGBoost)
  2. **Department Overload Prediction** (Logistic Regression / Random Forest / XGBoost — 4-class risk)
  3. **Emergency/Department Waiting-Time Prediction** (Gradient Boosting / Random Forest / XGBoost)
  4. **Bed Availability Forecasting** (Random Forest / XGBoost)
  5. **Appointment No-Show Prediction** (Logistic Regression / Random Forest / XGBoost)
- **Explainability** on every prediction — top contributing factors, not just a bare number.
- **JWT auth + RBAC** — Admin, Hospital Manager, Department Manager, Staff.
- **Alert engine** — auto-generates HIGH DEMAND / OVERLOAD / BED SHORTAGE alerts with AI recommendations.
- **Full CRUD** for patients, appointments, departments, beds.
- **Analytics APIs** — occupancy, emergency metrics, department performance.
- **CSV report export**, **audit logs**, **model performance dashboard**.
- **Synthetic data generator** — 12+ months, 100k+ visit records, 49k+ appointments.
- **Docker Compose** — Postgres + Redis + backend + frontend, one command.
- **Automated tests** — auth, RBAC, CRUD, ML feature engineering (pytest).

---

## 2. Architecture

```
Next.js-style SPA Dashboard (static, Tailwind + Chart.js)
                │  REST (JSON)
                ▼
         FastAPI (Python)  ──── JWT / RBAC ──── SQLAlchemy ──── PostgreSQL
                │
                ▼
     ml/ (trained models loaded via joblib — never trained per-request)
     ├── demand_model.joblib         (Model 1: Patient Demand)
     ├── overload_model.joblib       (Model 2: Overload Risk)
     ├── waiting_time_model.joblib   (Model 3: Waiting Time)
     ├── bed_model.joblib            (Model 4: Bed Availability)
     └── noshow_model.joblib         (Model 5: No-Show)
                │
                ▼
      Alert Engine → Alerts + AI Recommendations (stored in DB)
```

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| ML | pandas, NumPy, scikit-learn, XGBoost, joblib |
| Database | PostgreSQL (Docker) / SQLite (local dev default) |
| Auth | JWT (python-jose), bcrypt |
| Frontend | Vanilla JS SPA, Tailwind CSS (CDN), Chart.js |
| Infra | Docker, Docker Compose, Nginx |
| Testing | pytest, FastAPI TestClient |

---

## 4. Database Schema (summary)

`users · roles(enum) · hospitals · departments · doctors · staff · patients · appointments · visits · beds · hospital_events · staff_schedules · predictions · model_versions · alerts · audit_logs`

Key relationships: `Hospital → Departments → Doctors/Staff/Beds`, `Patients → Appointments/Visits`, `Departments → Predictions → Alerts`.

---

## 5. ML Models & Evaluation Methodology

- **Time-aware splits** — training on earlier dates, testing on later dates only (no shuffling future data into training), preventing leakage.
- Each training script (`ml/training/train_*.py`) trains **multiple candidate algorithms**, evaluates with MAE/RMSE/MAPE/R² (regression) or accuracy/F1/ROC-AUC (classification), and **automatically selects the best model**.
- Metadata (algorithm, version, dataset version, metrics, feature list) is saved alongside each model and served via `/api/models/performance`.
- Explainability: `ml/explainability/explain.py` combines model feature-importance with each prediction's actual feature values to surface the top contributing factors for every response (analogous to SHAP, optimized for interactive latency).

Run training after generating data (see Quick Start):
```bash
python -m ml.training.train_demand_model
python -m ml.training.train_overload_model
python -m ml.training.train_waiting_time_model
python -m ml.training.train_bed_model
python -m ml.training.train_noshow_model
```

---

## 6. API Documentation

Interactive docs are auto-generated by FastAPI once the server is running:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

Key endpoint groups: `/api/auth/*`, `/api/patients`, `/api/appointments`, `/api/departments`, `/api/beds`, `/api/analytics/*`, `/api/predictions/*`, `/api/alerts/*`, `/api/admin/run-forecast`, `/api/models/performance`, `/api/reports/export`, `/api/audit-logs`.

---

## 7. Installation & Running Locally (without Docker)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env      # edit if needed (defaults to SQLite, fine for local dev)

# 1. Generate synthetic dataset (12+ months, 100k+ records)
python -m scripts.generate_dataset --days 400 --out ml/data/raw

# 2. Train all 5 ML models (reads from ml/data/raw, saves to ml/models/artifacts)
python -m ml.training.train_demand_model
python -m ml.training.train_overload_model
python -m ml.training.train_waiting_time_model
python -m ml.training.train_bed_model
python -m ml.training.train_noshow_model

# 3. Seed the database (demo users + departments + loads synthetic data)
python -m scripts.seed_database

# 4. Run the API
uvicorn app.main:app --reload --port 8000
```

Then open `frontend/index.html` directly in a browser, or serve it:
```bash
cd frontend
python3 -m http.server 8080
# visit http://localhost:8080
```

### Demo accounts (created by the seed script)
| Role | Email | Password |
|---|---|---|
| Admin | admin@hospital-ops.demo | Admin@123 |
| Hospital Manager | manager@hospital-ops.demo | Manager@123 |
| Department Manager | deptmanager@hospital-ops.demo | DeptMgr@123 |
| Staff | staff@hospital-ops.demo | Staff@123 |

---

## 8. Running with Docker

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, the FastAPI backend (port 8000), and the Nginx-served frontend (port 8080). After the containers are up, run the data + training + seed steps **inside** the backend container once:

```bash
docker compose exec backend python -m scripts.generate_dataset --days 400 --out ml/data/raw
docker compose exec backend python -m ml.training.train_demand_model
docker compose exec backend python -m ml.training.train_overload_model
docker compose exec backend python -m ml.training.train_waiting_time_model
docker compose exec backend python -m ml.training.train_bed_model
docker compose exec backend python -m ml.training.train_noshow_model
docker compose exec backend python -m scripts.seed_database
```

Then visit `http://localhost:8080`.

---

## 9. Environment Variables

See `backend/.env.example`:
```
DATABASE_URL, SECRET_KEY, JWT_SECRET, REDIS_URL, MODEL_PATH, CORS_ORIGINS
```
Never commit real secrets — `.env` is gitignored.

---

## 10. Testing

```bash
cd backend
pytest tests/ -v
```
Covers: health check, registration/login, RBAC enforcement (403 for unauthorized roles), patient CRUD, and ML feature-engineering correctness (lag features, overload label thresholds).

---

## 11. Scheduled Forecasting

In production, the pipeline in `app/services/alert_engine.py::run_daily_predictions_and_alerts` should run automatically every day at 00:00 via a scheduler (cron, Celery beat, or a cloud scheduler hitting `POST /api/admin/run-forecast`). It is exposed as an on-demand admin/hospital-manager endpoint here so the whole pipeline can be exercised without extra infrastructure.

---

## 12. Privacy, Security & Safety Boundaries

- All patient/visit/appointment data is **synthetically generated** — see `scripts/generate_dataset.py`. Never treat it as real.
- Passwords hashed with bcrypt; JWT access + refresh tokens; RBAC enforced at the route level.
- The platform explicitly does **not**: diagnose disease, recommend medication/treatment, replace doctors, or make autonomous clinical decisions. It only supports operational forecasting, staffing/capacity planning, and queue/bed management — always as decision support for a human operator.

---

## 13. Future Improvements

- Wire up Alembic migrations (currently `Base.metadata.create_all` on startup).
- Move `run-forecast` to a real Celery/Redis background worker + scheduled beat job.
- Expand the frontend into a full multi-page Next.js/TypeScript app matching the original 16-page spec (Settings, Hospital Events UI, richer Reports UI, dark mode).
- Add SHAP for full Shapley-value explainability (current explainability layer is a fast feature-importance approximation).
- Add PDF report export (CSV is implemented) and forecast-accuracy dashboards (prediction vs. actual).
- Expand automated test coverage to appointments/beds/predictions routers and the alert engine.

---

## Disclaimer

This is an educational/operational prototype built to demonstrate a realistic AI/ML hospital-operations architecture. It is **not** a certified clinical system and must not be used for real patient care or real hospital operations without substantial further engineering, validation, and regulatory review.
