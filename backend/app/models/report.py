from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


class EmergencyReport(Base):
    __tablename__ = "emergency_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Report content
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    full_report = Column(JSON, nullable=True)    # Structured JSON report

    # File paths
    pdf_path = Column(String, nullable=True)

    generated_by = Column(String, default="RapidCare AI v1.0")
