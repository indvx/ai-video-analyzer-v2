from sqlalchemy import Column, Integer, String, func, DateTime
from database import Base


class Video(Base):
    """SQLAlchemy model representing the `videos` table in the database.
    
    Stores metadata for uploaded video files. The actual video binary is kept
    on disk (inside settings.video_org_dir), while this row tracks its name,
    format, classification tags, and creation dates.
    """
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    # The filename as stored on disk (e.g., 'sample_video.mp4')
    video_name = Column(String(255), nullable=False)
    # Optional genre or category (e.g., 'movie', 'tutorial', 'song')
    category = Column(String(255), nullable=True)
    # Audience suitability rating (e.g., 'All ages', 'PG-13', 'Adult')
    suitability = Column(String(255), nullable=True)
    # Video container/format (defaults to 'mp4')
    video_type = Column(String(255), nullable=True)
    
    # Timestamps handled directly by the database server
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=func.now())
