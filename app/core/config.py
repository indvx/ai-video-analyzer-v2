from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment variables configuration."""

    # LLM Config
    llm_provider: str
    llm_model_name: str
    llm_embedding_model: str
    google_api_key: str
    openai_api_key: str

    # Vector DB Config
    vector_db_dir_name: str
    vector_db_collection_name: str

    # Database Config
    database_connection: str
    database_host: str
    database_port: str
    database_user: str
    database_password: str
    database_name: str

    # Directories Config
    video_temp_dir: str
    video_org_dir: str
    log_file_dir: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
