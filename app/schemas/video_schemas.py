from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoBase(BaseModel):
    id: int
    video_name: str
    category: Optional[str] = None
    suitability: Optional[str] = None
    video_type: Optional[str] = None
    duration: Optional[int] = 0
    duration_formatted: Optional[str] = "0:00"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoCreate(BaseModel):
    video_name: str
    video_type: Optional[str] = "mp4"


class VideoListResponse(BaseModel):
    total: int
    videos: List[VideoBase]
    page: int
    limit: int


class SummaryRequest(BaseModel):
    video_name: str
    prompt: Optional[str] = ""
    is_new_video: Optional[bool] = False


class CustomPromptRequest(BaseModel):
    summary_type: Optional[str] = "Short summary"
    summary_duration: Optional[int] = 1
    summary_bullet: Optional[bool] = False
    detect_harmful_words: Optional[bool] = False
    detect_harmful_pictures: Optional[bool] = False
    age: Optional[int] = None
    summary_language: Optional[str] = "English"


class TimeRangeSummaryRequest(BaseModel):
    video_name: str
    start_time: int
    end_time: int
    prompt: Optional[str] = ""


class SummaryResponse(BaseModel):
    video_name: str
    summary: str


class QuestionRequest(BaseModel):
    video_name: str
    question: str
    thread_id: Optional[str] = None


class QuestionResponse(BaseModel):
    question: str
    answer: str
    thread_id: str
