from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from app.core.config import settings

# Build connection string from environment variables
SQLALCHEMY_DATABASE_URL = "{}://{}:{}@{}:{}/{}".format(
    settings.database_connection,
    settings.database_user,
    settings.database_password,
    settings.database_host,
    settings.database_port,
    settings.database_name,
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    pool_pre_ping=True,
    isolation_level="READ COMMITTED",
)

# Use scoped session for thread safety across requests
SessionLocal = sessionmaker(bind=engine)
SessionLocal = scoped_session(SessionLocal)

Base = declarative_base()


def get_db():
    """Yield a database session context."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
