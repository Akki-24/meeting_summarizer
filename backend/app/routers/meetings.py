import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Meeting
from app.schemas import MeetingResponse
from app.config import settings
from app.services.pipeline import process_meeting_pipeline

router = APIRouter(prefix="/meetings", tags=["meetings"])

@router.post("/upload", response_model=MeetingResponse)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    meeting_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1] or ".mp4"
    saved_filename = f"{meeting_id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    meeting = Meeting(
        id=meeting_id,
        title=file.filename,
        file_path=file_path,
        status="pending"
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # Trigger background worker
    background_tasks.add_task(process_meeting_pipeline, meeting.id)

    return meeting

@router.get("", response_model=list[MeetingResponse])
def get_all_meetings(db: Session = Depends(get_db)):
    return db.query(Meeting).order_by(Meeting.created_at.desc()).all()

@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting