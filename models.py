"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    CONFERENCE = "Conference"
    COMPETITION = "Competition"
    SYMPOSIUM = "Symposium"
    SOCIAL = "Social"
    SPORTS = "Sports"
    OTHER = "Other"

class RegistrationStatus(str, Enum):
    REGISTERED = "registered"
    CANCELLED = "cancelled"
    WAITLISTED = "waitlisted"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"

# College Models
class CollegeBase(BaseModel):
    name: str
    code: str
    location: Optional[str] = None

class CollegeCreate(CollegeBase):
    pass

class College(CollegeBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Student Models
class StudentBase(BaseModel):
    student_id: str
    email: EmailStr
    first_name: str
    last_name: str
    college_id: int

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Event Models
class EventBase(BaseModel):
    event_code: str
    title: str
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    college_id: int
    start_date: datetime
    end_date: datetime
    location: Optional[str] = None
    max_capacity: Optional[int] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    max_capacity: Optional[int] = None
    is_cancelled: Optional[bool] = None

class Event(EventBase):
    id: int
    is_cancelled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Registration Models
class EventRegistrationBase(BaseModel):
    student_id: int
    event_id: int
    status: RegistrationStatus = RegistrationStatus.REGISTERED

class EventRegistrationCreate(EventRegistrationBase):
    pass

class EventRegistration(EventRegistrationBase):
    id: int
    registration_date: datetime
    
    class Config:
        from_attributes = True

# Attendance Models
class AttendanceBase(BaseModel):
    student_id: int
    event_id: int
    attendance_status: AttendanceStatus = AttendanceStatus.PRESENT
    check_out_time: Optional[datetime] = None

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    check_in_time: datetime
    
    class Config:
        from_attributes = True

# Feedback Models
class EventFeedbackBase(BaseModel):
    student_id: int
    event_id: int
    rating: int
    feedback_text: Optional[str] = None

class EventFeedbackCreate(EventFeedbackBase):
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class EventFeedback(EventFeedbackBase):
    id: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True

# Reporting Models
class EventStats(BaseModel):
    event_id: int
    event_title: str
    total_registrations: int
    total_attendance: int
    attendance_percentage: float
    average_rating: Optional[float] = None
    total_feedback: int

class StudentStats(BaseModel):
    student_id: int
    student_name: str
    college_name: str
    total_registrations: int
    total_attendance: int
    attendance_rate: float
    average_rating_given: Optional[float] = None

class CollegeStats(BaseModel):
    college_id: int
    college_name: str
    total_students: int
    total_events: int
    total_registrations: int
    average_attendance_rate: float
    average_event_rating: Optional[float] = None

class EventParticipationReport(BaseModel):
    event_id: int
    event_title: str
    event_type: str
    college_name: str
    start_date: datetime
    total_registrations: int
    attendance_count: int
    attendance_percentage: float
    average_rating: Optional[float] = None
    feedback_count: int
    capacity_utilization: Optional[float] = None

class TopStudentsReport(BaseModel):
    student_id: int
    student_name: str
    college_name: str
    participation_score: float
    total_events_attended: int
    average_rating_given: Optional[float] = None

# Response Models
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int

