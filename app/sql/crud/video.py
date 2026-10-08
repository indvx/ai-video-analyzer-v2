from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.sql.model.video import Video


def create_video(db: Session, video_name, video_type):
    new_video = Video(
        video_name=video_name,
        video_type=video_type,
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    return new_video


def get_video_by_name(db: Session, video_name):
    return db.query(Video).filter(Video.video_name == video_name).first()


def get_video_list(
    db: Session,
    filter: str = None,
    limit: int = 20,
    page: int = 1,
) -> dict:
    query = db.query(Video)

    if filter and filter != "":
        search_filter = f"%{filter}%"
        query = query.filter(
            or_(
                Video.video_name.ilike(search_filter),
                Video.video_type.ilike(search_filter),
                Video.category.ilike(search_filter),
                Video.suitability.ilike(search_filter),
            )
        )

    total = query.count()
    if limit and limit != 0:
        if page < 1:
            page = 1
        query = query.limit(limit).offset((page - 1) * limit)

    videos = query.all()
    return {"total": total, "videos": videos, "page": page, "limit": limit}
