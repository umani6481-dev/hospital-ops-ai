from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Bed, User, BedStatusEnum, AuditLog
from app.schemas.schemas import BedCreate, BedOut, BedStatusUpdate
from app.core.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/beds", tags=["Beds"])


@router.get("", response_model=list[BedOut])
def list_beds(department_id: str | None = None, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    q = db.query(Bed)
    if department_id:
        q = q.filter(Bed.department_id == department_id)
    return q.all()


@router.post("", response_model=BedOut, status_code=201)
def create_bed(payload: BedCreate, db: Session = Depends(get_db),
                user: User = Depends(require_roles("admin"))):
    bed = Bed(**payload.dict())
    db.add(bed)
    db.commit()
    db.refresh(bed)
    return bed


@router.put("/{bed_id}", response_model=BedOut)
def update_bed_status(bed_id: str, payload: BedStatusUpdate, db: Session = Depends(get_db),
                       user: User = Depends(require_roles("admin", "hospital_manager", "department_manager"))):
    bed = db.query(Bed).filter(Bed.id == bed_id).first()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    if payload.status not in [s.value for s in BedStatusEnum]:
        raise HTTPException(status_code=400, detail="Invalid status")
    bed.status = payload.status
    bed.updated_at = datetime.utcnow()
    db.add(AuditLog(user_id=user.id, action="update_bed_status", entity="bed", entity_id=bed_id,
                     details={"status": payload.status}))
    db.commit()
    db.refresh(bed)
    return bed
