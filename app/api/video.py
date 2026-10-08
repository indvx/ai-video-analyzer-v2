import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.schemas.video_schemas import (
    VideoBase,
    VideoListResponse,
    SummaryRequest,
    CustomPromptRequest,
    TimeRangeSummaryRequest,
    SummaryResponse,
)
from app.services.utility import UtilityService
from app.services.ai_service.vector_store import VectorStoreService
from app.sql.crud.video import (
    create_video,
    get_video_by_name,
    get_video_by_id,
    get_video_list,
    delete_video_by_id,
)
from database import get_db
from logger_app import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/api/video",
    tags=["Video"],
    responses={404: {"description": "Not found"}},
)

utility_service = UtilityService()
vector_store_service = VectorStoreService()


@router.post("/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    video_type: Optional[str] = Form("mp4"),
    generate_initial_summary: Optional[bool] = Form(False),
    db: Session = Depends(get_db),
):
    """Upload a new video file, register in DB, calculate duration, and optionally generate initial summary."""
    try:
        os.makedirs(settings.video_org_dir, exist_ok=True)
        video_name = file.filename
        if not video_name:
            raise HTTPException(status_code=400, detail="Filename is required")

        save_path = os.path.join(settings.video_org_dir, video_name)
        
        # Save file to ORG_DIR
        with open(save_path, "wb") as f:
            f.write(await file.read())

        is_new_video = False
        existing_video = get_video_by_name(db, video_name)
        if not existing_video:
            existing_video = create_video(db, video_name, video_type)
            is_new_video = True

        duration = utility_service.get_video_duration(save_path)
        formatted_duration = utility_service.format_time(duration)

        summary = None
        if generate_initial_summary:
            summary = utility_service.generate_summary(
                video_path=save_path,
                video_name=video_name,
                is_new_video=is_new_video,
            )

        return {
            "message": "Video uploaded successfully",
            "video": {
                "id": existing_video.id,
                "video_name": existing_video.video_name,
                "video_type": existing_video.video_type,
                "duration": duration,
                "duration_formatted": formatted_duration,
                "created_at": existing_video.created_at,
            },
            "summary": summary,
        }
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=VideoListResponse)
async def get_videos(
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get list of uploaded videos with search filtering and pagination."""
    try:
        data = get_video_list(db, filter=filter, limit=limit, page=page)
        enhanced_videos = []
        for v in data["videos"]:
            file_path = os.path.join(settings.video_org_dir, v.video_name)
            duration = utility_service.get_video_duration(file_path)
            enhanced_videos.append(
                VideoBase(
                    id=v.id,
                    video_name=v.video_name,
                    category=v.category,
                    suitability=v.suitability,
                    video_type=v.video_type,
                    duration=duration,
                    duration_formatted=utility_service.format_time(duration),
                    created_at=v.created_at,
                )
            )

        return VideoListResponse(
            total=data["total"],
            videos=enhanced_videos,
            page=data["page"],
            limit=data["limit"],
        )
    except Exception as e:
        logger.error(f"Error getting video list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/{video_id}", response_model=VideoBase)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get video details by ID."""
    video = get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = os.path.join(settings.video_org_dir, video.video_name)
    duration = utility_service.get_video_duration(file_path)

    return VideoBase(
        id=video.id,
        video_name=video.video_name,
        category=video.category,
        suitability=video.suitability,
        video_type=video.video_type,
        duration=duration,
        duration_formatted=utility_service.format_time(duration),
        created_at=video.created_at,
    )


@router.get("/stream/{video_name}")
async def stream_video(video_name: str):
    """Stream video file for playback in frontend video player."""
    file_path = os.path.join(settings.video_org_dir, video_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    return FileResponse(file_path, media_type="video/mp4")


@router.post("/summary", response_model=SummaryResponse)
async def generate_video_summary(req: SummaryRequest, db: Session = Depends(get_db)):
    """Generate full AI summary for an existing video file."""
    try:
        video_path = os.path.join(settings.video_org_dir, req.video_name)
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video file '{req.video_name}' not found")

        summary = utility_service.generate_summary(
            video_path=video_path,
            video_name=req.video_name,
            is_new_video=req.is_new_video,
            prompt=req.prompt or "",
        )
        return SummaryResponse(video_name=req.video_name, summary=summary)
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom-prompt", response_model=dict)
async def build_custom_prompt(req: CustomPromptRequest):
    """Generate custom summary prompt string based on user options."""
    prompt = utility_service.build_custom_prompt(req)
    return {"prompt": prompt}


@router.post("/range-summary", response_model=SummaryResponse)
async def generate_range_summary(req: TimeRangeSummaryRequest):
    """Generate summary for a specific time range segment of a video."""
    try:
        video_path = os.path.join(settings.video_org_dir, req.video_name)
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video file '{req.video_name}' not found")

        summary = utility_service.generate_range_summary(
            video_path=video_path,
            video_name=req.video_name,
            start_time=req.start_time,
            end_time=req.end_time,
            prompt=req.prompt or "",
        )
        return SummaryResponse(video_name=req.video_name, summary=summary)
    except Exception as e:
        logger.error(f"Error generating range summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{video_id}", response_model=dict)
async def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Delete video from DB, remove stored vector embeddings, and delete file from disk."""
    video = get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_name = video.video_name
    file_path = os.path.join(settings.video_org_dir, video_name)

    # Remove vector embeddings
    vector_store_service._delete_documents(video_name)

    # Delete record from database
    delete_video_by_id(db, video_id)

    # Remove file from disk
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"message": f"Video '{video_name}' deleted successfully", "id": video_id}
