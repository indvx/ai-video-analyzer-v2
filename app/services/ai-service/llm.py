from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from core.config import settings


class LLMService:
    """Provides LLM chat and embedding model instances based on the configured provider (OpenAI or Google Gemini)."""

    def __init__(self):
        self.__provider = str(settings.llm_provider)
        self.__chat_model = str(settings.llm_model_name)
        self.__embedding_model = str(settings.llm_embedding_model)

    def gemini_chat_model(self):
        """Initialize and return the Google Gemini chat model."""
        return ChatGoogleGenerativeAI(
            model=self.__chat_model,
            temperature=0,
            max_output_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def gemini_embedding_model(self):
        """Initialize and return Google Gemini embeddings."""
        return GoogleGenerativeAIEmbeddings(model=self.__embedding_model)

    def openai_chat_model(self):
        """Initialize and return the OpenAI GPT chat model."""
        return ChatOpenAI(model=self.__chat_model, temperature=0, verbose=True)

    def openai_embedding_model(self):
        """Initialize and return OpenAI embeddings."""
        return OpenAIEmbeddings(model=self.__embedding_model)

    def get_chat_model(self):
        """Return the active chat model instance based on configuration."""
        if self.__provider == "openai":
            return self.openai_chat_model()
        return self.gemini_chat_model()

    def get_embedding_model(self):
        """Return the active embedding model instance based on configuration."""
        if self.__provider == "openai":
            return self.openai_embedding_model()
        return self.gemini_embedding_model()
