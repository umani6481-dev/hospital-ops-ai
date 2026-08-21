import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import User, Visit, Appointment, AuditLog
from app.core.deps import get_current_user, require_roles
from app.services.alert_engine import run_daily_predictions_and_alerts
from ml.prediction import predict_service as ps

router = APIRouter(prefix="/api", tags=["Admin & Reports"])

MODEL_FILE_MAP = {
    "demand_forecast": "demand_model",
    "overload_prediction": "overload_model",
    "waiting_time_prediction": "waiting_time_model",
    "bed_availability": "bed_model",
    "no_show_prediction": "noshow_model",
}


@router.post("/admin/run-forecast", tags=["Admin & Reports"])
def trigger_forecast(db: Session = Depends(get_db),
                      user: User = Depends(require_roles("admin", "hospital_manager"))):
    """Manually trigger the scheduled daily forecasting + alert generation job
    (in production this runs automatically every day at 00:00 via a scheduler)."""
    result = run_daily_predictions_and_alerts(db)
    db.add(AuditLog(user_id=user.id, action="run_forecast", entity="system", details=result))
    db.commit()
    return result


@router.get("/models/performance", tags=["Admin & Reports"])
def model_performance(user: User = Depends(get_current_user)):
    performance = {}
    for display_name, file_prefix in MODEL_FILE_MAP.items():
        try:
            performance[display_name] = ps.load_model_metadata(file_prefix)
        except ps.ModelNotTrainedError:
            performance[display_name] = {"status": "not_trained"}
    return performance


@router.get("/reports/export", tags=["Admin & Reports"])
def export_report(report_type: str = "visits", db: Session = Depends(get_db),
                   user: User = Depends(require_roles("admin", "hospital_manager", "department_manager"))):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "visits":
        writer.writerow(["id", "department_id", "visit_type", "arrival_time", "waiting_time_minutes", "visit_status"])
        for v in db.query(Visit).limit(5000).all():
            writer.writerow([v.id, v.department_id, v.visit_type.value if v.visit_type else "", v.arrival_time,
                              v.waiting_time_minutes, v.visit_status])
    elif report_type == "appointments":
        writer.writerow(["id", "department_id", "appointment_date", "status", "waiting_time_minutes"])
        for a in db.query(Appointment).limit(5000).all():
            writer.writerow([a.id, a.department_id, a.appointment_date, a.status.value if a.status else "",
                              a.waiting_time_minutes])
    else:
        raise HTTPException(status_code=400, detail="Unknown report_type. Use 'visits' or 'appointments'.")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"},
    )


@router.get("/audit-logs", tags=["Admin & Reports"])
def get_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                    user: User = Depends(require_roles("admin"))):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return [{"id": l.id, "user_id": l.user_id, "action": l.action, "entity": l.entity,
              "entity_id": l.entity_id, "details": l.details, "created_at": l.created_at} for l in logs]
