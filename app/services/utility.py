import os
import time
import uuid
from moviepy.video.io.VideoFileClip import VideoFileClip
from app.services.ai_service.langgraph import LanggraphService
from app.core.config import settings
from logger_app import setup_logger
from app.schemas.video_schemas import CustomPromptRequest

logger = setup_logger(__name__)


class UtilityService:
    """Helper service for video duration formatting, prompt generation, subclipping, and AI workflow integration."""

    def __init__(self):
        self.langgraph_service = LanggraphService()
        self.graph = self.langgraph_service.build_pipeline()

    @staticmethod
    def format_time(seconds: int) -> str:
        """Format total seconds into mm:ss."""
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"

    @staticmethod
    def get_video_duration(video_path: str) -> int:
        """Get video duration in seconds using MoviePy."""
        try:
            if os.path.exists(video_path):
                clip = VideoFileClip(video_path)
                duration = int(clip.duration)
                clip.close()
                return duration
        except Exception as e:
            logger.error(f"Error calculating duration for {video_path}: {e}")
        return 0

    @staticmethod
    def build_custom_prompt(req: CustomPromptRequest) -> str:
        """Build dynamic prompt string based on prompt options."""
        prompt_parts = []

        if req.summary_type:
            prompt_parts.append(f"Generate a {req.summary_type.lower()} of the given video.")

        if req.summary_duration:
            prompt_parts.append(f"The summary should be in {req.summary_duration} minute(s).")

        if req.summary_language:
            prompt_parts.append(f"Write the summary in {req.summary_language} language.")

        if req.age is not None:
            if req.age <= 18:
                prompt_parts.append(
                    f"Evaluate whether the video content (audio & visuals) is appropriate for viewers under {req.age} years old."
                )
            else:
                prompt_parts.append(
                    "Evaluate whether the video content (audio & visuals) is appropriate for a general adult audience."
                )

        if req.summary_bullet:
            prompt_parts.append(
                "Present the summary in well-structured bullet points, covering aspects such as video language, category (movie, song, cartoon), and tone."
            )

        if req.detect_harmful_words:
            prompt_parts.append(
                "Identify and highlight any harmful, offensive, or inappropriate words in the transcript."
            )

        if req.detect_harmful_pictures:
            prompt_parts.append(
                "Analyze and mention if the video contains harmful, violent, or inappropriate visuals."
            )

        return " ".join(prompt_parts).strip()

    def generate_summary(
        self, video_path: str, video_name: str, is_new_video: bool = False, prompt: str = ""
    ) -> str:
        """Generate AI-based summary for a video."""
        thread_id = video_name
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {
            "video_path": video_path,
            "video_name": video_name,
            "is_new_video": is_new_video,
            "prompt": prompt,
        }
        state = self.graph.invoke(inputs, config)  # type: ignore
        return state.get("summary", "")

    def generate_range_summary(
        self, video_path: str, video_name: str, start_time: int, end_time: int, prompt: str = ""
    ) -> str:
        """Generate AI summary for a specific time range segment of a video."""
        os.makedirs(settings.video_temp_dir, exist_ok=True)
        clip = VideoFileClip(video_path).subclipped(start_time, end_time)
        new_file = f"{int(time.time())}_{uuid.uuid4().hex}.mp4"
        temp_path = os.path.join(settings.video_temp_dir, new_file)
        clip.write_videofile(temp_path, codec="libx264", audio_codec="aac", logger=None)
        clip.close()

        try:
            summary = self.generate_summary(temp_path, video_name, is_new_video=False, prompt=prompt)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return summary

    def generate_answer(
        self, video_path: str, video_name: str, question: str, thread_id: str = None
    ) -> str:
        """Answer user questions about the video content via RAG workflow."""
        if not thread_id:
            thread_id = video_name
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {
            "video_path": video_path,
            "video_name": video_name,
            "question": question,
            "messages": [],
        }
        logger.info(f"===generate_answer===: {inputs}")
        state = self.graph.invoke(inputs, config)
        return state.get("answer", "")
