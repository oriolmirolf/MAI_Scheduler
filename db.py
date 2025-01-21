# db.py
import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# If we have a secrets-based URL, use that. Otherwise fallback to local dev.
DATABASE_URL = st.secrets.get("DATABASE_URL", "sqlite:///myapp.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    schedules = relationship("SavedSchedule", back_populates="owner")

class SavedSchedule(Base):
    __tablename__ = "saved_schedules"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_json = Column(Text, nullable=False)

    owner = relationship("User", back_populates="schedules")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
