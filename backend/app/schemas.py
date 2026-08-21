from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TranscriptSegmentResponse(BaseModel):
    id: str
    speaker: str
    start_time: float
    end_time: float
    text: str

    class Config:
        from_attributes = True

class ActionItemResponse(BaseModel):
    id: str
    task: str
    owner: str
    due_date: str
    source_quote: Optional[str] = None
    is_grounded: bool
    grounding_score: float
    matched_segment_id: Optional[str] = None

    class Config:
        from_attributes = True

class MeetingDecisionResponse(BaseModel):
    id: str
    decision_text: str

    class Config:
        from_attributes = True

class MeetingResponse(BaseModel):
    id: str
    title: str
    file_path: str
    status: str
    summary: Optional[str] = None
    raw_transcript: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    segments: List[TranscriptSegmentResponse] = []
    action_items: List[ActionItemResponse] = []
    decisions: List[MeetingDecisionResponse] = []

    class Config:
        from_attributes = True