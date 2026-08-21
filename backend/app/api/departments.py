from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Department, User
from app.schemas.schemas import DepartmentCreate, DepartmentOut
from app.core.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Department).all()


@router.get("/{dept_id}", response_model=DepartmentOut)
def get_department(dept_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.post("", response_model=DepartmentOut, status_code=201)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db),
                       user: User = Depends(require_roles("admin"))):
    dept = Department(**payload.dict())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
