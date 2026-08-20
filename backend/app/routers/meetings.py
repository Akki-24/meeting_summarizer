import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db, SessionLocal
from app.models import Meeting
from app.schemas import MeetingResponse, MeetingUploadResponse
from app.services.pipeline import process_meeting_pipeline

router = APIRouter(prefix="/meetings", tags=["meetings"])

@router.post("/upload", response_model=MeetingUploadResponse)
async def upload_meeting_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    allowed_extensions = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".mp4"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {ext}")

    meeting_id = str(uuid.uuid4())
    saved_filename = f"{meeting_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    meeting = Meeting(
        id=meeting_id,
        filename=file.filename,
        audio_path=file_path,
        status="pending"
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # Hand off long-running transcription & processing to background task
    background_tasks.add_task(process_meeting_pipeline, meeting_id, SessionLocal)

    return MeetingUploadResponse(
        id=meeting.id,
        filename=meeting.filename,
        status=meeting.status,
        message="Audio uploaded successfully. Processing started in background."
    )

@router.get("", response_model=List[MeetingResponse])
def list_meetings(db: Session = Depends(get_db)):
    return db.query(Meeting).order_by(Meeting.created_at.desc()).all()

@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting