"""
Database Models for Litigation Tracker
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

DATABASE_URL = "sqlite:///./litigation_tracker.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class Forum(str, enum.Enum):
    CAT = "CAT"
    HC = "HC"
    SC = "SC"
    OTHER = "Other Tribunals"


class CaseStatus(str, enum.Enum):
    FILED = "Filed"
    ADMISSION = "Admission"
    HEARING = "Hearing"
    DISMISSED = "Dismissed"
    ADJOURNED = "Adjourned"
    RESERVED = "Reserved"
    ALLOWED = "Allowed"


class AffidavitStatus(str, enum.Enum):
    FILED = "Filed"
    PWC_SUBMITTED_SC = "PWC Submitted to SC"
    PWC_PENDING = "PWC Pending"
    AFFIDAVIT_SUBMITTED_SC = "Affidavit Submitted to SC"
    DRAFT_RECEIVED = "Draft Affidavit Received"
    SENT_VETTING = "Sent for Vetting"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default=UserRole.USER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(20), unique=True, index=True, nullable=False)  # YYYY001 format
    forum = Column(String(50), nullable=False)
    case_type = Column(String(100))
    case_no = Column(String(50))
    connected_case_nos = Column(Text)  # Comma separated
    is_appeal = Column(Boolean, default=False)
    lower_court_case_no = Column(String(50))
    lower_court = Column(String(100))
    lower_court_order_date = Column(Date)
    lower_court_order_doc = Column(String(255))  # File path
    
    counsel_name = Column(String(100))
    counsel_contact = Column(String(20))
    asg_engaged = Column(Boolean, default=False)
    
    brief_facts = Column(Text)
    
    last_hearing_date = Column(Date)
    next_hearing_date = Column(Date)
    
    affidavit_status = Column(String(50))
    case_status = Column(String(50), default=CaseStatus.FILED.value)
    
    final_order_doc = Column(String(255))
    final_order_date = Column(Date)
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    petitioners = relationship("Party", back_populates="case", foreign_keys="Party.case_id", 
                               primaryjoin="and_(Case.id==Party.case_id, Party.party_type=='petitioner')",
                               overlaps="respondents,case")
    respondents = relationship("Party", back_populates="case", foreign_keys="Party.case_id",
                               primaryjoin="and_(Case.id==Party.case_id, Party.party_type=='respondent')",
                               overlaps="petitioners,case")
    documents = relationship("Document", back_populates="case")
    hearings = relationship("Hearing", back_populates="case", order_by="desc(Hearing.hearing_date)")
    
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class Party(Base):
    __tablename__ = "parties"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    party_type = Column(String(20), nullable=False)  # petitioner or respondent
    party_number = Column(Integer, nullable=False)  # P1, P2, R1, R2 etc
    name = Column(String(200), nullable=False)
    address = Column(Text)
    
    case = relationship("Case", back_populates="petitioners", foreign_keys=[case_id], overlaps="petitioners,respondents")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    doc_type = Column(String(100), nullable=False)
    doc_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    filing_date = Column(Date)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    
    case = relationship("Case", back_populates="documents")
    uploader = relationship("User")


class Hearing(Base):
    __tablename__ = "hearings"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    hearing_date = Column(Date, nullable=False)
    brief = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    case = relationship("Case", back_populates="hearings")
    creator = relationship("User")


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

