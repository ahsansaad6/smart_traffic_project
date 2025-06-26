from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Annotated
import os
from jose import JWTError, jwt

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Security settings
SECRET_KEY = os.environ.get("SECRET_KEY", "YOUR_SECRET_KEY") # Use a strong, environment-based secret in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.UserBase(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[models.User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# --- User-related database functions ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Authentication Endpoints ---
@app.post("/auth/signup", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    return current_user

@app.get("/users/", response_model=list[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# --- Existing Traffic Zone Endpoints (Now Protected) ---
@app.post("/zones/", response_model=schemas.TrafficZone)
def create_zone_api(zone: schemas.TrafficZoneCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    return create_zone(db=db, zone=zone)

@app.get("/zones/", response_model=list[schemas.TrafficZone])
def read_zones_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    zones = get_zones(db, skip=skip, limit=limit)
    return zones

@app.get("/zones/{zone_id}", response_model=schemas.TrafficZone)
def read_zone_api(zone_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_zone = get_zone(db, zone_id=zone_id)
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Traffic Zone not found")
    return db_zone

@app.put("/zones/{zone_id}", response_model=schemas.TrafficZone)
def update_zone_api(zone_id: int, zone: schemas.TrafficZoneUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_zone = update_zone(db=db, zone_id=zone_id, zone=zone)
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Traffic Zone not found")
    return db_zone

@app.delete("/zones/{zone_id}")
def delete_zone_api(zone_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_zone = delete_zone(db=db, zone_id=zone_id)
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Traffic Zone not found")
    return {"message": f"Traffic Zone with id {zone_id} deleted"}

# --- Existing Traffic Zone Database Functions ---
def create_zone(db: Session, zone: schemas.TrafficZoneCreate):
    db_zone = models.TrafficZone(**zone.dict())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

def get_zones(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TrafficZone).offset(skip).limit(limit).all()

def get_zone(db: Session, zone_id: int):
    return db.query(models.TrafficZone).filter(models.TrafficZone.id == zone_id).first()

def update_zone(db: Session, zone_id: int, zone: schemas.TrafficZoneUpdate):
    db_zone = db.query(models.TrafficZone).filter(models.TrafficZone.id == zone_id).first()
    if db_zone:
        for key, value in zone.dict(exclude_unset=True).items():
            setattr(db_zone, key, value)
        db.commit()
        db.refresh(db_zone)
    return db_zone

def delete_zone(db: Session, zone_id: int):
    db_zone = db.query(models.TrafficZone).filter(models.TrafficZone.id == zone_id).first()
    if db_zone:
        db.delete(db_zone)
        db.commit()
    return db_zone is not None