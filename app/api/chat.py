import os
from fastapi import APIRouter, HTTPException
from app.schemas.video_schemas import QuestionRequest, QuestionResponse
from app.services.utility import UtilityService
from logger_app import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)

# Router for conversational AI chat and video Q&A endpoints
router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

utility_service = UtilityService()


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(req: QuestionRequest):
    """Answers user questions about a specific video using semantic RAG retrieval.
    
    Combines ChromaDB vector search with LangGraph conversational memory to support
    multi-turn Q&A across the video's content and transcripts.
    """
    try:
        # Validate that the query is not whitespace-only
        if not req.question or not req.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        video_path = os.path.join(settings.video_org_dir, req.video_name)
        
        # If the frontend didn't supply an ongoing chat thread ID, use video_name as the default bucket
        thread_id = req.thread_id or req.video_name

        answer = utility_service.generate_answer(
            video_path=video_path,
            video_name=req.video_name,
            question=req.question.strip(),
            thread_id=thread_id,
        )

        return QuestionResponse(
            question=req.question,
            answer=answer,
            thread_id=thread_id,
        )
    except Exception as e:
        logger.error(f"Error generating answer for question '{req.question}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
