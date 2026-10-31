# Audio Transcription API

## 1. Project Overview

This project implements a speech-to-text transcription service using Python, FastAPI, and Faster-Whisper.

The API accepts audio files, processes spoken language using a pretrained Whisper model, and returns the transcription along with segment-level timestamps.

The objective is to provide a simple REST API that can convert audio into text and make the results available in a structured JSON response.

## 2. Technologies Used

- **Python:** Main programming language.
- **FastAPI:** Used to build REST API endpoints.
- **Faster-Whisper:** Open-source speech recognition implementation used for audio transcription.
- **Uvicorn:** ASGI server used to run the FastAPI application.
- **PyAV:** Used by Faster-Whisper for audio decoding.
- **UUID:** Generates unique identifiers for transcription jobs.

## 3. Design Decisions

### Why FastAPI?

I selected FastAPI because it provides a lightweight framework for building REST APIs, supports file uploads, and automatically generates interactive API documentation through Swagger UI.

### Why Faster-Whisper?

I selected Faster-Whisper because it provides an optimized implementation of the Whisper speech recognition model. It supports multiple languages, automatic language detection, and timestamped transcription segments.

I used a pretrained model rather than training a speech recognition model from scratch because the assessment focuses on engineering and integration decisions.

### Why Local Processing?

The model runs locally on the CPU, so the application does not require an external speech-to-text API key. I configured INT8 computation to reduce memory requirements.

### Why Temporary File Storage?

Uploaded audio is temporarily saved so the transcription model can process it. The temporary file is deleted after processing to avoid unnecessary disk usage.

### Why Background Tasks?

FastAPI BackgroundTasks allows the upload endpoint to return a job ID while transcription continues in the background. This also enables clients to check job status and retrieve results separately.

For this assessment, job information is stored in memory. A production implementation would use persistent storage and a dedicated task queue.

## 4. Transcription Workflow

1. The client uploads an audio file.
2. The API validates the file extension and size.
3. The audio is temporarily stored.
4. A unique job ID is generated.
5. A background task processes the audio using Faster-Whisper.
6. The model detects the spoken language and generates text.
7. Segment-level timestamps are collected.
8. The job status is updated.
9. The client retrieves the completed transcription through the result endpoint.

## 5. Supported Audio Formats

The API accepts the following file extensions:

- WAV
- MP3
- M4A
- FLAC
- OGG
- WEBM

The maximum upload size is 100 MB per file.

Faster-Whisper uses its audio decoding dependencies to process supported formats.

## 6. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Checks API health |
| POST | `/transcribe` | Uploads audio and starts transcription |
| GET | `/transcriptions/{job_id}/status` | Checks transcription job status |
| GET | `/transcriptions/{job_id}` | Retrieves the transcription result |

### Example Transcription Response

```json
{
  "job_id": "generated-unique-id",
  "filename": "force.mp3",
  "language": "en",
  "duration": 3.53,
  "text": "The force will be with you, always.",
  "segments": [
    {
      "start": 0.0,
      "end": 3.0,
      "text": "The force will be with you, always."
    }
  ]
}
```

## 7. How to Run the Application

### Install Dependencies

```bash
pip install fastapi uvicorn faster-whisper python-multipart
pip install av==18.0.0
```

### Start the API

```bash
python -m uvicorn app:app --reload
```

### Open API Documentation

Open the following URL in your browser:

http://127.0.0.1:8000/docs

The Swagger interface allows users to test all four endpoints and upload audio files.

## 8. Error Handling

The API handles several common errors:

- Unsupported audio formats return HTTP 400.
- Empty audio files return HTTP 400.
- Files exceeding the 100 MB limit return HTTP 413.
- Unknown transcription job IDs return HTTP 404.
- Transcription failures update the job status to failed.

## 9. Handling Long Audio Files

The implementation uses Faster-Whisper's voice activity detection filter (`vad_filter=True`) to help filter silent portions of audio.

The model returns transcription segments with timestamps.

For very long recordings, a production enhancement would be to split audio into smaller overlapping chunks, process them independently, and combine the results while adjusting timestamps.

## 10. Future Improvements

For a production-ready implementation, I would consider:

- Using PostgreSQL to persist job information and transcription results.
- Using Amazon S3 or Azure Blob Storage for audio files.
- Introducing Redis, Celery, or RabbitMQ for reliable background processing.
- Implementing retry mechanisms for failed jobs.
- Adding authentication, rate limiting, and upload security.
- Adding dedicated workers to handle concurrent transcription requests.
- Implementing chunk-based processing for long audio recordings.

## 11. Testing

The API was tested using an MP3 audio file containing spoken English.

The transcription service successfully detected the language and generated:

"The force will be with you, always."

The response included the complete transcription, audio duration, detected language, and segment-level timestamps.

---

**Note:** This is an assessment-level implementation. The current job store is in memory, and background tasks are handled by FastAPI rather than a persistent distributed queue.