from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True  # Changed from orm_mode in Pydantic V2

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TrafficZoneBase(BaseModel):
    name: str
    vehicle_count: int

class TrafficZoneCreate(TrafficZoneBase):
    pass

class TrafficZoneUpdate(BaseModel):
    name: Optional[str] = None
    vehicle_count: Optional[int] = None

class TrafficZone(TrafficZoneBase):
    id: int
    class Config:
        from_attributes = True  # Changed from orm_mode in Pydantic V2