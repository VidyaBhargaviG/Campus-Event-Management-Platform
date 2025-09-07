"""
Database configuration and models for the Event Reporting System
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL - using SQLite for prototype, easily switchable to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./event_management.db")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class College(Base):
    """College/Institution model"""
    __tablename__ = "colleges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)  # e.g., "MIT", "STAN"
    location = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    students = relationship("Student", back_populates="college")
    events = relationship("Event", back_populates="college")

class Student(Base):
    """Student model"""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), nullable=False)  # College-specific student ID
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    college = relationship("College", back_populates="students")
    registrations = relationship("EventRegistration", back_populates="student")
    attendance = relationship("Attendance", back_populates="student")
    feedback = relationship("EventFeedback", back_populates="student")
    
    # Unique constraint for student_id within college
    __table_args__ = (UniqueConstraint('student_id', 'college_id', name='unique_student_per_college'),)

class Event(Base):
    """Event model"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_code = Column(String(50), nullable=False)  # College-specific event code
    title = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(String(100))  # e.g., "Workshop", "Seminar", "Conference"
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(255))
    max_capacity = Column(Integer)
    is_cancelled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    college = relationship("College", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event")
    attendance = relationship("Attendance", back_populates="event")
    feedback = relationship("EventFeedback", back_populates="event")
    
    # Unique constraint for event_code within college
    __table_args__ = (UniqueConstraint('event_code', 'college_id', name='unique_event_per_college'),)

class EventRegistration(Base):
    """Event registration model"""
    __tablename__ = "event_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="registered")  # registered, cancelled, waitlisted
    
    # Relationships
    student = relationship("Student", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
    
    # Unique constraint to prevent duplicate registrations
    __table_args__ = (UniqueConstraint('student_id', 'event_id', name='unique_registration'),)

class Attendance(Base):
    """Attendance tracking model"""
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    check_in_time = Column(DateTime, default=datetime.utcnow)
    check_out_time = Column(DateTime)
    attendance_status = Column(String(20), default="present")  # present, absent, late
    
    # Relationships
    student = relationship("Student", back_populates="attendance")
    event = relationship("Event", back_populates="attendance")
    
    # Unique constraint to prevent duplicate attendance records
    __table_args__ = (UniqueConstraint('student_id', 'event_id', name='unique_attendance'),)

class EventFeedback(Base):
    """Event feedback model"""
    __tablename__ = "event_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback_text = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="feedback")
    event = relationship("Event", back_populates="feedback")
    
    # Unique constraint to prevent duplicate feedback
    __table_args__ = (UniqueConstraint('student_id', 'event_id', name='unique_feedback'),)

# Database utility functions
def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def init_db():
    """Initialize database with sample data"""
    create_tables()
    
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(College).first():
            return
        
        # Create sample colleges
        colleges = [
            College(name="Massachusetts Institute of Technology", code="MIT", location="Cambridge, MA"),
            College(name="Stanford University", code="STAN", location="Stanford, CA"),
            College(name="University of California Berkeley", code="UCB", location="Berkeley, CA"),
            College(name="Carnegie Mellon University", code="CMU", location="Pittsburgh, PA"),
            College(name="Georgia Institute of Technology", code="GT", location="Atlanta, GA"),
        ]
        
        for college in colleges:
            db.add(college)
        
        db.commit()
        
        # Create sample students
        students = [
            # MIT students
            Student(student_id="MIT001", email="john.doe@mit.edu", first_name="John", last_name="Doe", college_id=1),
            Student(student_id="MIT002", email="jane.smith@mit.edu", first_name="Jane", last_name="Smith", college_id=1),
            Student(student_id="MIT003", email="bob.johnson@mit.edu", first_name="Bob", last_name="Johnson", college_id=1),
            Student(student_id="MIT004", email="sarah.wilson@mit.edu", first_name="Sarah", last_name="Wilson", college_id=1),
            Student(student_id="MIT005", email="mike.brown@mit.edu", first_name="Mike", last_name="Brown", college_id=1),
            
            # Stanford students
            Student(student_id="STAN001", email="alice.brown@stanford.edu", first_name="Alice", last_name="Brown", college_id=2),
            Student(student_id="STAN002", email="charlie.wilson@stanford.edu", first_name="Charlie", last_name="Wilson", college_id=2),
            Student(student_id="STAN003", email="david.garcia@stanford.edu", first_name="David", last_name="Garcia", college_id=2),
            Student(student_id="STAN004", email="emma.davis@stanford.edu", first_name="Emma", last_name="Davis", college_id=2),
            
            # UC Berkeley students
            Student(student_id="UCB001", email="diana.davis@berkeley.edu", first_name="Diana", last_name="Davis", college_id=3),
            Student(student_id="UCB002", email="eve.miller@berkeley.edu", first_name="Eve", last_name="Miller", college_id=3),
            Student(student_id="UCB003", email="frank.moore@berkeley.edu", first_name="Frank", last_name="Moore", college_id=3),
            Student(student_id="UCB004", email="grace.taylor@berkeley.edu", first_name="Grace", last_name="Taylor", college_id=3),
            
            # CMU students
            Student(student_id="CMU001", email="henry.anderson@cmu.edu", first_name="Henry", last_name="Anderson", college_id=4),
            Student(student_id="CMU002", email="iris.thomas@cmu.edu", first_name="Iris", last_name="Thomas", college_id=4),
            
            # Georgia Tech students
            Student(student_id="GT001", email="jack.jackson@gatech.edu", first_name="Jack", last_name="Jackson", college_id=5),
            Student(student_id="GT002", email="kate.white@gatech.edu", first_name="Kate", last_name="White", college_id=5),
        ]
        
        for student in students:
            db.add(student)
        
        db.commit()
        
        # Create sample events
        from datetime import datetime, timedelta
        events = [
            # MIT Events
            Event(
                event_code="MIT-TECH-001",
                title="AI and Machine Learning Workshop",
                description="Hands-on workshop covering fundamentals of AI and ML with practical coding sessions",
                event_type="Workshop",
                college_id=1,
                start_date=datetime.utcnow() + timedelta(days=7),
                end_date=datetime.utcnow() + timedelta(days=7, hours=4),
                location="MIT Building 32",
                max_capacity=50
            ),
            Event(
                event_code="MIT-ROBOTICS-001",
                title="Robotics Innovation Challenge",
                description="Build and program autonomous robots for various challenges",
                event_type="Competition",
                college_id=1,
                start_date=datetime.utcnow() + timedelta(days=15),
                end_date=datetime.utcnow() + timedelta(days=15, hours=8),
                location="MIT Robotics Lab",
                max_capacity=30
            ),
            
            # Stanford Events
            Event(
                event_code="STAN-ENTREP-001",
                title="Startup Pitch Competition",
                description="Annual startup pitch competition for student entrepreneurs",
                event_type="Competition",
                college_id=2,
                start_date=datetime.utcnow() + timedelta(days=14),
                end_date=datetime.utcnow() + timedelta(days=14, hours=6),
                location="Stanford Graduate School of Business",
                max_capacity=100
            ),
            Event(
                event_code="STAN-DATA-001",
                title="Data Science Symposium",
                description="Exploring the latest trends in data science and analytics",
                event_type="Symposium",
                college_id=2,
                start_date=datetime.utcnow() + timedelta(days=25),
                end_date=datetime.utcnow() + timedelta(days=25, hours=6),
                location="Stanford Computer Science Building",
                max_capacity=80
            ),
            
            # UC Berkeley Events
            Event(
                event_code="UCB-RESEARCH-001",
                title="Research Symposium",
                description="Graduate student research presentations across multiple disciplines",
                event_type="Symposium",
                college_id=3,
                start_date=datetime.utcnow() + timedelta(days=21),
                end_date=datetime.utcnow() + timedelta(days=21, hours=8),
                location="UC Berkeley Campus",
                max_capacity=200
            ),
            Event(
                event_code="UCB-CYBER-001",
                title="Cybersecurity Workshop",
                description="Learn about cybersecurity best practices and ethical hacking",
                event_type="Workshop",
                college_id=3,
                start_date=datetime.utcnow() + timedelta(days=30),
                end_date=datetime.utcnow() + timedelta(days=30, hours=5),
                location="UC Berkeley EECS Building",
                max_capacity=60
            ),
            
            # CMU Events
            Event(
                event_code="CMU-SOFTWARE-001",
                title="Software Engineering Best Practices",
                description="Industry experts share insights on modern software development",
                event_type="Seminar",
                college_id=4,
                start_date=datetime.utcnow() + timedelta(days=10),
                end_date=datetime.utcnow() + timedelta(days=10, hours=3),
                location="CMU Gates Hillman Center",
                max_capacity=120
            ),
            
            # Georgia Tech Events
            Event(
                event_code="GT-GAME-001",
                title="Game Development Workshop",
                description="Create your own video game using modern development tools",
                event_type="Workshop",
                college_id=5,
                start_date=datetime.utcnow() + timedelta(days=18),
                end_date=datetime.utcnow() + timedelta(days=18, hours=6),
                location="Georgia Tech College of Computing",
                max_capacity=40
            ),
        ]
        
        for event in events:
            db.add(event)
        
        db.commit()
        
        # Create sample registrations, attendance, and feedback
        create_sample_activity_data(db, students, events)
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def create_sample_activity_data(db, students, events):
    """Create sample registrations, attendance, and feedback data"""
    import random
    from datetime import datetime, timedelta
    
    # Sample registrations for events
    registrations = []
    for event in events[:6]:  # Only for first 6 events
        # Randomly select 60-80% of students from the same college
        college_students = [s for s in students if s.college_id == event.college_id]
        num_registrations = random.randint(
            max(1, len(college_students) // 2), 
            min(len(college_students), event.max_capacity or len(college_students))
        )
        
        selected_students = random.sample(college_students, num_registrations)
        
        for student in selected_students:
            registration = EventRegistration(
                student_id=student.id,
                event_id=event.id,
                registration_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                status="registered"
            )
            registrations.append(registration)
            db.add(registration)
    
    db.commit()
    
    # Sample attendance (80-95% of registrations)
    attendance_records = []
    for registration in registrations:
        if random.random() < 0.85:  # 85% attendance rate
            attendance = Attendance(
                student_id=registration.student_id,
                event_id=registration.event_id,
                check_in_time=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                attendance_status="present" if random.random() > 0.1 else "late"
            )
            attendance_records.append(attendance)
            db.add(attendance)
    
    db.commit()
    
    # Sample feedback (70-90% of attendance)
    feedback_records = []
    for attendance in attendance_records:
        if random.random() < 0.8:  # 80% feedback rate
            feedback = EventFeedback(
                student_id=attendance.student_id,
                event_id=attendance.event_id,
                rating=random.randint(3, 5),  # Mostly positive ratings
                feedback_text=random.choice([
                    "Great event! Very informative and well-organized.",
                    "Excellent speakers and engaging content.",
                    "Learned a lot from this workshop.",
                    "Well-structured event with practical examples.",
                    "Good networking opportunities.",
                    "Could use more hands-on activities.",
                    "Very professional and educational.",
                    "Amazing experience, would recommend!",
                    "Good content but room was too crowded.",
                    "Inspiring and thought-provoking presentations."
                ]),
                submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
            )
            feedback_records.append(feedback)
            db.add(feedback)
    
    db.commit()

if __name__ == "__main__":
    init_db()
