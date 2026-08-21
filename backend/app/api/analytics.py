from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.models import Visit, Bed, BedStatusEnum, Department, User
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_beds = db.query(func.count(Bed.id)).scalar() or 0
    occupied = db.query(func.count(Bed.id)).filter(Bed.status == BedStatusEnum.OCCUPIED).scalar() or 0
    available = db.query(func.count(Bed.id)).filter(Bed.status == BedStatusEnum.AVAILABLE).scalar() or 0
    reserved = db.query(func.count(Bed.id)).filter(Bed.status == BedStatusEnum.RESERVED).scalar() or 0
    occupancy_rate = round((occupied / total_beds) * 100, 1) if total_beds else 0.0

    last_30d = datetime.utcnow() - timedelta(days=30)
    total_patients = db.query(func.count(Visit.id)).filter(Visit.arrival_time >= last_30d).scalar() or 0
    avg_wait = db.query(func.avg(Visit.waiting_time_minutes)).filter(
        Visit.arrival_time >= last_30d, Visit.waiting_time_minutes.isnot(None)
    ).scalar()

    return {
        "total_beds": total_beds,
        "occupied_beds": occupied,
        "available_beds": available,
        "reserved_beds": reserved,
        "occupancy_rate": occupancy_rate,
        "patients_last_30_days": total_patients,
        "avg_waiting_time_minutes": round(avg_wait, 1) if avg_wait else None,
    }


@router.get("/departments")
def department_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    departments = db.query(Department).all()
    results = []
    for d in departments:
        beds_total = db.query(func.count(Bed.id)).filter(Bed.department_id == d.id).scalar() or 0
        beds_occupied = db.query(func.count(Bed.id)).filter(
            Bed.department_id == d.id, Bed.status == BedStatusEnum.OCCUPIED
        ).scalar() or 0
        visits_30d = db.query(func.count(Visit.id)).filter(
            Visit.department_id == d.id, Visit.arrival_time >= datetime.utcnow() - timedelta(days=30)
        ).scalar() or 0
        results.append({
            "department_id": d.id,
            "name": d.name,
            "capacity": d.capacity,
            "beds_total": beds_total,
            "beds_occupied": beds_occupied,
            "occupancy_rate": round((beds_occupied / beds_total) * 100, 1) if beds_total else 0.0,
            "visits_last_30_days": visits_30d,
        })
    return results


@router.get("/emergency")
def emergency_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.models import VisitTypeEnum
    last_24h = datetime.utcnow() - timedelta(hours=24)
    arrivals = db.query(func.count(Visit.id)).filter(
        Visit.visit_type == VisitTypeEnum.EMERGENCY, Visit.arrival_time >= last_24h
    ).scalar() or 0
    avg_wait = db.query(func.avg(Visit.waiting_time_minutes)).filter(
        Visit.visit_type == VisitTypeEnum.EMERGENCY, Visit.arrival_time >= last_24h
    ).scalar()
    max_wait = db.query(func.max(Visit.waiting_time_minutes)).filter(
        Visit.visit_type == VisitTypeEnum.EMERGENCY, Visit.arrival_time >= last_24h
    ).scalar()
    currently_waiting = db.query(func.count(Visit.id)).filter(
        Visit.visit_type == VisitTypeEnum.EMERGENCY, Visit.departure_time.is_(None)
    ).scalar() or 0
    return {
        "arrivals_last_24h": arrivals,
        "avg_waiting_time_minutes": round(avg_wait, 1) if avg_wait else None,
        "max_waiting_time_minutes": round(max_wait, 1) if max_wait else None,
        "patients_currently_waiting": currently_waiting,
    }


@router.get("/beds")
def bed_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    by_status = db.query(Bed.status, func.count(Bed.id)).group_by(Bed.status).all()
    return {status.value: count for status, count in by_status}
