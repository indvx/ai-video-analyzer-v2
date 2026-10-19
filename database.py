from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from app.core.config import settings

# Format connection string from environment variables (e.g., postgresql://user:pass@host:port/dbname)
SQLALCHEMY_DATABASE_URL = "{}://{}:{}@{}:{}/{}".format(
    settings.database_connection,
    settings.database_user,
    settings.database_password,
    settings.database_host,
    settings.database_port,
    settings.database_name,
)

# Engine setup:
# - pool_size=5: keeps a modest connection pool suitable for concurrent API traffic
# - pool_pre_ping=True: tests connections before running queries, preventing "server closed connection" errors
# - isolation_level="READ COMMITTED": ensures queries see only committed transactions without locking issues
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    pool_pre_ping=True,
    isolation_level="READ COMMITTED",
)

# Scoped session ensures thread safety across concurrent FastAPI request handlers
SessionLocal = sessionmaker(bind=engine)
SessionLocal = scoped_session(SessionLocal)

# Declarative base model that all ORM entities inherit from
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session for a single request

    and guarantees connection cleanup in the `finally` block when done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
