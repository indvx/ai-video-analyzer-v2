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
│   ├── versions/              # Auto-generated versioned migrations
│   ├── env.py                 # Alembic runtime configuration
│   └── script.py.mako         # Migration script template
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
- Alembic (for database migrations)

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

## Database Setup & Migrations with Alembic

### What is Alembic?

Alembic is a lightweight SQL database migration tool for SQLAlchemy. It allows you to:
- Automate schema changes (create tables, add columns, modify constraints, etc.)
- Track database version history
- Easily upgrade and downgrade between schema versions
- Collaborate on database changes without manual SQL

### Initial Database Setup

Before running migrations, ensure your MySQL database exists:

```bash
mysql -u root -p
```

```sql
CREATE DATABASE ai;
EXIT;
```

### Running Migrations

The first time you set up the project, apply all migrations to create the initial schema:

```bash
alembic upgrade head
```

This creates all necessary tables (e.g., the `videos` table) to match your SQLAlchemy models.

### Checking Migration Status

To see which migrations have been applied:

```bash
alembic current
```

To view the migration history:

```bash
alembic history
```

### Creating a New Migration

When you add or modify a SQLAlchemy model in `app/sql/model/`, generate a migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

This creates a new versioned migration file in `alembic/versions/` that Alembic will track.

Example:

```bash
alembic revision --autogenerate -m "Add suitability column to videos table"
```

### Applying Migrations

After creating a migration, apply it to the database:

```bash
alembic upgrade head
```

### Rolling Back Migrations

If you need to undo the most recent migration:

```bash
alembic downgrade -1
```

To downgrade to a specific revision:

```bash
alembic downgrade <revision_id>
```

### Migration Files

All migration scripts are stored in `alembic/versions/` with names like:
```
001_initial_schema.py
002_add_suitability_column.py
```

Each file contains `upgrade()` and `downgrade()` functions that define how to apply and undo the changes.

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

## Database Schema

The project uses SQLAlchemy models under `app/sql/model` and CRUD helpers under `app/sql/crud` to manage video metadata.

### Video Table

The `videos` table stores uploaded video metadata:

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT | Primary key, auto-increment |
| `video_name` | VARCHAR(255) | Unique identifier for the video file |
| `category` | VARCHAR(255) | Optional content category (e.g., "movie", "tutorial") |
| `suitability` | VARCHAR(255) | Optional age/audience rating (e.g., "PG-13") |
| `video_type` | VARCHAR(255) | File format (e.g., "mp4") |
| `created_at` | DATETIME | Timestamp when the video was uploaded |
| `updated_at` | DATETIME | Timestamp of last modification |

Migrations for this table are managed through Alembic. To view or modify the schema, update the model in `app/sql/model/video.py` and create a new migration.

## Notes

- This repository is designed as a backend service and expects a frontend client or API consumer to upload and interact with videos.
- Some configuration values are intentionally set via `.env` rather than hardcoded in the source tree.
- Database schema changes are managed through Alembic migrations. Always use `alembic revision --autogenerate` when modifying SQLAlchemy models.
- The project uses a scoped session for thread-safe database access across concurrent requests.

## License

This project does not appear to include a license file in the current repository snapshot. If you intend to publish or distribute it, add an explicit license before doing so.

## Contributing

Feel free to fork the repository and submit pull requests with improvements, bug fixes, or new AI analysis features.
