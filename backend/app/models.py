import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="pending", index=True)  # pending, transcribing, summarizing, completed, failed
    summary = Column(Text, nullable=True)
    raw_transcript = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    segments = relationship("TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    decisions = relationship("MeetingDecision", back_populates="meeting", cascade="all, delete-orphan")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    speaker = Column(String, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)

    meeting = relationship("Meeting", back_populates="segments")
    action_items = relationship("ActionItem", back_populates="matched_segment")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    matched_segment_id = Column(String, ForeignKey("transcript_segments.id"), nullable=True, index=True)
    task = Column(Text, nullable=False)
    owner = Column(String, default="Unassigned")
    due_date = Column(String, default="None")
    source_quote = Column(Text, nullable=True)
    is_grounded = Column(Boolean, default=False)
    grounding_score = Column(Float, default=0.0)

    meeting = relationship("Meeting", back_populates="action_items")
    matched_segment = relationship("TranscriptSegment", back_populates="action_items")


class MeetingDecision(Base):
    __tablename__ = "meeting_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    decision_text = Column(Text, nullable=False)

    meeting = relationship("Meeting", back_populates="decisions")