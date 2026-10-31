
from pathlib import Path
import tempfile
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from faster_whisper import WhisperModel

app = FastAPI(
    title="Audio Transcription API",
    description="Upload audio and receive transcription with timestamps.",
    version="2.0.0"
)

# Load the pretrained Whisper model once.
model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8",
    cpu_threads=2,
    num_workers=1
)

SUPPORTED_FORMATS = {
    ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Demo job storage (in memory).
jobs = {}


# 1. Health Check Endpoint
@app.get("/")
def home():
    return {
        "message": "Audio Transcription API is running",
        "status": "healthy"
    }


# Background transcription function
def process_transcription(job_id: str, audio_path: str, filename: str):

    jobs[job_id]["status"] = "processing"

    try:
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True
        )

        results = []
        full_text = []

        for segment in segments:
            text = segment.text.strip()

            results.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text
            })

            full_text.append(text)

        jobs[job_id]["result"] = {
            "job_id": job_id,
            "filename": filename,
            "language": info.language,
            "duration": round(info.duration, 2),
            "text": " ".join(full_text),
            "segments": results
        }

        jobs[job_id]["status"] = "completed"

    except Exception as error:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(error)

    finally:
        Path(audio_path).unlink(missing_ok=True)


# 2. Upload Audio and Start Transcription
@app.post("/transcribe", status_code=202)
def transcribe_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):

    extension = Path(file.filename or "").suffix.lower()

    if extension not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format."
        )

    audio_path = None

    try:
        audio_data = file.file.read()

        if not audio_data:
            raise HTTPException(
                status_code=400,
                detail="Uploaded audio file is empty."
            )

        if len(audio_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Audio file exceeds the 100 MB limit."
            )

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False
        ) as temp_audio:
            temp_audio.write(audio_data)
            audio_path = Path(temp_audio.name)

        job_id = str(uuid.uuid4())

        jobs[job_id] = {
            "status": "pending",
            "result": None,
            "error": None
        }

        background_tasks.add_task(
            process_transcription,
            job_id,
            str(audio_path),
            file.filename or "audio"
        )

        return {
            "message": "Transcription job submitted successfully",
            "job_id": job_id,
            "status": "pending"
        }

    except HTTPException:
        if audio_path:
            audio_path.unlink(missing_ok=True)
        raise

    except Exception as error:
        if audio_path:
            audio_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(error)}"
        )

    finally:
        file.file.close()


# 3. Check Transcription Job Status
@app.get("/transcriptions/{job_id}/status")
def get_transcription_status(job_id: str):

    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail="Transcription job not found."
        )

    return {
        "job_id": job_id,
        "status": jobs[job_id]["status"]
    }


# 4. Retrieve Transcription Result
@app.get("/transcriptions/{job_id}")
def get_transcription_result(job_id: str):

    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail="Transcription job not found."
        )

    job = jobs[job_id]

    if job["status"] in ["pending", "processing"]:
        return {
            "job_id": job_id,
            "status": job["status"],
            "message": "Transcription is not completed yet."
        }

    if job["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=job["error"]
        )

    return job["result"]
