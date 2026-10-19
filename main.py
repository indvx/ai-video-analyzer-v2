import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import video, chat
from app.core.config import settings

# Ensure required storage directories exist before handling any requests.
# This prevents runtime FileNotFoundError when saving uploads, writing subclips,
# persisting Chroma embeddings, or writing logs.
os.makedirs(settings.video_org_dir, exist_ok=True)
os.makedirs(settings.video_temp_dir, exist_ok=True)
os.makedirs(settings.log_file_dir, exist_ok=True)
os.makedirs(settings.vector_db_dir_name, exist_ok=True)

app = FastAPI(
    title="Video Analyzer with AI API",
    description="Backend API for AI-powered video summarization, subclip analysis, and RAG Q&A",
    version="1.0.0",
)

# Allow all origins during development and cross-domain access from frontend UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register feature routers: video asset management and RAG-based chat Q&A
app.include_router(video.router)
app.include_router(chat.router)


@app.get("/", tags=["Health Check"])
def read_root():
    """Simple ping endpoint for uptime monitoring and container readiness probes."""
    return {
        "status": "healthy",
        "service": "Video Analyzer with AI API",
        "version": "1.0.0",
    }
