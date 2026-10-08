from sqlalchemy import Column, Integer, String, func, DateTime
from database import Base


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    video_name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=True)
    suitability = Column(String(255), nullable=True)
    video_type = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=None, onupdate=func.now())
