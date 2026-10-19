from langchain_chroma import Chroma
from app.services.ai_service.llm import LLMService
from app.core.config import settings
import os


class VectorStoreService:
    """Manages the local Chroma vector database instance used for RAG semantic search.
    
    Stores summary chunks as embedded vectors tagged with `source: <video_name>`,
    allowing Q&A lookups to isolate chunks relevant to a specific video.
    """

    def __init__(self):
        # Embedding function aligns with the active LLM provider (OpenAI or Gemini)
        self.__embedding = LLMService().get_embedding_model()
        self.__persist_directory = settings.vector_db_dir_name
        self.__collection_name = settings.vector_db_collection_name

    def vector_db(self):
        """Initializes or connects to the existing Chroma vector store persisted on disk."""
        return Chroma(
            collection_name=self.__collection_name,
            embedding_function=self.__embedding,
            persist_directory=self.__persist_directory,
        )

    def _delete_documents(self, file_name: str):
        """Purges all chunk embeddings tagged with `source: file_name`.
        
        Called when a video is deleted so orphan vector chunks don't pollute future search results.
        """
        vector_store = self.vector_db()
        try:
            vector_store.delete(where={"source": file_name})
        except Exception as e:
            # Non-fatal if the collection didn't have entries for this video yet
            print(f"Error deleting documents for {file_name}: {e}")
        return True

    def get_documents(self):
        """Helper to access the underlying vector store for debugging or inspection."""
        vector_store = self.vector_db()
        return True
