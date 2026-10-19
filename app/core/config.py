from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded automatically from the `.env` file.
    
    Contains credentials, model selections, database connection parameters,
    and local storage paths for videos and Chroma embeddings.
    """

    # LLM Provider & Model settings ('google' or 'openai')
    llm_provider: str
    llm_model_name: str
    llm_embedding_model: str
    google_api_key: str
    openai_api_key: str

    # Chroma Vector Database settings (local directory and collection partition)
    vector_db_dir_name: str
    vector_db_collection_name: str

    # Relational Database connection parameters (PostgreSQL / MySQL / etc.)
    database_connection: str
    database_host: str
    database_port: str
    database_user: str
    database_password: str
    database_name: str

    # Local disk directories for video processing and file logs
    # - video_temp_dir: holds short-lived subclips during range summaries
    # - video_org_dir: stores uploaded full-length source videos
    # - log_file_dir: directory where app.log is written
    video_temp_dir: str
    video_org_dir: str
    log_file_dir: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra environment variables not defined here so startup never crashes
        extra="ignore",
    )


# Singleton settings instance accessed across routers and services
settings = Settings()
