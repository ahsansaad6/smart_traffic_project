from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

app = FastAPI()

# Database Setup for incidents
INCIDENT_DATABASE_URL = "sqlite:///./incidents.db"
incident_engine = create_engine(INCIDENT_DATABASE_URL)
IncidentBase = declarative_base()
IncidentSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=incident_engine)

# Define the Incident model
class Incident(IncidentBase):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    location = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

IncidentBase.metadata.create_all(bind=incident_engine)

# Pydantic models
class IncidentBaseModel(BaseModel):
    type: str
    location: str

class IncidentCreate(IncidentBaseModel):
    pass

class IncidentUpdate(BaseModel):
    type: Optional[str] = None
    location: Optional[str] = None

class IncidentResponse(IncidentBaseModel):
    id: int
    timestamp: datetime

# Dependency to get the incident database session
def get_incident_db():
    db = IncidentSessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD Operations for Incidents
def create_incident(db: Session, incident: IncidentCreate):
    db_incident = Incident(**incident.dict())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_incidents(db: Session):
    return db.query(Incident).all()

def get_incident_by_id(db: Session, incident_id: int):
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db_incident

def update_incident(db: Session, incident_id: int, incident_update: IncidentUpdate):
    db_incident = get_incident_by_id(db, incident_id)
    update_data = incident_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_incident, key, value)
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def delete_incident(db: Session, incident_id: int):
    db_incident = get_incident_by_id(db, incident_id)
    db.delete(db_incident)
    db.commit()
    return {"message": f"Incident with ID {incident_id} deleted"}

# API Endpoints
@app.post("/report", response_model=IncidentResponse)
def report_incident_api(incident: IncidentCreate, db: Session = Depends(get_incident_db)):
    return create_incident(db=db, incident=incident)

@app.get("/incidents/", response_model=List[IncidentResponse])
def read_incidents_api(db: Session = Depends(get_incident_db)):
    return get_incidents(db=db)

@app.get("/incidents/{incident_id}", response_model=IncidentResponse)
def read_incident_api(incident_id: int, db: Session = Depends(get_incident_db)):
    return get_incident_by_id(db=db, incident_id=incident_id)

@app.put("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident_api(incident_id: int, incident_update: IncidentUpdate, db: Session = Depends(get_incident_db)):
    return update_incident(db=db, incident_id=incident_id, incident_update=incident_update)

@app.delete("/incidents/{incident_id}")
def delete_incident_api(incident_id: int, db: Session = Depends(get_incident_db)):
    return delete_incident(db=db, incident_id=incident_id)