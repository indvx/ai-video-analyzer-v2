# AI Video Analyzer Backend

A FastAPI-based backend for uploading videos, generating AI summaries, extracting insights from specific time ranges, and answering questions about video content using a retrieval-augmented generation (RAG) workflow.

This project combines:
- FastAPI for API endpoints
- LangGraph for multi-step AI orchestration
- Chroma vector store for video summary retrieval
- MySQL for metadata storage
- OpenAI or Google Gemini LLMs for video understanding and Q&A
- MoviePy for video processing

## Features

- Upload video files and save them to disk
- Store video metadata in MySQL
- Calculate video duration and list videos with pagination/filtering
- Generate AI summaries for an entire video
- Generate summaries for custom time windows
- Build custom prompt templates based on audience, language, and safety settings
- Ask questions about previously analyzed videos using semantic retrieval
- Stream uploaded videos back to clients
- Delete videos and remove their vector embeddings

## Project Structure

```text
.
├── .env-copy                  # Sample environment configuration
├── README.md                  # Project documentation
├── alembic.ini                # Alembic migration configuration
├── alembic/                   # Database migration scripts
├── app/
│   ├── api/
│   │   ├── chat.py            # Chat Q&A endpoints
│   │   └── video.py           # Video upload/summary endpoints
│   ├── core/
│   │   └── config.py          # Environment-based settings loader
│   ├── schemas/
│   │   └── video_schemas.py   # Request/response models
│   ├── services/
│   │   ├── ai_service/
│   │   │   ├── langgraph.py   # LangGraph workflow for video analysis and RAG
│   │   │   ├── llm.py         # LLM provider setup
│   │   │   └── vector_store.py # Chroma vector DB setup
│   │   ├── utility.py        # Utility methods for summaries, subclips, duration
│   │   └── video.py          # Placeholder video service module
│   ├── sql/
│   │   ├── crud/
│   │   │   └── video.py       # CRUD for video metadata
│   │   └── model/
│   │       └── video.py       # Video SQLAlchemy model
│   └── __init__.py
├── database.py                # SQLAlchemy engine and DB session setup
├── logger_app.py              # Logging configuration
├── main.py                    # FastAPI app entry point
├── requirements.txt           # Python dependencies
├── videos/
│   ├── org_videos/            # Original uploaded videos
│   └── temp_videos/           # Temporary subclips for range summaries
├── logs/                      # Application logs
├── vector_db/                 # Chroma vector database storage
└── .gitignore
```

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- MySQL
- ChromaDB
- LangGraph
- LangChain
- OpenAI / Google Gemini
- MoviePy

## Environment Configuration

Copy the sample environment file and customize it:

```bash
cp .env-copy .env
```

Example values are defined in `.env-copy`:

```env
# LLM Config
LLM_PROVIDER=gemini
LLM_MODEL_NAME=gemini-2.5-flash
LLM_EMBEDDING_MODEL=models/embedding-001
GOOGLE_API_KEY=
OPENAI_API_KEY=

# Vector DB Config
VECTOR_DB_DIR_NAME=./vector_db/chroma_db
VECTOR_DB_COLLECTION_NAME=video_summaries

# Database Config
DATABASE_CONNECTION='mysql+pymysql'
DATABASE_HOST="127.0.0.1"
DATABASE_PORT="3306"
DATABASE_USER="root"
DATABASE_PASSWORD="root"
DATABASE_NAME="ai"

# Directories Config
VIDEO_TEMP_DIR=./videos/temp_videos
VIDEO_ORG_DIR=./videos/org_videos
LOG_FILE_DIR=./logs
```

Important notes:
- Set either `GOOGLE_API_KEY` or `OPENAI_API_KEY` depending on your chosen provider.
- Ensure the MySQL database exists before running the app.
- The app creates local storage folders automatically at startup if they are missing.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the App

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- http://localhost:8000
- Swagger docs: http://localhost:8000/docs

## API Endpoints

### Health

```http
GET /
```

Returns the service status and version.

### Video APIs

```http
POST /api/video/upload
GET /api/video/list
GET /api/video/get/{video_id}
GET /api/video/stream/{video_name}
POST /api/video/summary
POST /api/video/custom-prompt
POST /api/video/range-summary
DELETE /api/video/{video_id}
```

#### Upload video

```bash
curl -X POST "http://localhost:8000/api/video/upload" \
  -F "file=@example.mp4" \
  -F "video_type=mp4" \
  -F "generate_initial_summary=true"
```

#### Generate summary

```bash
curl -X POST "http://localhost:8000/api/video/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "video_name": "example.mp4",
    "prompt": "Provide a concise summary.",
    "is_new_video": false
  }'
```

#### Generate range summary

```bash
curl -X POST "http://localhost:8000/api/video/range-summary" \
  -H "Content-Type: application/json" \
  -d '{
    "video_name": "example.mp4",
    "start_time": 30,
    "end_time": 90,
    "prompt": "Summarize the scene in bullet points."
  }'
```

### Chat APIs

```http
POST /api/chat/ask
```

This endpoint answers questions about a specific uploaded video using a vector retrieval workflow.

Example:

```bash
curl -X POST "http://localhost:8000/api/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "video_name": "example.mp4",
    "question": "What happened in the first scene?",
    "thread_id": "example-thread"
  }'
```

## How It Works

1. A video is uploaded through the FastAPI API.
2. The backend saves the file in `VIDEO_ORG_DIR` and registers metadata in MySQL.
3. A LangGraph workflow loads the video, summarizes it with an LLM, and stores the summary chunks in ChromaDB.
4. When a user asks a question, the related summary chunks are retrieved and sent back to the model with chat context.
5. The answer is returned through the chat API.

## Database Notes

The project uses SQLAlchemy models under `app/sql/model` and CRUD helpers under `app/sql/crud` to manage video metadata. The model includes:

- `id`
- `video_name`
- `category`
- `suitability`
- `video_type`
- `created_at`
- `updated_at`

## Notes

- This repository is designed as a backend service and expects a frontend client or API consumer to upload and interact with videos.
- Some configuration values are intentionally set via `.env` rather than hardcoded in the source tree.
- The project includes Alembic configuration for future schema migrations.

## License

This project does not appear to include a license file in the current repository snapshot. If you intend to publish or distribute it, add an explicit license before doing so.

## Contributing

Feel free to fork the repository and submit pull requests with improvements, bug fixes, or new AI analysis features.

