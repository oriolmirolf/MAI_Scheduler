# auth.py
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db import User, SavedSchedule
import json

# Configure Passlib for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Securely hash the password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain-text password vs hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def register_user(db: Session, username: str, password: str):
    """Register a new user. Returns (success, message)."""
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return False, "Username already taken."
    
    new_user = User(
        username=username,
        hashed_password=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    return True, "User registered successfully!"

def authenticate_user(db: Session, username: str, password: str):
    """Check if username & password are valid. Returns (success, user_or_msg)."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False, "User does not exist."
    if not verify_password(password, user.hashed_password):
        return False, "Incorrect password."
    return True, user

def save_schedule_for_user(db: Session, user_id: int, schedule_data: dict):
    """
    Save a schedule to the database for a user.
    `schedule_data` can be any JSON-serializable structure 
    (list of course codes, metrics, etc.).
    """
    schedule_json = json.dumps(schedule_data)
    saved = SavedSchedule(user_id=user_id, schedule_json=schedule_json)
    db.add(saved)
    db.commit()
    return True, "Schedule saved successfully!"

def get_user_schedules(db: Session, user_id: int):
    """Retrieve all schedules for the given user as Python objects."""
    entries = db.query(SavedSchedule).filter_by(user_id=user_id).all()
    results = []
    for e in entries:
        results.append(json.loads(e.schedule_json))
    return results
