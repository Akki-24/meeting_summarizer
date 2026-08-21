import os
import tempfile
import subprocess
import torch
import soundfile as sf
from faster_whisper import WhisperModel
from app.config import settings

class WhisperASRService:
    def __init__(self):
        # 1. Initialize Whisper ASR
        self.whisper_model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE
        )

        # 2. Initialize PyAnnote Diarization Pipeline if HF_TOKEN is configured
        self.diarization_pipeline = None
        if settings.HF_TOKEN:
            try:
                from pyannote.audio import Pipeline
                print("[ASR] Loading PyAnnote acoustic speaker diarization pipeline...")
                try:
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        token=settings.HF_TOKEN
                    )
                except TypeError:
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=settings.HF_TOKEN
                    )

                device = torch.device(settings.WHISPER_DEVICE if torch.cuda.is_available() and settings.WHISPER_DEVICE == "cuda" else "cpu")
                self.diarization_pipeline.to(device)
                print("[ASR] PyAnnote Diarization Pipeline loaded successfully.")
            except Exception as e:
                print(f"[ASR] Warning: Could not initialize PyAnnote ({e}). Falling back to turn segmentation.")
                self.diarization_pipeline = None

    def _convert_to_wav(self, audio_path: str) -> str:
        """Converts media format to 16kHz mono WAV via ffmpeg."""
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav.close()

        cmd = [
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            temp_wav.name
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return temp_wav.name

    def _get_speaker_turns(self, audio_path: str) -> list[dict]:
        """Runs acoustic clustering on converted WAV tensor."""
        if not self.diarization_pipeline:
            return []

        temp_wav_path = None
        try:
            temp_wav_path = self._convert_to_wav(audio_path)
            data, sample_rate = sf.read(temp_wav_path)
            waveform = torch.from_numpy(data).float().unsqueeze(0)

            audio_input = {
                "waveform": waveform,
                "sample_rate": sample_rate
            }

            output = self.diarization_pipeline(audio_input)
            annotation = getattr(output, "speaker_diarization", output)

            speaker_turns = []
            for turn, _, speaker in annotation.itertracks(yield_label=True):
                speaker_turns.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
            return speaker_turns
        except Exception as e:
            print(f"[ASR] Diarization runtime error: {e}")
            return []
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

    def _match_speaker(self, seg_start: float, seg_end: float, speaker_turns: list[dict], fallback_id: int) -> str:
        """Matches segment to the PyAnnote speaker having maximum temporal intersection."""
        if not speaker_turns:
            return f"Turn {fallback_id}"

        speaker_overlaps = {}
        for turn in speaker_turns:
            # Calculate overlap interval [max(starts), min(ends)]
            overlap_start = max(seg_start, turn["start"])
            overlap_end = min(seg_end, turn["end"])
            overlap_duration = max(0.0, overlap_end - overlap_start)

            if overlap_duration > 0:
                speaker = turn["speaker"]
                speaker_overlaps[speaker] = speaker_overlaps.get(speaker, 0.0) + overlap_duration

        if speaker_overlaps:
            # Pick speaker with largest temporal overlap
            best_speaker = max(speaker_overlaps, key=speaker_overlaps.get)
            num_part = "".join(filter(str.isdigit, best_speaker))
            speaker_idx = int(num_part) + 1 if num_part else 1
            return f"Speaker {speaker_idx}"

        # Fallback to closest acoustic boundary if segment sits in a silence gap
        closest_turn = min(speaker_turns, key=lambda t: min(abs(t["start"] - seg_start), abs(t["end"] - seg_end)))
        num_part = "".join(filter(str.isdigit, closest_turn["speaker"]))
        speaker_idx = int(num_part) + 1 if num_part else 1
        return f"Speaker {speaker_idx}"

    def transcribe(self, audio_path: str) -> list[dict]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at: {audio_path}")

        speaker_turns = self._get_speaker_turns(audio_path)

        segments_generator, _ = self.whisper_model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True
        )

        segments = []
        seg_id = 1

        for segment in segments_generator:
            text = segment.text.strip()
            if not text:
                continue

            seg_start = round(segment.start, 2)
            seg_end = round(segment.end, 2)

            assigned_speaker = self._match_speaker(seg_start, seg_end, speaker_turns, seg_id)

            segments.append({
                "id": seg_id,
                "speaker": assigned_speaker,
                "start_time": seg_start,
                "end_time": seg_end,
                "text": text
            })
            seg_id += 1

        return segments

asr_service = WhisperASRService()