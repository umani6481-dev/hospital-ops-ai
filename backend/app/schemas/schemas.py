from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "staff"
    department_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    department_id: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Department ----------
class DepartmentCreate(BaseModel):
    hospital_id: str
    name: str
    capacity: int = 50
    num_doctors: int = 5
    num_staff: int = 10
    num_beds: int = 20
    operating_hours: str = "00:00-23:59"
    avg_handling_capacity: int = 100


class DepartmentOut(DepartmentCreate):
    id: str

    class Config:
        from_attributes = True


# ---------- Bed ----------
class BedCreate(BaseModel):
    department_id: str
    ward: str = "General"
    status: str = "available"


class BedOut(BedCreate):
    id: str

    class Config:
        from_attributes = True


class BedStatusUpdate(BaseModel):
    status: str


# ---------- Patient ----------
class PatientCreate(BaseModel):
    age_group: str
    gender: str
    region: str


class PatientOut(PatientCreate):
    id: str
    registration_date: datetime

    class Config:
        from_attributes = True


# ---------- Appointment ----------
class AppointmentCreate(BaseModel):
    patient_id: str
    department_id: str
    doctor_id: Optional[str] = None
    appointment_date: datetime
    appointment_type: str = "OPD"


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    appointment_date: Optional[datetime] = None
    check_in_time: Optional[datetime] = None
    waiting_time_minutes: Optional[float] = None


class AppointmentOut(BaseModel):
    id: str
    patient_id: str
    department_id: str
    doctor_id: Optional[str]
    appointment_date: datetime
    appointment_type: str
    status: str
    check_in_time: Optional[datetime]
    waiting_time_minutes: Optional[float]

    class Config:
        from_attributes = True


# ---------- Alerts ----------
class AlertOut(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    department_id: Optional[str]
    acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Predictions ----------
class PredictionOut(BaseModel):
    model_name: str
    department_id: Optional[str] = None
    target_date: Optional[datetime] = None
    prediction_value: Any
    confidence: Optional[float] = None
    explanation: Optional[Any] = None
