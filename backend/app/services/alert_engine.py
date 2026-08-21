"""
Alert generation & AI recommendation engine.

Runs the trained ML models against current department state and creates
Alert rows + Prediction rows when risk thresholds are crossed. Intended to
be invoked by the scheduled forecasting job (scripts/run_daily_forecast.py)
or on-demand from an admin endpoint — never inline on every dashboard request.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import Department, Alert, AlertSeverityEnum, Prediction
from app.api.predictions import _dept_context
from ml.prediction import predict_service as ps


def _severity_from_risk(risk: str) -> AlertSeverityEnum:
    mapping = {
        "normal": AlertSeverityEnum.INFO,
        "low": AlertSeverityEnum.LOW,
        "moderate": AlertSeverityEnum.MEDIUM,
        "medium": AlertSeverityEnum.MEDIUM,
        "high": AlertSeverityEnum.HIGH,
        "critical": AlertSeverityEnum.CRITICAL,
    }
    return mapping.get(risk, AlertSeverityEnum.INFO)


def recommendation_for_overload(dept_name: str, risk: str, expected_patients: int, capacity: int) -> str:
    if risk in ("high", "critical"):
        return (
            f"{dept_name} is expected to exceed capacity ({expected_patients}/{capacity}). "
            "Recommended actions: 1) Increase staffing during peak hours. "
            "2) Reassign available staff from low-demand departments. "
            "3) Prepare additional beds/overflow capacity. "
            "4) Monitor waiting time every 30 minutes."
        )
    return f"{dept_name} is operating within normal parameters."


def run_daily_predictions_and_alerts(db: Session) -> dict:
    """Generate next-day predictions for every department, store them, and
    raise alerts + recommendations where thresholds are crossed."""
    departments = db.query(Department).all()
    generated_alerts = 0
    generated_predictions = 0

    for d in departments:
        ctx = _dept_context(db, d)
        try:
            demand = ps.predict_demand(
                department_name=d.name, capacity=d.capacity, doctors_available=ctx["doctors_available"],
                prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
            )
            overload = ps.predict_overload(
                department_name=d.name, expected_patients=demand["predicted_patients"], capacity=d.capacity,
                doctors_available=ctx["doctors_available"],
            )
            beds = ps.predict_bed_availability(
                department_name=d.name, total_beds=ctx["total_beds"], capacity=d.capacity,
                prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
            )
        except ps.ModelNotTrainedError:
            continue

        for model_name, value in (("demand_forecast", demand), ("overload_prediction", overload), ("bed_availability", beds)):
            db.add(Prediction(
                model_name=model_name, department_id=d.id, target_date=datetime.utcnow(),
                prediction_value=value, explanation=value.get("explanation"),
            ))
            generated_predictions += 1

        if overload["risk_level"] in ("high", "critical"):
            db.add(Alert(
                title=f"{overload['risk_level'].upper()} OVERLOAD RISK — {d.name}",
                message=(
                    f"Overload probability: {overload['overload_probability']}%. "
                    f"Expected patients: {overload['expected_patients']} / capacity {overload['capacity']}. "
                    + recommendation_for_overload(d.name, overload["risk_level"], overload["expected_patients"], overload["capacity"])
                ),
                severity=_severity_from_risk(overload["risk_level"]),
                department_id=d.id,
            ))
            generated_alerts += 1

        if beds["predicted_available_beds"] < max(3, int(0.1 * beds["total_beds"])):
            db.add(Alert(
                title=f"BED SHORTAGE PREDICTED — {d.name}",
                message=(
                    f"Predicted available beds tomorrow: {beds['predicted_available_beds']} "
                    f"(total {beds['total_beds']}). Consider reallocating beds or expediting discharges."
                ),
                severity=AlertSeverityEnum.HIGH,
                department_id=d.id,
            ))
            generated_alerts += 1

        demand_ratio = demand["predicted_patients"] / max(1, d.avg_handling_capacity)
        if demand_ratio > 1.2:
            pct = round((demand_ratio - 1) * 100, 1)
            db.add(Alert(
                title=f"HIGH DEMAND — {d.name}",
                message=f"Expected patient volume is {pct}% above normal handling capacity.",
                severity=AlertSeverityEnum.MEDIUM,
                department_id=d.id,
            ))
            generated_alerts += 1

    db.commit()
    return {"departments_processed": len(departments), "alerts_generated": generated_alerts,
            "predictions_generated": generated_predictions}
