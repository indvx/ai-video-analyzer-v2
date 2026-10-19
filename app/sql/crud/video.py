from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.sql.model.video import Video


def create_video(db: Session, video_name: str, video_type: str = "mp4", category: str = None, suitability: str = None):
    """Inserts a new video entry into the database and refreshes the object to get its auto-incremented ID."""
    new_video = Video(
        video_name=video_name,
        video_type=video_type,
        category=category,
        suitability=suitability,
    )
    db.add(new_video)
    db.commit()
    # Refresh retrieves the generated database fields (id, created_at)
    db.refresh(new_video)
    return new_video


def get_video_by_name(db: Session, video_name: str):
    """Fetches a video record by exact filename. Used to detect re-uploads of existing files."""
    return db.query(Video).filter(Video.video_name == video_name).first()


def get_video_by_id(db: Session, video_id: int):
    """Fetches a single video by its primary key ID."""
    return db.query(Video).filter(Video.id == video_id).first()


def delete_video_by_id(db: Session, video_id: int):
    """Removes a video row from the database.
    
    Returns True if found and deleted, False otherwise. Note that caller is responsible
    for also removing the MP4 file from disk and wiping associated vector embeddings.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        db.delete(video)
        db.commit()
        return True
    return False


def get_video_list(
    db: Session,
    filter: str = None,
    limit: int = 20,
    page: int = 1,
) -> dict:
    """Returns a paginated list of videos with optional multi-field fuzzy search."""
    query = db.query(Video)

    # If search text is provided, perform case-insensitive substring matching
    # across video filename, format, category, and audience suitability tags
    if filter and filter.strip():
        search_filter = f"%{filter.strip()}%"
        query = query.filter(
            or_(
                Video.video_name.ilike(search_filter),
                Video.video_type.ilike(search_filter),
                Video.category.ilike(search_filter),
                Video.suitability.ilike(search_filter),
            )
        )

    # Get total count before applying limit/offset for frontend pagination indicators
    total = query.count()
    if limit and limit > 0:
        # Guard against invalid 0 or negative page numbers
        if page < 1:
            page = 1
        query = query.offset((page - 1) * limit).limit(limit)

    videos = query.all()
    return {"total": total, "videos": videos, "page": page, "limit": limit}
