from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text, Enum
from sqlalchemy.sql import func
import enum
import uuid
from app.db.database import Base


class SeverityLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    SEVERE = "SEVERE"
    MODERATE = "MODERATE"
    MILD = "MILD"
    UNKNOWN = "UNKNOWN"


class EmergencyType(str, enum.Enum):
    ROAD_ACCIDENT = "road_accident"
    CARDIAC_ARREST = "cardiac_arrest"
    STROKE = "stroke"
    DROWNING = "drowning"
    FIRE_BURN = "fire_burn"
    FRACTURE = "fracture"
    HEAD_INJURY = "head_injury"
    BLEEDING = "bleeding"
    UNKNOWN = "unknown"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Input data
    input_text = Column(Text, nullable=True)
    input_image_path = Column(String, nullable=True)
    input_audio_path = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # AI Analysis results
    emergency_type = Column(String, default=EmergencyType.UNKNOWN)
    severity_score = Column(Float, default=0.0)   # 0-100
    severity_level = Column(String, default=SeverityLevel.UNKNOWN)
    survival_probability = Column(Float, default=0.0)  # 0-1
    confidence_score = Column(Float, default=0.0)

    # Guidance
    first_aid_steps = Column(JSON, default=list)
    warnings = Column(JSON, default=list)

    # Assigned hospital
    assigned_hospital_id = Column(String, nullable=True)
    ambulance_dispatched = Column(Integer, default=0)  # boolean as int for compat

    # Full AI report
    ai_report = Column(JSON, nullable=True)

    status = Column(String, default="active")
