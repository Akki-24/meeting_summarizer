import traceback
import uuid
from app.database import SessionLocal
from app.models import Meeting, TranscriptSegment, ActionItem, MeetingDecision
from app.services.asr.whisper_service import asr_service
from app.services.llm.gemini_provider import GeminiProvider
from app.services.grounding import grounding_verifier
from app.prompts import CHUNK_EXTRACTION_PROMPT, FINAL_SYNTHESIS_PROMPT

def run_map_reduce_extraction(llm_provider: GeminiProvider, diarized_segments: list[dict]) -> tuple[str, list[str], list[dict]]:
    """Runs 2-Stage Map-Reduce extraction on transcript segments."""
    chunk_size = 15
    chunks = [diarized_segments[i:i + chunk_size] for i in range(0, len(diarized_segments), chunk_size)]
    
    chunk_summaries = []
    chunk_decisions = []
    all_candidate_actions = []

    for idx, chunk in enumerate(chunks):
        formatted_chunk = "\n".join([
            f"[{s.get('speaker', 'Speaker')} | {s.get('start_time', 0.0)}s - {s.get('end_time', 0.0)}s]: {s.get('text', '')}"
            for s in chunk
        ])
        
        user_prompt = f"Analyze Meeting Chunk {idx + 1}/{len(chunks)}:\n\n{formatted_chunk}"
        chunk_data = llm_provider.generate_json(CHUNK_EXTRACTION_PROMPT, user_prompt)
        
        chunk_summaries.extend(chunk_data.get("key_points", []))
        chunk_decisions.extend(chunk_data.get("decisions", []))
        
        for item in chunk_data.get("action_items", []):
            all_candidate_actions.append({
                "task": item.get("task", ""),
                "owner": item.get("owner", "Unassigned"),
                "due_date": item.get("due_date", "None"),
                "source_quote": item.get("source_quote", "")
            })

    # Reduce Stage
    synthesis_input = (
        "Candidate Points:\n" + "\n".join([f"- {p}" for p in chunk_summaries]) + "\n\n"
        "Candidate Decisions:\n" + "\n".join([f"- {d}" for d in chunk_decisions])
    )
    
    final_output = llm_provider.generate_json(FINAL_SYNTHESIS_PROMPT, synthesis_input)
    executive_summary = final_output.get("executive_summary", "Summary generation completed.")
    final_decisions = final_output.get("decisions", chunk_decisions)

    return executive_summary, final_decisions, all_candidate_actions

def process_meeting_pipeline(meeting_id: str):
    """Safe background pipeline execution with local session management."""
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        # 1. Transcribe & Diarize
        meeting.status = "transcribing"
        db.commit()

        diarized_segments = asr_service.transcribe(meeting.file_path)
        if not diarized_segments:
            raise ValueError("ASR transcription yielded no audio segments.")

        meeting.raw_transcript = "\n".join([
            f"[{s['speaker']}] {s['text']}" for s in diarized_segments
        ])
        
        # Save segments and assign persistent DB UUIDs
        saved_db_segments = []
        for s in diarized_segments:
            segment_uuid = str(uuid.uuid4())
            db_segment = TranscriptSegment(
                id=segment_uuid,
                meeting_id=meeting.id,
                speaker=s["speaker"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                text=s["text"]
            )
            db.add(db_segment)
            # Retain DB UUID for grounding linker
            s_with_db_id = dict(s)
            s_with_db_id["id"] = segment_uuid
            saved_db_segments.append(s_with_db_id)

        db.commit()

        # 2. Map-Reduce Summarization
        meeting.status = "summarizing"
        db.commit()

        llm = GeminiProvider()
        summary, decisions, raw_actions = run_map_reduce_extraction(llm, saved_db_segments)
        
        meeting.summary = summary
        
        for dec in decisions:
            dec_text = dec if isinstance(dec, str) else dec.get("decision", "")
            if dec_text:
                db.add(MeetingDecision(meeting_id=meeting.id, decision_text=dec_text))
        db.commit()

        # 3. Grounding Verification (linked with actual DB segment UUIDs)
        verified_actions = grounding_verifier.verify_action_items(raw_actions, saved_db_segments)
        
        for act in verified_actions:
            db.add(ActionItem(
                meeting_id=meeting.id,
                matched_segment_id=act.get("matched_segment_id"),
                task=act.get("task", ""),
                owner=act.get("owner", "Unassigned"),
                due_date=act.get("due_date", "None"),
                source_quote=act.get("source_quote", ""),
                is_grounded=act.get("is_grounded", False),
                grounding_score=act.get("grounding_score", 0.0)
            ))

        meeting.status = "completed"
        meeting.error_message = None
        db.commit()
        print(f"[Pipeline] Meeting {meeting_id} completed successfully with segment grounding links.")

    except Exception as e:
        db.rollback()
        error_msg = traceback.format_exc()
        print(f"[Pipeline Error] Meeting {meeting_id} failed:\n{error_msg}")
        try:
            meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
            if meeting:
                meeting.status = "failed"
                meeting.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()