from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Patient, User
from app.schemas.schemas import PatientCreate, PatientOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("", response_model=list[PatientOut])
def list_patients(skip: int = 0, limit: int = 50, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return db.query(Patient).offset(skip).limit(limit).all()


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    patient = Patient(**payload.dict())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: str, payload: PatientCreate, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in payload.dict().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p
