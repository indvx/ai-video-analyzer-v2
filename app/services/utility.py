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
    """Helper service bridging video media manipulations (MoviePy) with the LangGraph AI workflows."""

    def __init__(self):
        # Initialize and compile the LangGraph workflow pipeline once on startup
        self.langgraph_service = LanggraphService()
        self.graph = self.langgraph_service.build_pipeline()

    @staticmethod
    def format_time(seconds: int) -> str:
        """Formats an integer seconds count into human-friendly mm:ss string (e.g. 125 -> '2:05')."""
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"

    @staticmethod
    def get_video_duration(video_path: str) -> int:
        """Reads video duration in seconds via MoviePy.
        
        Always explicitly closes the clip reader to prevent open file descriptor leaks.
        """
        try:
            if os.path.exists(video_path):
                clip = VideoFileClip(video_path)
                duration = int(clip.duration)
                # Important: release the file lock immediately after reading header metadata
                clip.close()
                return duration
        except Exception as e:
            logger.error(f"Error calculating duration for {video_path}: {e}")
        return 0

    @staticmethod
    def build_custom_prompt(req: CustomPromptRequest) -> str:
        """Translates user preferences from the frontend UI into a structured instruction for the LLM."""
        prompt_parts = []

        if req.summary_type:
            prompt_parts.append(f"Generate a {req.summary_type.lower()} of the given video.")

        if req.summary_duration:
            prompt_parts.append(f"The summary should be in {req.summary_duration} minute(s).")

        if req.summary_language:
            prompt_parts.append(f"Write the summary in {req.summary_language} language.")

        # Age-appropriate content evaluation instructions
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

        # Content moderation checks
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
        """Executes the summarization pipeline on a video file.
        
        Passes `thread_id=video_name` so any follow-up questions can reference this video's conversation state.
        """
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
        """Cuts a video clip between `start_time` and `end_time` (seconds) and runs it through the AI summarizer."""
        os.makedirs(settings.video_temp_dir, exist_ok=True)
        
        # Render the subclip to a temporary file so the multimodal LLM can consume it directly
        clip = VideoFileClip(video_path).subclipped(start_time, end_time)
        new_file = f"{int(time.time())}_{uuid.uuid4().hex}.mp4"
        temp_path = os.path.join(settings.video_temp_dir, new_file)
        clip.write_videofile(temp_path, codec="libx264", audio_codec="aac", logger=None)
        clip.close()  # Release file lock before passing to LLM

        # Always clean up the temp file even if LLM inference times out or throws an error
        try:
            # `is_new_video=False` ensures subclip summaries are not pushed to Chroma (avoids polluting main video RAG)
            summary = self.generate_summary(temp_path, video_name, is_new_video=False, prompt=prompt)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return summary

    def generate_answer(
        self, video_path: str, video_name: str, question: str, thread_id: str = None
    ) -> str:
        """Executes the RAG pipeline to answer questions about a video.
        
        Uses the `thread_id` to maintain multi-turn chat memory in LangGraph.
        """
        # If no explicit chat session ID is passed, group conversation history by video filename
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
