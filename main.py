"""
FastAPI application for Event Reporting System
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

from database import get_db, init_db
from models import *
from services import EventService, StudentService, ReportService

# Initialize FastAPI app
app = FastAPI(
    title="Event Reporting System",
    description="Comprehensive event management and reporting platform for campus events",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Root endpoint to serve the main page
@app.get("/")
async def read_root():
    from fastapi.responses import FileResponse
    return FileResponse('static/index.html')

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# College endpoints
@app.get("/colleges", response_model=List[College])
async def get_colleges(db: Session = Depends(get_db)):
    """Get all colleges"""
    return db.query(College).all()

@app.post("/colleges", response_model=College)
async def create_college(college: CollegeCreate, db: Session = Depends(get_db)):
    """Create a new college"""
    # Check if college code already exists
    existing = db.query(College).filter(College.code == college.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="College code already exists"
        )
    
    db_college = College(**college.dict())
    db.add(db_college)
    db.commit()
    db.refresh(db_college)
    return db_college

# Student endpoints
@app.get("/students", response_model=List[Student])
async def get_students(
    college_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get students with optional college filter"""
    query = db.query(Student)
    if college_id:
        query = query.filter(Student.college_id == college_id)
    
    return query.offset(skip).limit(limit).all()

@app.post("/students", response_model=Student)
async def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student"""
    # Check if student ID already exists in the college
    existing = db.query(Student).filter(
        Student.student_id == student.student_id,
        Student.college_id == student.college_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID already exists in this college"
        )
    
    # Check if email already exists
    existing_email = db.query(Student).filter(Student.email == student.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# Event endpoints
@app.get("/events", response_model=List[Event])
async def get_events(
    college_id: Optional[int] = None,
    event_type: Optional[EventType] = None,
    upcoming_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get events with optional filters"""
    query = db.query(Event)
    
    if college_id:
        query = query.filter(Event.college_id == college_id)
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if upcoming_only:
        query = query.filter(Event.start_date > datetime.utcnow())
    
    query = query.filter(Event.is_cancelled == False)
    
    return query.offset(skip).limit(limit).all()

@app.post("/events", response_model=Event)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    # Check if event code already exists in the college
    existing = db.query(Event).filter(
        Event.event_code == event.event_code,
        Event.college_id == event.college_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event code already exists in this college"
        )
    
    # Validate dates
    if event.start_date >= event.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.put("/events/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db)
):
    """Update an event"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

# Registration endpoints
@app.post("/registrations", response_model=EventRegistration)
async def register_for_event(
    registration: EventRegistrationCreate,
    db: Session = Depends(get_db)
):
    """Register a student for an event"""
    return await EventService.register_student(db, registration)

@app.delete("/registrations/{registration_id}")
async def cancel_registration(
    registration_id: int,
    db: Session = Depends(get_db)
):
    """Cancel a registration"""
    return await EventService.cancel_registration(db, registration_id)

@app.get("/registrations/event/{event_id}", response_model=List[EventRegistration])
async def get_event_registrations(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get all registrations for an event"""
    return db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id
    ).all()

@app.get("/registrations/student/{student_id}", response_model=List[EventRegistration])
async def get_student_registrations(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get all registrations for a student"""
    return db.query(EventRegistration).filter(
        EventRegistration.student_id == student_id
    ).all()

# Attendance endpoints
@app.post("/attendance", response_model=Attendance)
async def mark_attendance(
    attendance: AttendanceCreate,
    db: Session = Depends(get_db)
):
    """Mark student attendance for an event"""
    return await EventService.mark_attendance(db, attendance)

@app.get("/attendance/event/{event_id}", response_model=List[Attendance])
async def get_event_attendance(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get attendance records for an event"""
    return db.query(Attendance).filter(Attendance.event_id == event_id).all()

@app.get("/attendance/student/{student_id}", response_model=List[Attendance])
async def get_student_attendance(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get attendance records for a student"""
    return db.query(Attendance).filter(Attendance.student_id == student_id).all()

# Feedback endpoints
@app.post("/feedback", response_model=EventFeedback)
async def submit_feedback(
    feedback: EventFeedbackCreate,
    db: Session = Depends(get_db)
):
    """Submit feedback for an event"""
    return await EventService.submit_feedback(db, feedback)

@app.get("/feedback/event/{event_id}", response_model=List[EventFeedback])
async def get_event_feedback(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get all feedback for an event"""
    return db.query(EventFeedback).filter(EventFeedback.event_id == event_id).all()

@app.get("/feedback/student/{student_id}", response_model=List[EventFeedback])
async def get_student_feedback(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get all feedback submitted by a student"""
    return db.query(EventFeedback).filter(EventFeedback.student_id == student_id).all()

# Reporting endpoints
@app.get("/reports/event-stats/{event_id}", response_model=EventStats)
async def get_event_stats(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for an event"""
    return await ReportService.get_event_stats(db, event_id)

@app.get("/reports/student-stats/{student_id}", response_model=StudentStats)
async def get_student_stats(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for a student"""
    return await ReportService.get_student_stats(db, student_id)

@app.get("/reports/college-stats/{college_id}", response_model=CollegeStats)
async def get_college_stats(
    college_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for a college"""
    return await ReportService.get_college_stats(db, college_id)

@app.get("/reports/event-participation", response_model=List[EventParticipationReport])
async def get_event_participation_report(
    college_id: Optional[int] = None,
    event_type: Optional[EventType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive event participation report"""
    return await ReportService.get_event_participation_report(
        db, college_id, event_type, start_date, end_date
    )

@app.get("/reports/top-students", response_model=List[TopStudentsReport])
async def get_top_students_report(
    college_id: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get top most active students"""
    return await ReportService.get_top_students_report(db, college_id, limit)

@app.get("/reports/event-popularity", response_model=List[EventStats])
async def get_event_popularity_report(
    college_id: Optional[int] = None,
    event_type: Optional[EventType] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get event popularity ranking"""
    return await ReportService.get_event_popularity_report(
        db, college_id, event_type, limit
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
