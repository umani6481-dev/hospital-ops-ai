from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.models import Department, Bed, Visit, BedStatusEnum, VisitTypeEnum, User, Prediction
from app.core.deps import get_current_user
from ml.prediction import predict_service as ps

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


def _dept_context(db: Session, dept: Department):
    """Derive live feature inputs for a department from current DB state."""
    now = datetime.utcnow()
    last_1d = now - timedelta(days=1)
    last_7d = now - timedelta(days=7)
    last_14d = now - timedelta(days=14)

    prev_day = db.query(func.count(Visit.id)).filter(
        Visit.department_id == dept.id, Visit.arrival_time >= last_1d
    ).scalar() or dept.avg_handling_capacity
    prev_week = db.query(func.count(Visit.id)).filter(
        Visit.department_id == dept.id, Visit.arrival_time >= last_7d, Visit.arrival_time < last_7d + timedelta(days=1)
    ).scalar() or dept.avg_handling_capacity
    ma7 = db.query(func.count(Visit.id)).filter(
        Visit.department_id == dept.id, Visit.arrival_time >= last_7d
    ).scalar() or dept.avg_handling_capacity
    ma7 = ma7 / 7
    ma14 = db.query(func.count(Visit.id)).filter(
        Visit.department_id == dept.id, Visit.arrival_time >= last_14d
    ).scalar() or dept.avg_handling_capacity
    ma14 = ma14 / 14

    total_beds = db.query(func.count(Bed.id)).filter(Bed.department_id == dept.id).scalar() or dept.num_beds
    occupied_beds = db.query(func.count(Bed.id)).filter(
        Bed.department_id == dept.id, Bed.status == BedStatusEnum.OCCUPIED
    ).scalar() or 0

    return {
        "prev_day_demand": float(prev_day),
        "prev_week_demand": float(prev_week),
        "ma_7": float(ma7),
        "ma_14": float(ma14),
        "total_beds": total_beds or dept.num_beds,
        "occupied_beds": occupied_beds,
        "doctors_available": dept.num_doctors,
    }


def _handle_missing_model(e: Exception):
    raise HTTPException(status_code=503, detail=str(e))


@router.get("/demand")
def demand_forecast(department_id: str | None = None, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    depts = db.query(Department).filter(Department.id == department_id).all() if department_id else db.query(Department).all()
    if not depts:
        raise HTTPException(status_code=404, detail="Department(s) not found")
    results = []
    try:
        for d in depts:
            ctx = _dept_context(db, d)
            results.append(ps.predict_demand(
                department_name=d.name, capacity=d.capacity, doctors_available=ctx["doctors_available"],
                prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
            ))
    except ps.ModelNotTrainedError as e:
        _handle_missing_model(e)
    return results


@router.get("/overload")
def overload_prediction(department_id: str | None = None, db: Session = Depends(get_db),
                         user: User = Depends(get_current_user)):
    depts = db.query(Department).filter(Department.id == department_id).all() if department_id else db.query(Department).all()
    if not depts:
        raise HTTPException(status_code=404, detail="Department(s) not found")
    results = []
    try:
        for d in depts:
            ctx = _dept_context(db, d)
            expected = ps.predict_demand(
                department_name=d.name, capacity=d.capacity, doctors_available=ctx["doctors_available"],
                prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
            )["predicted_patients"]
            results.append(ps.predict_overload(
                department_name=d.name, expected_patients=expected, capacity=d.capacity,
                doctors_available=ctx["doctors_available"],
            ))
    except ps.ModelNotTrainedError as e:
        _handle_missing_model(e)
    return results


@router.get("/waiting-time")
def waiting_time_prediction(department_id: str | None = None, db: Session = Depends(get_db),
                             user: User = Depends(get_current_user)):
    depts = db.query(Department).filter(Department.id == department_id).all() if department_id else db.query(Department).all()
    if not depts:
        raise HTTPException(status_code=404, detail="Department(s) not found")
    results = []
    try:
        for d in depts:
            ctx = _dept_context(db, d)
            occ_ratio = ctx["occupied_beds"] / max(1, ctx["total_beds"])
            expected = int(ctx["ma_7"])
            results.append(ps.predict_waiting_time(
                department_name=d.name, expected_patients=expected, capacity=d.capacity,
                occupancy_ratio=occ_ratio, doctors_available=ctx["doctors_available"],
            ))
    except ps.ModelNotTrainedError as e:
        _handle_missing_model(e)
    return results


@router.get("/beds")
def bed_prediction(department_id: str | None = None, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    depts = db.query(Department).filter(Department.id == department_id).all() if department_id else db.query(Department).all()
    if not depts:
        raise HTTPException(status_code=404, detail="Department(s) not found")
    results = []
    try:
        for d in depts:
            ctx = _dept_context(db, d)
            results.append(ps.predict_bed_availability(
                department_name=d.name, total_beds=ctx["total_beds"], capacity=d.capacity,
                prev_day_demand=ctx["prev_day_demand"], prev_week_demand=ctx["prev_week_demand"],
                ma_7=ctx["ma_7"], ma_14=ctx["ma_14"],
            ))
    except ps.ModelNotTrainedError as e:
        _handle_missing_model(e)
    return results


@router.get("/no-show")
def no_show_prediction(department_id: str, lead_time_days: int = 3, appointment_type: str = "OPD",
                        age_group: str = "19-35", db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    try:
        result = ps.predict_no_show(
            lead_time_days=lead_time_days, day_of_week=datetime.utcnow().weekday(),
            previous_cancellations=0, department_name=dept.name,
            appointment_type=appointment_type, age_group=age_group,
        )
    except ps.ModelNotTrainedError as e:
        _handle_missing_model(e)
    return result
