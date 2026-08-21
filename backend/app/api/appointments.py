from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Appointment, User, AppointmentStatusEnum
from app.schemas.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.get("", response_model=list[AppointmentOut])
def list_appointments(department_id: str | None = None, doctor_id: str | None = None,
                       status: str | None = None, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    q = db.query(Appointment)
    if department_id:
        q = q.filter(Appointment.department_id == department_id)
    if doctor_id:
        q = q.filter(Appointment.doctor_id == doctor_id)
    if status:
        q = q.filter(Appointment.status == status)
    return q.order_by(Appointment.appointment_date.desc()).limit(200).all()


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    appt = Appointment(**payload.dict())
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.put("/{appt_id}", response_model=AppointmentOut)
def update_appointment(appt_id: str, payload: AppointmentUpdate, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    data = payload.dict(exclude_unset=True)
    if "status" in data and data["status"] not in [s.value for s in AppointmentStatusEnum]:
        raise HTTPException(status_code=400, detail="Invalid status")
    for k, v in data.items():
        setattr(appt, k, v)
    db.commit()
    db.refresh(appt)
    return appt


@router.delete("/{appt_id}", status_code=204)
def cancel_appointment(appt_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = AppointmentStatusEnum.CANCELLED
    db.commit()
    return None
