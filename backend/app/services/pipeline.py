import traceback
from sqlalchemy.orm import Session
from app.models import Meeting
from app.schemas import ActionItemCandidate
from app.services.asr.whisper_service import asr_service
from app.services.llm import get_llm_provider
from app.services.grounding import grounding_filter
from app.prompts import CHUNK_EXTRACTION_SYSTEM_PROMPT, FINAL_MERGE_SYSTEM_PROMPT

def split_transcript_into_chunks(diarized_segments: list, max_words: int = 800) -> list:
    """Groups diarized segments into context-bounded text chunks."""
    chunks = []
    current_chunk = []
    current_word_count = 0

    for seg in diarized_segments:
        text = f"[{seg['speaker']}]: {seg['text']}"
        word_count = len(text.split())
        
        if current_word_count + word_count > max_words and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [text]
            current_word_count = word_count
        else:
            current_chunk.append(text)
            current_word_count += word_count

    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks

def process_meeting_pipeline(meeting_id: str, db_session_factory):
    """Background worker task to orchestrate transcription, extraction, grounding, and storage."""
    db: Session = db_session_factory()
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        db.close()
        return

    try:
        # 1. ASR Transcription
        meeting.status = "transcribing"
        db.commit()

        raw_transcript, diarized_segments = asr_service.transcribe(meeting.audio_path)
        meeting.raw_transcript = raw_transcript
        meeting.diarized_segments = diarized_segments
        
        # 2. Chunking
        chunks = split_transcript_into_chunks(diarized_segments, max_words=800)
        
        # 3. LLM Extraction & Grounding Verification
        meeting.status = "summarizing"
        db.commit()

        llm = get_llm_provider()
        accumulated_summary_points = []
        accumulated_decisions = []
        accumulated_action_items = []

        for chunk_text in chunks:
            extracted_json = llm.generate_json(
                system_prompt=CHUNK_EXTRACTION_SYSTEM_PROMPT,
                user_content=chunk_text
            )
            
            accumulated_summary_points.extend(extracted_json.get("summary_points", []))
            accumulated_decisions.extend(extracted_json.get("decisions", []))
            
            raw_action_items = [
                ActionItemCandidate(**item) for item in extracted_json.get("action_items", [])
            ]
            verified = grounding_filter.verify_action_items(raw_action_items, raw_transcript)
            accumulated_action_items.extend(verified)

        # 4. Final Consolidation & Merge
        merge_payload = (
            f"Summary Points:\n" + "\n".join(f"- {p}" for p in accumulated_summary_points) +
            f"\n\nDecisions:\n" + "\n".join(f"- {d}" for d in accumulated_decisions) +
            f"\n\nAction Items:\n" + "\n".join(f"- [{a.owner}] {a.task} (Quote: {a.source_quote})" for a in accumulated_action_items)
        )

        final_json = llm.generate_json(
            system_prompt=FINAL_MERGE_SYSTEM_PROMPT,
            user_content=merge_payload
        )

        # 5. Persist Results
        meeting.summary = final_json.get("summary", "")
        meeting.decisions = final_json.get("decisions", accumulated_decisions)
        meeting.action_items = [item.model_dump() if hasattr(item, "model_dump") else item for item in accumulated_action_items]
        meeting.status = "done"
        db.commit()

    except Exception as e:
        db.rollback()
        meeting.status = "failed"
        meeting.error_message = f"{str(e)}\n{traceback.format_exc()}"
        db.commit()
    finally:
        db.close()