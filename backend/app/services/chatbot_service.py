"""
Rule-based chatbot for the Hospital Operations AI dashboard.
Knowledge base built directly from the project's README, so every
answer matches what is actually implemented in this repository.

Uses keyword + fuzzy matching (Python's built-in difflib) so it can
tolerate small spelling mistakes without needing any external API or
extra package installs.
"""
import difflib
import re

# ---------------------------------------------------------------------
# Knowledge base: each intent has a list of trigger keywords/phrases
# and a detailed, easy-to-understand answer.
# ---------------------------------------------------------------------
INTENTS = [
    {
        "name": "greeting",
        "keywords": ["hi", "hello", "hey", "salam", "assalam", "hlo"],
        "answer": (
            "Hello! I'm the Hospital Operations AI assistant. I can answer "
            "questions about this dashboard — beds, alerts, patient demand "
            "predictions, departments, roles, reports, and more. What would "
            "you like to know?"
        ),
    },
    {
        "name": "what_is_this",
        "keywords": ["what is this", "about this project", "what does this do", "purpose", "this app", "this platform"],
        "answer": (
            "This is the Hospital Operations AI platform — an AI/ML-powered "
            "OPERATIONS MANAGEMENT tool for hospital administrators. It "
            "forecasts patient demand, predicts department overload risk, "
            "estimates emergency waiting times, forecasts bed availability, "
            "and predicts appointment no-shows. It also has explainable AI, "
            "role-based access control, automatic alerts, and a live "
            "dashboard. Important: it is NOT a medical diagnosis or "
            "treatment system, and all data here is synthetic/demo data."
        ),
    },
    {
        "name": "beds",
        "keywords": ["bed", "beds", "occupancy", "vacant", "available bed", "bed availability", "bed shortage"],
        "answer": (
            "The 'Beds' page shows real-time bed occupancy and availability "
            "across all departments, so you can see how many beds are free "
            "vs occupied at a glance. On the AI Predictions page, there is "
            "also a 'Bed Availability Forecast' (trained with Random Forest "
            "and XGBoost) that predicts how many beds are likely to be free "
            "tomorrow. If predicted availability gets too low, the Alert "
            "Engine automatically raises a BED SHORTAGE alert."
        ),
    },
    {
        "name": "alerts",
        "keywords": ["alert", "alerts", "notification", "warning", "overload alert", "alert engine"],
        "answer": (
            "The 'Alerts' page lists alerts that the system generates "
            "automatically — HIGH DEMAND, OVERLOAD, and BED SHORTAGE — each "
            "one comes with an AI-generated recommendation for what action "
            "to take. New alerts are created whenever the forecast job runs "
            "(either by clicking 'Run Forecast Job & Generate Alerts', or "
            "automatically once a day in production via a scheduler)."
        ),
    },
    {
        "name": "predictions_overview",
        "keywords": ["ai predictions", "prediction page", "how many models", "5 models", "ml models"],
        "answer": (
            "The AI Predictions page brings together 5 trained ML models: "
            "1) Patient Demand Forecasting, 2) Department Overload "
            "Prediction, 3) Emergency/Department Waiting-Time Prediction, "
            "4) Bed Availability Forecasting, and 5) Appointment No-Show "
            "Prediction. Each model was trained on multiple algorithms and "
            "the best one was automatically selected using time-aware "
            "validation (training on earlier dates, testing on later ones, "
            "so there's no data leakage from the future)."
        ),
    },
    {
        "name": "predictions_demand",
        "keywords": ["demand", "forecast", "predicted patients", "patient demand", "demand forecasting"],
        "answer": (
            "Patient Demand Forecasting predicts tomorrow's expected patient "
            "volume for each department. It was trained by comparing Linear "
            "Regression, Random Forest, and XGBoost, and the best-performing "
            "one was kept. On the dashboard you'll see a number per "
            "department plus a confidence range and the top factors (like "
            "department capacity or last week's volume) driving that "
            "prediction — this is the model's built-in explainability."
        ),
    },
    {
        "name": "predictions_overload",
        "keywords": ["overload", "risk", "department overload", "capacity risk", "overload prediction"],
        "answer": (
            "Department Overload Prediction estimates how likely each "
            "department is to be overloaded tomorrow, using a 4-class risk "
            "scale (Low / Medium / High / Critical). It was trained by "
            "comparing Logistic Regression, Random Forest, and XGBoost. "
            "When risk is high, the Alert Engine automatically creates an "
            "OVERLOAD alert with a recommended action."
        ),
    },
    {
        "name": "predictions_waiting",
        "keywords": ["waiting time", "wait time", "queue", "emergency wait", "waiting time prediction"],
        "answer": (
            "The Waiting-Time Prediction model estimates how long patients "
            "are likely to wait in Emergency and other departments. It was "
            "trained by comparing Gradient Boosting, Random Forest, and "
            "XGBoost, so hospital managers can plan staffing ahead of time "
            "instead of reacting after queues build up."
        ),
    },
    {
        "name": "predictions_noshow",
        "keywords": ["no show", "noshow", "no-show", "missed appointment", "no show prediction"],
        "answer": (
            "Appointment No-Show Prediction estimates the probability that "
            "a scheduled patient won't show up for their appointment. It "
            "compares Logistic Regression, Random Forest, and XGBoost. "
            "Staff can use this to decide who might need a reminder call or "
            "which slots are safe to slightly overbook."
        ),
    },
    {
        "name": "explainability",
        "keywords": ["explainability", "explainable", "why this prediction", "top factors", "feature importance", "shap"],
        "answer": (
            "Every prediction on this dashboard comes with an explanation, "
            "not just a bare number. The explainability layer combines each "
            "model's feature importance with the actual feature values used "
            "for that specific prediction, to surface the top contributing "
            "factors — similar in spirit to SHAP, but optimized to be fast "
            "enough for interactive use. Full Shapley-value (SHAP) "
            "explainability is listed as a future improvement."
        ),
    },
    {
        "name": "departments",
        "keywords": ["department", "departments", "ward", "unit"],
        "answer": (
            "The 'Departments' page lists all hospital departments (e.g. "
            "Emergency, Cardiology, Pediatrics, OPD - General Medicine, "
            "Orthopedics, Radiology) along with their capacity and current "
            "status. Departments are the central hub the predictions, "
            "alerts, and staff/bed data are all organized around."
        ),
    },
    {
        "name": "emergency",
        "keywords": ["emergency", "er", "arrivals", "emergency arrivals"],
        "answer": (
            "The 'Emergency' page tracks emergency arrivals and related "
            "metrics in real time, separate from the general department "
            "view — including how many arrivals happened in the last 24 "
            "hours and the current predicted peak risk."
        ),
    },
    {
        "name": "patients",
        "keywords": ["patient", "patients", "patient record", "patient crud"],
        "answer": (
            "The 'Patients' page lets authorized roles view, add, update, "
            "or remove patient records (full CRUD). Every patient record in "
            "this project is synthetic/demo data generated by the dataset "
            "generator — never real patient data."
        ),
    },
    {
        "name": "appointments",
        "keywords": ["appointment", "appointments", "booking", "schedule visit"],
        "answer": (
            "The 'Appointments' page shows scheduled patient appointments "
            "and lets authorized roles create, update, or cancel them (full "
            "CRUD). This data also feeds the No-Show Prediction model."
        ),
    },
    {
        "name": "audit_logs",
        "keywords": ["audit", "audit log", "logs", "activity log"],
        "answer": (
            "The 'Audit Logs' page records who did what and when across "
            "the system — useful for accountability, security review, and "
            "tracing back any changes made by staff or managers."
        ),
    },
    {
        "name": "model_performance",
        "keywords": ["model performance", "accuracy", "ml model metrics", "model metrics", "mae", "rmse", "r2", "f1"],
        "answer": (
            "The 'Model Performance' page (served by the /api/models/"
            "performance endpoint) shows each of the 5 models' algorithm, "
            "version, dataset version, and evaluation metrics — MAE, RMSE, "
            "MAPE, R² for regression models (Demand, Waiting Time, Beds), "
            "and Accuracy, F1, ROC-AUC for classification models (Overload, "
            "No-Show). This tells you how reliable each prediction is."
        ),
    },
    {
        "name": "roles",
        "keywords": ["role", "roles", "admin", "manager", "staff account", "permission", "rbac", "access control"],
        "answer": (
            "This platform has 4 roles enforced by JWT auth + RBAC: Admin, "
            "Hospital Manager, Department Manager, and Staff. Permissions "
            "are enforced at the API route level — for example, running the "
            "forecast job or seeing certain admin actions is typically "
            "restricted to Admin/Hospital Manager, while Department "
            "Managers and Staff see more limited views."
        ),
    },
    {
        "name": "login",
        "keywords": ["login", "sign in", "password", "logout", "sign out", "demo account", "demo credentials"],
        "answer": (
            "You can sign in with the demo account buttons on the login "
            "page: Admin (admin@hospital-ops.demo / Admin@123), Hospital "
            "Manager (manager@hospital-ops.demo / Manager@123), Department "
            "Manager (deptmanager@hospital-ops.demo / DeptMgr@123), or "
            "Staff (staff@hospital-ops.demo / Staff@123). These are created "
            "automatically by the seed script. Use 'Sign out' in the "
            "sidebar to log out."
        ),
    },
    {
        "name": "report",
        "keywords": ["report", "export", "csv", "download report", "reports export"],
        "answer": (
            "You can export operational reports as CSV files via the "
            "/api/reports/export endpoint, covering patients, appointments, "
            "and analytics data. PDF report export is planned as a future "
            "improvement but not implemented yet."
        ),
    },
    {
        "name": "run_forecast",
        "keywords": ["run forecast", "generate alerts", "forecast job", "run forecast job"],
        "answer": (
            "The 'Run Forecast Job & Generate Alerts' button (which calls "
            "POST /api/admin/run-forecast) re-runs all 5 ML models and "
            "creates fresh alerts based on the latest predictions. In "
            "production this same pipeline (app/services/alert_engine.py) "
            "is meant to run automatically every day at midnight via a "
            "scheduler such as cron or Celery beat — here it's exposed as "
            "an on-demand button so you can try it without extra "
            "infrastructure."
        ),
    },
    {
        "name": "analytics",
        "keywords": ["analytics", "occupancy analytics", "department performance", "metrics api"],
        "answer": (
            "The Analytics APIs (/api/analytics/*) power the dashboard's "
            "summary numbers — things like overall bed occupancy, emergency "
            "metrics, and department-level performance comparisons."
        ),
    },
    {
        "name": "tech_stack",
        "keywords": ["tech stack", "technology used", "built with", "which framework", "backend framework"],
        "answer": (
            "Backend: Python, FastAPI, SQLAlchemy, Pydantic. ML: pandas, "
            "NumPy, scikit-learn, XGBoost, joblib. Database: SQLite for "
            "local development, PostgreSQL when running via Docker. Auth: "
            "JWT (python-jose) with bcrypt password hashing. Frontend: "
            "vanilla JavaScript single-page app with Tailwind CSS and "
            "Chart.js. Infra: Docker, Docker Compose, Nginx. Testing: "
            "pytest with FastAPI's TestClient."
        ),
    },
    {
        "name": "database_schema",
        "keywords": ["database schema", "tables", "db schema", "database structure"],
        "answer": (
            "The database has these main tables: users, roles, hospitals, "
            "departments, doctors, staff, patients, appointments, visits, "
            "beds, hospital_events, staff_schedules, predictions, "
            "model_versions, alerts, and audit_logs. The key relationships "
            "are: Hospital → Departments → Doctors/Staff/Beds, "
            "Patients → Appointments/Visits, and "
            "Departments → Predictions → Alerts."
        ),
    },
    {
        "name": "docker",
        "keywords": ["docker", "docker compose", "container", "containerize"],
        "answer": (
            "Running `docker compose up --build` starts everything at once: "
            "PostgreSQL, Redis, the FastAPI backend (port 8000), and the "
            "Nginx-served frontend (port 8080). After the containers are "
            "up, you still need to run the data-generation, model-training, "
            "and seed-database commands once inside the backend container "
            "(using `docker compose exec backend ...`) before predictions "
            "will work."
        ),
    },
    {
        "name": "testing",
        "keywords": ["testing", "pytest", "test suite", "run tests"],
        "answer": (
            "Automated tests live in backend/tests and run with `pytest "
            "tests/ -v`. They cover the health check endpoint, "
            "registration/login, RBAC enforcement (making sure unauthorized "
            "roles get a 403), patient CRUD, and ML feature-engineering "
            "correctness such as lag features and overload label "
            "thresholds."
        ),
    },
    {
        "name": "synthetic_data",
        "keywords": ["synthetic data", "dataset generator", "fake data", "generate dataset", "demo data"],
        "answer": (
            "All data in this project — patients, visits, appointments — is "
            "generated by scripts/generate_dataset.py, a synthetic data "
            "generator that creates 12+ months of history, 100,000+ visit "
            "records, and 49,000+ appointments. None of it is real patient "
            "data, which keeps the whole project safe to run and share."
        ),
    },
    {
        "name": "environment_variables",
        "keywords": ["env variable", ".env", "environment variable", "secret key", "database url", "cors origins"],
        "answer": (
            "Configuration lives in backend/.env (copied from .env.example): "
            "DATABASE_URL (defaults to SQLite for local dev, or a "
            "PostgreSQL URL for Docker), SECRET_KEY and JWT_SECRET for "
            "auth, REDIS_URL for background workers, MODEL_PATH for where "
            "trained models are stored, and CORS_ORIGINS for which frontend "
            "URLs are allowed to call the API. `.env` itself should never "
            "be committed to version control."
        ),
    },
    {
        "name": "privacy_safety",
        "keywords": ["diagnose", "diagnosis", "medicine", "treatment", "disease", "prescribe", "medical advice", "safety", "privacy"],
        "answer": (
            "This platform is strictly an operations-management "
            "decision-support tool. It does NOT diagnose disease, "
            "recommend medication or treatment, replace doctors, or make "
            "autonomous clinical decisions — it only supports operational "
            "forecasting, staffing/capacity planning, and queue/bed "
            "management as decision support for a human operator. All "
            "patient/visit/appointment data is synthetic. Passwords are "
            "hashed with bcrypt, and access is controlled with JWT + RBAC "
            "at the route level."
        ),
    },
    {
        "name": "future_improvements",
        "keywords": ["future improvement", "roadmap", "not yet implemented", "coming soon", "limitations"],
        "answer": (
            "Known simplifications/roadmap items: Alembic migrations aren't "
            "wired up yet (tables are created directly by SQLAlchemy); "
            "the forecast job runs synchronously on-demand rather than via "
            "a real Celery/Redis background worker; the frontend is a "
            "single-page dashboard rather than the full multi-page Next.js "
            "spec (no Settings page, Hospital Events UI, or dark mode yet); "
            "full SHAP-based explainability, PDF report export, and wider "
            "automated test coverage (appointments/beds/predictions "
            "routers, alert engine) are also planned but not done."
        ),
    },
    {
        "name": "api_docs",
        "keywords": ["api docs", "swagger", "redoc", "api documentation", "endpoints list"],
        "answer": (
            "Interactive API documentation is auto-generated by FastAPI: "
            "Swagger UI at http://localhost:8000/api/docs and ReDoc at "
            "http://localhost:8000/api/redoc. Key endpoint groups include "
            "/api/auth/*, /api/patients, /api/appointments, "
            "/api/departments, /api/beds, /api/analytics/*, "
            "/api/predictions/*, /api/alerts/*, /api/admin/run-forecast, "
            "/api/models/performance, /api/reports/export, and "
            "/api/audit-logs."
        ),
    },
]

FALLBACK_ANSWER = (
    "Sorry, I can only help with questions about this dashboard's features "
    "— beds, alerts, the 5 AI predictions, departments, patients, "
    "appointments, roles, model performance, reports, and how the system "
    "works under the hood. Could you rephrase your question?"
)


def _tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [w for w in text.split() if w]


def get_chatbot_reply(message: str) -> str:
    """Return the best-matching answer for a free-text user message."""
    if not message or not message.strip():
        return "Please type a question about the dashboard's features."

    words = _tokenize(message)
    if not words:
        return FALLBACK_ANSWER

    # Build a flat list of (keyword, intent_index) pairs for fuzzy lookup
    all_keyword_pairs = []
    for idx, intent in enumerate(INTENTS):
        for kw in intent["keywords"]:
            all_keyword_pairs.append((kw, idx))

    all_keywords = [kw for kw, _ in all_keyword_pairs]

    scores = [0] * len(INTENTS)

    # 1. Direct substring match on the full message (handles multi-word keywords)
    lowered_message = " ".join(words)
    for kw, idx in all_keyword_pairs:
        if kw in lowered_message:
            scores[idx] += 2

    # 2. Fuzzy match word-by-word (handles small spelling mistakes)
    for word in words:
        matches = difflib.get_close_matches(word, all_keywords, n=1, cutoff=0.8)
        if matches:
            matched_kw = matches[0]
            for kw, idx in all_keyword_pairs:
                if kw == matched_kw:
                    scores[idx] += 1

    best_idx = max(range(len(scores)), key=lambda i: scores[i])
    if scores[best_idx] == 0:
        return FALLBACK_ANSWER

    return INTENTS[best_idx]["answer"]