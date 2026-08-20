import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    audio_path = Column(String(500), nullable=False)
    
    # Status: pending -> transcribing -> summarizing -> done / failed
    status = Column(String(50), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Transcription: List of segments [{"speaker": "SPEAKER_00", "start": 0.0, "end": 4.2, "text": "..."}]
    raw_transcript = Column(Text, nullable=True)
    diarized_segments = Column(JSON, nullable=True)
    
    # Summaries & structured output
    summary = Column(Text, nullable=True)
    decisions = Column(JSON, nullable=True)      # list of string decisions
    action_items = Column(JSON, nullable=True)   # list of action item objects
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)