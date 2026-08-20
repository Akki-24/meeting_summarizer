from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SpeakerSegment(BaseModel):
    speaker: str = "Unknown"
    start: float
    end: float
    text: str

class ActionItemCandidate(BaseModel):
    task: str = Field(..., description="Actionable task to be done")
    owner: str = Field(default="Unassigned", description="Name or Speaker ID responsible")
    due_date: Optional[str] = Field(default=None, description="Due date or timeframe if mentioned")
    source_quote: str = Field(..., description="Verbatim transcript sentence grounding this item")

class ChunkExtractionResult(BaseModel):
    summary_points: List[str] = []
    decisions: List[str] = []
    action_items: List[ActionItemCandidate] = []

class FinalMeetingSummary(BaseModel):
    summary: str
    decisions: List[str]
    action_items: List[ActionItemCandidate]

class MeetingResponse(BaseModel):
    id: str
    filename: str
    status: str
    error_message: Optional[str] = None
    raw_transcript: Optional[str] = None
    diarized_segments: Optional[List[SpeakerSegment]] = None
    summary: Optional[str] = None
    decisions: Optional[List[str]] = None
    action_items: Optional[List[ActionItemCandidate]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MeetingUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str