# models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # 'student', 'organizer', 'admin'
    branch = Column(String) # For AI recommendations
    year = Column(Integer)  # For AI recommendations
    
    registrations = relationship("Registration", back_populates="student")
    feedbacks = relationship("Feedback", back_populates="student")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True) # e.g., 'Workshop', 'Fest', 'Seminar'
    
    events = relationship("Event", back_populates="category")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    date = Column(DateTime)
    venue = Column(String)
    capacity = Column(Integer)
    organizer_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    category = relationship("Category", back_populates="events")
    registrations = relationship("Registration", back_populates="event")
    feedbacks = relationship("Feedback", back_populates="event")

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    status = Column(String, default="confirmed") # 'confirmed' or 'waitlisted'
    registration_date = Column(DateTime, default=datetime.utcnow)
    
    student = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
    attendance = relationship("Attendance", back_populates="registration", uselist=False)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(Integer, ForeignKey("registrations.id"))
    qr_data_scanned = Column(String) # To verify the specific QR code
    scanned_at = Column(DateTime, default=datetime.utcnow)
    
    registration = relationship("Registration", back_populates="attendance")

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    rating = Column(Integer) # 1 to 5
    comments = Column(Text)
    
    student = relationship("User", back_populates="feedbacks")
    event = relationship("Event", back_populates="feedbacks")