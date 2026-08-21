import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database.session import Base


def gen_uuid():
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    HOSPITAL_MANAGER = "hospital_manager"
    DEPARTMENT_MANAGER = "department_manager"
    STAFF = "staff"


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.STAFF)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="users")


class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    address = Column(String)
    total_capacity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    departments = relationship("Department", back_populates="hospital")


class Department(Base):
    __tablename__ = "departments"
    id = Column(String, primary_key=True, default=gen_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"))
    name = Column(String, nullable=False)
    capacity = Column(Integer, default=50)
    num_doctors = Column(Integer, default=5)
    num_staff = Column(Integer, default=10)
    num_beds = Column(Integer, default=20)
    operating_hours = Column(String, default="00:00-23:59")
    avg_handling_capacity = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    hospital = relationship("Hospital", back_populates="departments")
    users = relationship("User", back_populates="department")
    doctors = relationship("Doctor", back_populates="department")
    beds = relationship("Bed", back_populates="department")


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(String, primary_key=True, default=gen_uuid)
    department_id = Column(String, ForeignKey("departments.id"))
    full_name = Column(String, nullable=False)
    specialization = Column(String)
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="doctors")


class Staff(Base):
    __tablename__ = "staff"
    id = Column(String, primary_key=True, default=gen_uuid)
    department_id = Column(String, ForeignKey("departments.id"))
    full_name = Column(String, nullable=False)
    role_title = Column(String)
    shift = Column(String)
    is_active = Column(Boolean, default=True)


class BedStatusEnum(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"


class Bed(Base):
    __tablename__ = "beds"
    id = Column(String, primary_key=True, default=gen_uuid)
    department_id = Column(String, ForeignKey("departments.id"))
    ward = Column(String, default="General")
    status = Column(Enum(BedStatusEnum), default=BedStatusEnum.AVAILABLE)
    updated_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="beds")


class VisitTypeEnum(str, enum.Enum):
    OPD = "OPD"
    EMERGENCY = "Emergency"
    FOLLOW_UP = "Follow-up"
    APPOINTMENT = "Appointment"
    WALK_IN = "Walk-in"


class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, default=gen_uuid)
    age_group = Column(String)
    gender = Column(String)
    region = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)


class Visit(Base):
    __tablename__ = "visits"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"))
    department_id = Column(String, ForeignKey("departments.id"))
    visit_type = Column(Enum(VisitTypeEnum), default=VisitTypeEnum.OPD)
    arrival_time = Column(DateTime)
    departure_time = Column(DateTime, nullable=True)
    waiting_time_minutes = Column(Float, nullable=True)
    visit_status = Column(String, default="completed")


class AppointmentStatusEnum(str, enum.Enum):
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_id = Column(String, ForeignKey("patients.id"))
    department_id = Column(String, ForeignKey("departments.id"))
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=True)
    appointment_date = Column(DateTime, nullable=False)
    appointment_type = Column(String, default="OPD")
    status = Column(Enum(AppointmentStatusEnum), default=AppointmentStatusEnum.SCHEDULED)
    check_in_time = Column(DateTime, nullable=True)
    waiting_time_minutes = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SeverityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HospitalEvent(Base):
    __tablename__ = "hospital_events"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    severity = Column(Enum(SeverityEnum), default=SeverityEnum.LOW)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StaffSchedule(Base):
    __tablename__ = "staff_schedules"
    id = Column(String, primary_key=True, default=gen_uuid)
    staff_id = Column(String, ForeignKey("staff.id"))
    shift_date = Column(DateTime)
    shift_type = Column(String)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(String, primary_key=True, default=gen_uuid)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    algorithm = Column(String)
    dataset_version = Column(String)
    metrics = Column(JSON)
    feature_list = Column(JSON)
    trained_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(String, primary_key=True, default=gen_uuid)
    model_name = Column(String, nullable=False)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    target_date = Column(DateTime)
    prediction_value = Column(JSON)
    confidence = Column(Float, nullable=True)
    explanation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertSeverityEnum(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    message = Column(Text)
    severity = Column(Enum(AlertSeverityEnum), default=AlertSeverityEnum.INFO)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
