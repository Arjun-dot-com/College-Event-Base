from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import qrcode
import base64
from io import BytesIO
import json
from typing import List
from ml_engine import get_personalized_events
import models
import schemas
from database import engine, SessionLocal
from sqlalchemy import func
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_super_secret_key"
ALGORITHM = "HS256"

# --- Dependencies & Utilities ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def send_confirmation_email(email: str, event_title: str, status: str, qr_code_str: str = None):
    # Mock function for background task
    print(f"Sending {status} email to {email} for event '{event_title}'")
    if qr_code_str:
        print("QR Code attached to email.")

def generate_qr_code_base64(registration_id: int, event_id: int) -> str:
    qr_data = json.dumps({"registration_id": registration_id, "event_id": event_id})
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# --- API Endpoints ---

@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        name=user.name, 
        email=user.email, 
        password_hash=hashed_password, 
        role=user.role,
        branch=user.branch,
        year=user.year
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.delete("/events/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    # 1. Find the event
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # 2. Clean up associated data to prevent database errors
    # Delete related feedback
    db.query(models.Feedback).filter(models.Feedback.event_id == event_id).delete()
    
    # Delete related attendance records by finding all registrations for this event
    registrations = db.query(models.Registration).filter(models.Registration.event_id == event_id).all()
    reg_ids = [reg.id for reg in registrations]
    if reg_ids:
        db.query(models.Attendance).filter(models.Attendance.registration_id.in_(reg_ids)).delete(synchronize_session=False)
        
    # Delete the registrations themselves
    db.query(models.Registration).filter(models.Registration.event_id == event_id).delete()

    # 3. Finally, delete the event
    db.delete(event)
    db.commit()
    
    return {"message": f"Event '{event.title}' successfully deleted."}

# --- NEW AUTHENTICATION ROUTE ---
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login/", response_model=schemas.TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(models.User).filter(models.User.email == req.email).first()
    
    # Verify user exists and password is correct
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate JWT Token
    expire = datetime.utcnow() + timedelta(minutes=60) # Token lasts 1 hour
    to_encode = {"sub": str(user.id), "role": user.role, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": encoded_jwt, 
        "token_type": "bearer", 
        "user_id": user.id, 
        "role": user.role
    }

# --- NEW CATEGORY ROUTES ---
@app.post("/categories/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    new_cat = models.Category(name=category.name)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@app.get("/categories/", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@app.get("/events/", response_model=List[schemas.EventResponse], status_code=status.HTTP_200_OK)
def get_all_events(db: Session = Depends(get_db)):
    """
    Returns all events for the dashboard.
    """
    return db.query(models.Event).all()

@app.post("/events/", response_model=schemas.EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: schemas.EventCreate, organizer_id: int, db: Session = Depends(get_db)):
    new_event = models.Event(**event.dict(), organizer_id=organizer_id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@app.post("/register/", response_model=schemas.RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_for_event(
    reg: schemas.RegistrationCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    event = db.query(models.Event).filter(models.Event.id == reg.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user = db.query(models.User).filter(models.User.id == reg.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_reg = db.query(models.Registration).filter(
        models.Registration.user_id == reg.user_id,
        models.Registration.event_id == reg.event_id
    ).first()
    
    if existing_reg:
        raise HTTPException(status_code=400, detail="User is already registered for this event")

    confirmed_count = db.query(models.Registration).filter(
        models.Registration.event_id == reg.event_id,
        models.Registration.status == "confirmed"
    ).count()

    registration_status = "confirmed" if confirmed_count < event.capacity else "waitlisted"

    new_registration = models.Registration(
        user_id=reg.user_id,
        event_id=reg.event_id,
        status=registration_status
    )
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)

    # Generate QR Code only if confirmed
    qr_code_str = None
    if registration_status == "confirmed":
        qr_code_str = generate_qr_code_base64(new_registration.id, event.id)

    background_tasks.add_task(
        send_confirmation_email, 
        user.email, 
        event.title, 
        registration_status, 
        qr_code_str
    )

    return new_registration

@app.post("/attendance/scan/", response_model=schemas.AttendanceResponse, status_code=status.HTTP_200_OK)
def mark_attendance(scan_data: schemas.AttendanceScan, db: Session = Depends(get_db)):
    registration = db.query(models.Registration).filter(
        models.Registration.id == scan_data.registration_id,
        models.Registration.event_id == scan_data.event_id
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Invalid QR Code: Registration not found.")

    if registration.status != "confirmed":
        raise HTTPException(status_code=403, detail="Student is waitlisted and cannot be marked present.")

    existing_attendance = db.query(models.Attendance).filter(
        models.Attendance.registration_id == scan_data.registration_id
    ).first()

    if existing_attendance:
        raise HTTPException(status_code=400, detail="Attendance already marked for this student.")

    new_attendance = models.Attendance(
        registration_id=scan_data.registration_id,
        qr_data_scanned=f"Scanned for Reg ID: {scan_data.registration_id}" 
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)

    return schemas.AttendanceResponse(
        message="Attendance successfully recorded!",
        registration_id=new_attendance.registration_id,
        scanned_at=new_attendance.scanned_at
    )

@app.get("/recommendations/{user_id}", response_model=List[schemas.EventResponse], status_code=status.HTTP_200_OK)
def recommend_events(user_id: int, db: Session = Depends(get_db)):
    """
    Returns top 3 recommended events based on user branch, year, and registration history.
    """
    recommended_events = get_personalized_events(user_id, db)
    
    if not recommended_events:
        raise HTTPException(status_code=404, detail="Not enough data to generate recommendations.")
        
    return recommended_events

@app.post("/feedback/", response_model=schemas.FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    # 1. Verify user actually attended the event before allowing feedback
    registration = db.query(models.Registration).filter(
        models.Registration.user_id == feedback.user_id,
        models.Registration.event_id == feedback.event_id
    ).first()

    if not registration:
        raise HTTPException(status_code=403, detail="Must be registered to leave feedback.")
        
    attendance = db.query(models.Attendance).filter(
        models.Attendance.registration_id == registration.id
    ).first()

    if not attendance:
        raise HTTPException(status_code=403, detail="Must have attended the event to leave feedback.")

    # 2. Save the feedback
    new_feedback = models.Feedback(**feedback.dict())
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    
    return new_feedback

@app.get("/admin/dashboard/", response_model=schemas.DashboardResponse, status_code=status.HTTP_200_OK)
def get_admin_dashboard(db: Session = Depends(get_db)):
    # 1. Get high-level metrics
    total_students = db.query(models.User).filter(models.User.role == "student").count()
    total_events = db.query(models.Event).count()
    
    # 2. Calculate granular stats per event
    events = db.query(models.Event).all()
    event_stats = []
    
    for event in events:
        # Registrations count
        reg_count = db.query(models.Registration).filter(
            models.Registration.event_id == event.id,
            models.Registration.status == "confirmed"
        ).count()
        
        # Attendance count
        # We join Registration and Attendance to count how many scanned in for this specific event
        attended_count = db.query(models.Attendance).join(models.Registration).filter(
            models.Registration.event_id == event.id
        ).count()
        
        # Average Rating
        avg_rating = db.query(func.avg(models.Feedback.rating)).filter(
            models.Feedback.event_id == event.id
        ).scalar()
        
        event_stats.append(
            schemas.EventAnalytics(
                event_id=event.id,
                event_title=event.title,
                capacity=event.capacity,
                total_registered=reg_count,
                total_attended=attended_count,
                average_rating=float(avg_rating) if avg_rating else 0.0
            )
        )
        
    return schemas.DashboardResponse(
        total_students=total_students,
        total_events=total_events,
        event_stats=event_stats
    )