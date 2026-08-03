"""
Speech Service: Transcribes audio using OpenAI Whisper (local model).
Demo mode returns mock transcription.
"""
import os
import tempfile
from app.config import get_settings

settings = get_settings()

DEMO_TRANSCRIPTION = (
    "There has been a road accident on the highway. "
    "One person is unconscious and bleeding from the head. "
    "Please send an ambulance immediately."
)


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe voice to text using Whisper.
    Returns: {transcription, language, duration_seconds}
    """
    if not audio_bytes:
        return {"transcription": "", "language": "en", "duration_seconds": 0}

    if settings.ai_mode == "full":
        try:
            return await _whisper_transcribe(audio_bytes, filename)
        except Exception as e:
            print(f"[Speech] Whisper failed: {e}. Using demo transcription.")

    return {
        "transcription": DEMO_TRANSCRIPTION,
        "language": "en",
        "duration_seconds": 8.5,
        "mode": "demo",
    }


async def _whisper_transcribe(audio_bytes: bytes, filename: str) -> dict:
    """Use local Whisper model for transcription."""
    import whisper

    model = whisper.load_model(settings.whisper_model)

    # Write bytes to temp file (Whisper needs file path)
    suffix = os.path.splitext(filename)[-1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path, fp16=False)
        return {
            "transcription": result["text"].strip(),
            "language": result.get("language", "en"),
            "duration_seconds": round(result.get("duration", 0), 1),
            "mode": "whisper",
        }
    finally:
        os.unlink(tmp_path)
