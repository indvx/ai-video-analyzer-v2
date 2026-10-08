import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import video, chat
from app.core.config import settings

# Create required storage & log directories on startup
os.makedirs(settings.video_org_dir, exist_ok=True)
os.makedirs(settings.video_temp_dir, exist_ok=True)
os.makedirs(settings.log_file_dir, exist_ok=True)

app = FastAPI(
    title="Video Analyzer with AI API",
    description="Backend API for AI-powered video summarization, subclip analysis, and RAG Q&A",
    version="1.0.0",
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(video.router)
app.include_router(chat.router)


@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "healthy",
        "service": "Video Analyzer with AI API",
        "version": "1.0.0",
    }
