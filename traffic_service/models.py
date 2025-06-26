# traffic_service/models.py
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from traffic_service.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class TrafficZone(Base):
    __tablename__ = "traffic_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    vehicle_count = Column(Integer)