from sqlalchemy import Column, String, Float, Integer, JSON, Boolean
import uuid
from app.db.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Specialties: list of strings e.g. ["trauma", "cardiac", "burn"]
    specialties = Column(JSON, default=list)

    # Capacity
    icu_beds_available = Column(Integer, default=0)
    trauma_center = Column(Boolean, default=False)
    helipad = Column(Boolean, default=False)
    blood_bank = Column(Boolean, default=False)

    # Rating / response time (minutes)
    avg_response_time_min = Column(Float, default=10.0)
    rating = Column(Float, default=4.0)
