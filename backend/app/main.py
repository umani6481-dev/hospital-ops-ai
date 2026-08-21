from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.session import Base, engine
from app.models import models  # noqa: F401  (ensures models are registered)

from app.api import auth, patients, appointments, departments, beds, analytics, predictions, alerts, admin, chatbot

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI/ML-powered Hospital Operations Intelligence Platform — forecasting, "
        "capacity planning, and decision support for hospital administrators. "
        "This is an OPERATIONS MANAGEMENT system, NOT a medical diagnosis or "
        "treatment system, and does not provide clinical/medical advice."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(departments.router)
app.include_router(beds.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(admin.router)
app.include_router(chatbot.router)


@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Hospital Operations AI API",
        "docs": "/api/docs",
        "disclaimer": "Operations-management decision support only. Not a medical diagnosis or treatment system.",
    }
