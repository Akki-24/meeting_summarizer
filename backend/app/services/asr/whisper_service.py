import os
from typing import List, Dict, Any, Tuple
from app.config import settings

class WhisperASRService:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        """Lazy-loads Faster-Whisper into memory only when audio is transcribed."""
        if self._model is None:
            from faster_whisper import WhisperModel
            compute_type = "float16" if settings.WHISPER_DEVICE == "cuda" else "int8"
            print(f"[ASR] Loading Faster-Whisper model '{settings.WHISPER_MODEL_SIZE}' on {settings.WHISPER_DEVICE}...")
            self._model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type=compute_type
            )
            print("[ASR] Model loaded successfully.")
        return self._model

    def transcribe(self, audio_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at: {audio_path}")

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        diarized_segments = []
        full_text_list = []
        speaker_idx = 1
        last_end = 0.0

        for segment in segments:
            if segment.start - last_end > 1.5 and last_end > 0:
                speaker_idx = 2 if speaker_idx == 1 else 1

            speaker_tag = f"Speaker {speaker_idx}"
            text = segment.text.strip()

            diarized_segments.append({
                "speaker": speaker_tag,
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text
            })
            full_text_list.append(f"[{speaker_tag} {round(segment.start, 1)}s]: {text}")
            last_end = segment.end

        raw_transcript = "\n".join(full_text_list)
        return raw_transcript, diarized_segments

asr_service = WhisperASRService()