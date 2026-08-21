from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SegmentResponse(BaseModel):
    id: str
    speaker: str
    start_time: float
    end_time: float
    text: str
    model_config = ConfigDict(from_attributes=True)

class ActionItemResponse(BaseModel):
    id: str
    task: str
    owner: str
    due_date: str
    source_quote: str | None = None
    is_grounded: bool = False
    grounding_score: float = 0.0
    model_config = ConfigDict(from_attributes=True)

class DecisionResponse(BaseModel):
    id: str
    decision_text: str
    model_config = ConfigDict(from_attributes=True)

class MeetingResponse(BaseModel):
    id: str
    title: str
    status: str
    summary: str | None = None
    raw_transcript: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    segments: list[SegmentResponse] = []
    action_items: list[ActionItemResponse] = []
    decisions: list[DecisionResponse] = []

    model_config = ConfigDict(from_attributes=True)