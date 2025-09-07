"""
Service layer for business logic and data processing
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from models import *
from database import Event, Student, College, EventRegistration, Attendance, EventFeedback

class EventService:
    """Service for event-related operations"""
    
    @staticmethod
    async def register_student(db: Session, registration: EventRegistrationCreate):
        """Register a student for an event with validation"""
        # Check if student exists
        student = db.query(Student).filter(Student.id == registration.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check if event exists and is not cancelled
        event = db.query(Event).filter(Event.id == registration.event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        if event.is_cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot register for cancelled event"
            )
        
        # Check if event has already started
        if event.start_date <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot register for event that has already started"
            )
        
        # Check if student is already registered
        existing_registration = db.query(EventRegistration).filter(
            EventRegistration.student_id == registration.student_id,
            EventRegistration.event_id == registration.event_id
        ).first()
        
        if existing_registration:
            if existing_registration.status == "registered":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student is already registered for this event"
                )
            elif existing_registration.status == "cancelled":
                # Allow re-registration if previously cancelled
                existing_registration.status = "registered"
                existing_registration.registration_date = datetime.utcnow()
                db.commit()
                db.refresh(existing_registration)
                return existing_registration
        
        # Check capacity if specified
        if event.max_capacity:
            current_registrations = db.query(EventRegistration).filter(
                EventRegistration.event_id == registration.event_id,
                EventRegistration.status == "registered"
            ).count()
            
            if current_registrations >= event.max_capacity:
                # Add to waitlist
                registration.status = "waitlisted"
        
        db_registration = EventRegistration(**registration.dict())
        db.add(db_registration)
        db.commit()
        db.refresh(db_registration)
        return db_registration
    
    @staticmethod
    async def cancel_registration(db: Session, registration_id: int):
        """Cancel a registration"""
        registration = db.query(EventRegistration).filter(
            EventRegistration.id == registration_id
        ).first()
        
        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found"
            )
        
        if registration.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration is already cancelled"
            )
        
        registration.status = "cancelled"
        db.commit()
        
        # If there are waitlisted students, promote the first one
        event = db.query(Event).filter(Event.id == registration.event_id).first()
        if event and event.max_capacity:
            waitlisted = db.query(EventRegistration).filter(
                EventRegistration.event_id == registration.event_id,
                EventRegistration.status == "waitlisted"
            ).order_by(EventRegistration.registration_date).first()
            
            if waitlisted:
                waitlisted.status = "registered"
                db.commit()
        
        return {"message": "Registration cancelled successfully"}
    
    @staticmethod
    async def mark_attendance(db: Session, attendance: AttendanceCreate):
        """Mark student attendance for an event"""
        # Check if student exists
        student = db.query(Student).filter(Student.id == attendance.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check if event exists
        event = db.query(Event).filter(Event.id == attendance.event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Check if student is registered for the event
        registration = db.query(EventRegistration).filter(
            EventRegistration.student_id == attendance.student_id,
            EventRegistration.event_id == attendance.event_id,
            EventRegistration.status == "registered"
        ).first()
        
        if not registration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is not registered for this event"
            )
        
        # Check if attendance is already marked
        existing_attendance = db.query(Attendance).filter(
            Attendance.student_id == attendance.student_id,
            Attendance.event_id == attendance.event_id
        ).first()
        
        if existing_attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance already marked for this student"
            )
        
        db_attendance = Attendance(**attendance.dict())
        db.add(db_attendance)
        db.commit()
        db.refresh(db_attendance)
        return db_attendance
    
    @staticmethod
    async def submit_feedback(db: Session, feedback: EventFeedbackCreate):
        """Submit feedback for an event"""
        # Check if student exists
        student = db.query(Student).filter(Student.id == feedback.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check if event exists
        event = db.query(Event).filter(Event.id == feedback.event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Check if student attended the event
        attendance = db.query(Attendance).filter(
            Attendance.student_id == feedback.student_id,
            Attendance.event_id == feedback.event_id
        ).first()
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student must attend the event to submit feedback"
            )
        
        # Check if feedback already exists
        existing_feedback = db.query(EventFeedback).filter(
            EventFeedback.student_id == feedback.student_id,
            EventFeedback.event_id == feedback.event_id
        ).first()
        
        if existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback already submitted for this event"
            )
        
        db_feedback = EventFeedback(**feedback.dict())
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback

class StudentService:
    """Service for student-related operations"""
    
    @staticmethod
    async def get_student_participation_summary(db: Session, student_id: int):
        """Get comprehensive participation summary for a student"""
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Get registration count
        total_registrations = db.query(EventRegistration).filter(
            EventRegistration.student_id == student_id,
            EventRegistration.status == "registered"
        ).count()
        
        # Get attendance count
        total_attendance = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.attendance_status == "present"
        ).count()
        
        # Get feedback count and average rating
        feedback_stats = db.query(
            func.count(EventFeedback.id).label('count'),
            func.avg(EventFeedback.rating).label('avg_rating')
        ).filter(EventFeedback.student_id == student_id).first()
        
        return {
            "student_id": student_id,
            "total_registrations": total_registrations,
            "total_attendance": total_attendance,
            "attendance_rate": (total_attendance / total_registrations * 100) if total_registrations > 0 else 0,
            "feedback_count": feedback_stats.count or 0,
            "average_rating_given": float(feedback_stats.avg_rating) if feedback_stats.avg_rating else None
        }

class ReportService:
    """Service for generating reports and analytics"""
    
    @staticmethod
    async def get_event_stats(db: Session, event_id: int):
        """Get comprehensive statistics for an event"""
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Get registration count
        total_registrations = db.query(EventRegistration).filter(
            EventRegistration.event_id == event_id,
            EventRegistration.status == "registered"
        ).count()
        
        # Get attendance count
        total_attendance = db.query(Attendance).filter(
            Attendance.event_id == event_id,
            Attendance.attendance_status == "present"
        ).count()
        
        # Get feedback statistics
        feedback_stats = db.query(
            func.count(EventFeedback.id).label('count'),
            func.avg(EventFeedback.rating).label('avg_rating')
        ).filter(EventFeedback.event_id == event_id).first()
        
        attendance_percentage = (total_attendance / total_registrations * 100) if total_registrations > 0 else 0
        
        return EventStats(
            event_id=event_id,
            event_title=event.title,
            total_registrations=total_registrations,
            total_attendance=total_attendance,
            attendance_percentage=round(attendance_percentage, 2),
            average_rating=float(feedback_stats.avg_rating) if feedback_stats.avg_rating else None,
            total_feedback=feedback_stats.count or 0
        )
    
    @staticmethod
    async def get_student_stats(db: Session, student_id: int):
        """Get comprehensive statistics for a student"""
        student = db.query(Student).join(College).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Get registration count
        total_registrations = db.query(EventRegistration).filter(
            EventRegistration.student_id == student_id,
            EventRegistration.status == "registered"
        ).count()
        
        # Get attendance count
        total_attendance = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.attendance_status == "present"
        ).count()
        
        # Get feedback statistics
        feedback_stats = db.query(
            func.avg(EventFeedback.rating).label('avg_rating')
        ).filter(EventFeedback.student_id == student_id).first()
        
        attendance_rate = (total_attendance / total_registrations * 100) if total_registrations > 0 else 0
        
        return StudentStats(
            student_id=student_id,
            student_name=f"{student.first_name} {student.last_name}",
            college_name=student.college.name,
            total_registrations=total_registrations,
            total_attendance=total_attendance,
            attendance_rate=round(attendance_rate, 2),
            average_rating_given=float(feedback_stats.avg_rating) if feedback_stats.avg_rating else None
        )
    
    @staticmethod
    async def get_college_stats(db: Session, college_id: int):
        """Get comprehensive statistics for a college"""
        college = db.query(College).filter(College.id == college_id).first()
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="College not found"
            )
        
        # Get student count
        total_students = db.query(Student).filter(Student.college_id == college_id).count()
        
        # Get event count
        total_events = db.query(Event).filter(Event.college_id == college_id).count()
        
        # Get total registrations
        total_registrations = db.query(EventRegistration).join(Student).filter(
            Student.college_id == college_id,
            EventRegistration.status == "registered"
        ).count()
        
        # Get average attendance rate
        attendance_stats = db.query(
            func.count(Attendance.id).label('attendance_count')
        ).join(Student).filter(
            Student.college_id == college_id,
            Attendance.attendance_status == "present"
        ).first()
        
        # Get average event rating
        rating_stats = db.query(
            func.avg(EventFeedback.rating).label('avg_rating')
        ).join(Student).filter(Student.college_id == college_id).first()
        
        attendance_rate = (attendance_stats.attendance_count / total_registrations * 100) if total_registrations > 0 else 0
        
        return CollegeStats(
            college_id=college_id,
            college_name=college.name,
            total_students=total_students,
            total_events=total_events,
            total_registrations=total_registrations,
            average_attendance_rate=round(attendance_rate, 2),
            average_event_rating=float(rating_stats.avg_rating) if rating_stats.avg_rating else None
        )
    
    @staticmethod
    async def get_event_participation_report(
        db: Session,
        college_id: Optional[int] = None,
        event_type: Optional[EventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """Get comprehensive event participation report"""
        query = db.query(Event).join(College)
        
        if college_id:
            query = query.filter(Event.college_id == college_id)
        
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        if start_date:
            query = query.filter(Event.start_date >= start_date)
        
        if end_date:
            query = query.filter(Event.start_date <= end_date)
        
        events = query.all()
        report = []
        
        for event in events:
            # Get registration count
            total_registrations = db.query(EventRegistration).filter(
                EventRegistration.event_id == event.id,
                EventRegistration.status == "registered"
            ).count()
            
            # Get attendance count
            attendance_count = db.query(Attendance).filter(
                Attendance.event_id == event.id,
                Attendance.attendance_status == "present"
            ).count()
            
            # Get feedback statistics
            feedback_stats = db.query(
                func.count(EventFeedback.id).label('count'),
                func.avg(EventFeedback.rating).label('avg_rating')
            ).filter(EventFeedback.event_id == event.id).first()
            
            attendance_percentage = (attendance_count / total_registrations * 100) if total_registrations > 0 else 0
            capacity_utilization = (total_registrations / event.max_capacity * 100) if event.max_capacity else None
            
            report.append(EventParticipationReport(
                event_id=event.id,
                event_title=event.title,
                event_type=event.event_type or "Other",
                college_name=event.college.name,
                start_date=event.start_date,
                total_registrations=total_registrations,
                attendance_count=attendance_count,
                attendance_percentage=round(attendance_percentage, 2),
                average_rating=float(feedback_stats.avg_rating) if feedback_stats.avg_rating else None,
                feedback_count=feedback_stats.count or 0,
                capacity_utilization=round(capacity_utilization, 2) if capacity_utilization else None
            ))
        
        return sorted(report, key=lambda x: x.total_registrations, reverse=True)
    
    @staticmethod
    async def get_top_students_report(db: Session, college_id: Optional[int] = None, limit: int = 10):
        """Get top most active students"""
        query = db.query(Student).join(College)
        
        if college_id:
            query = query.filter(Student.college_id == college_id)
        
        students = query.all()
        student_stats = []
        
        for student in students:
            # Get attendance count
            total_attendance = db.query(Attendance).filter(
                Attendance.student_id == student.id,
                Attendance.attendance_status == "present"
            ).count()
            
            # Get feedback statistics
            feedback_stats = db.query(
                func.avg(EventFeedback.rating).label('avg_rating')
            ).filter(EventFeedback.student_id == student.id).first()
            
            # Calculate participation score (attendance + feedback quality)
            participation_score = total_attendance
            if feedback_stats.avg_rating:
                participation_score += float(feedback_stats.avg_rating) * 0.5
            
            student_stats.append(TopStudentsReport(
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                college_name=student.college.name,
                participation_score=round(participation_score, 2),
                total_events_attended=total_attendance,
                average_rating_given=float(feedback_stats.avg_rating) if feedback_stats.avg_rating else None
            ))
        
        return sorted(student_stats, key=lambda x: x.participation_score, reverse=True)[:limit]
    
    @staticmethod
    async def get_event_popularity_report(
        db: Session,
        college_id: Optional[int] = None,
        event_type: Optional[EventType] = None,
        limit: int = 10
    ):
        """Get event popularity ranking"""
        query = db.query(Event)
        
        if college_id:
            query = query.filter(Event.college_id == college_id)
        
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        events = query.all()
        event_stats = []
        
        for event in events:
            # Get registration count
            total_registrations = db.query(EventRegistration).filter(
                EventRegistration.event_id == event.id,
                EventRegistration.status == "registered"
            ).count()
            
            # Get attendance count
            total_attendance = db.query(Attendance).filter(
                Attendance.event_id == event.id,
                Attendance.attendance_status == "present"
            ).count()
            
            # Get feedback statistics
            feedback_stats = db.query(
                func.count(EventFeedback.id).label('count'),
                func.avg(EventFeedback.rating).label('avg_rating')
            ).filter(EventFeedback.event_id == event.id).first()
            
            attendance_percentage = (total_attendance / total_registrations * 100) if total_registrations > 0 else 0
            
            event_stats.append(EventStats(
                event_id=event.id,
                event_title=event.title,
                total_registrations=total_registrations,
                total_attendance=total_attendance,
                attendance_percentage=round(attendance_percentage, 2),
                average_rating=float(feedback_stats.avg_rating) if feedback_stats.avg_rating else None,
                total_feedback=feedback_stats.count or 0
            ))
        
        return sorted(event_stats, key=lambda x: x.total_registrations, reverse=True)[:limit]

