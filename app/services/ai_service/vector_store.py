from langchain_chroma import Chroma
from app.services.ai_service.llm import LLMService
from app.core.config import settings
import os


class VectorStoreService:
    """Manages the Chroma vector database for video summary embeddings."""

    def __init__(self):
        self.__embedding = LLMService().get_embedding_model()
        self.__persist_directory = settings.vector_db_dir_name
        self.__collection_name = settings.vector_db_collection_name

    def vector_db(self):
        """Get the Chroma vector store instance."""
        return Chroma(
            collection_name=self.__collection_name,
            embedding_function=self.__embedding,
            persist_directory=self.__persist_directory,
        )

    def _delete_documents(self, file_name: str):
        """Delete stored embeddings associated with a specific video file."""
        vector_store = self.vector_db()
        try:
            vector_store.delete(where={"source": file_name})
        except Exception as e:
            print(f"Error deleting documents for {file_name}: {e}")
        return True

    def get_documents(self):
        """Retrieve stored document embeddings."""
        vector_store = self.vector_db()
        return True
