from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# --- User Schemas ---
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str # 'student', 'organizer', 'admin'
    branch: Optional[str] = None
    year: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

# --- Event Schemas ---
class EventCreate(BaseModel):
    title: str
    description: str
    date: datetime
    venue: str
    capacity: int
    category_id: int

class EventResponse(BaseModel):
    id: int
    title: str
    date: datetime
    venue: str
    capacity: int
    
    class Config:
        orm_mode = True

# --- Registration Schemas ---
class RegistrationCreate(BaseModel):
    event_id: int
    user_id: int 

class RegistrationResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: str
    registration_date: datetime

    class Config:
        orm_mode = True

# --- Attendance Schemas ---
class AttendanceScan(BaseModel):
    registration_id: int
    event_id: int

class AttendanceResponse(BaseModel):
    message: str
    registration_id: int
    scanned_at: datetime

# --- Feedback Schemas ---
class FeedbackCreate(BaseModel):
    user_id: int
    event_id: int
    rating: int  # Ensure this is validated 1-5 in the frontend
    comments: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    rating: int
    comments: Optional[str]

    class Config:
        orm_mode = True

# --- Analytics Dashboard Schemas ---
class EventAnalytics(BaseModel):
    event_id: int
    event_title: str
    capacity: int
    total_registered: int
    total_attended: int
    average_rating: float

class DashboardResponse(BaseModel):
    total_students: int
    total_events: int
    event_stats: list[EventAnalytics]

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str

class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True