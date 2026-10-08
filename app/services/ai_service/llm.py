from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings


class LLMService:
    """Provides LLM chat and embedding model instances based on the configured provider (OpenAI or Google Gemini)."""

    def __init__(self):
        self.__provider = str(settings.llm_provider)
        self.__chat_model = str(settings.llm_model_name)
        self.__embedding_model = str(settings.llm_embedding_model)
        self.__api_key = (
            str(settings.openai_api_key)
            if self.__provider == "openai"
            else str(settings.google_api_key)
        )

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
        return GoogleGenerativeAIEmbeddings(
            model=self.__embedding_model, api_key=self.__api_key
        )

    def openai_chat_model(self):
        """Initialize and return the OpenAI GPT chat model."""
        return ChatOpenAI(
            model=self.__chat_model,
            temperature=0,
            api_key=self.__api_key,
            verbose=True,
        )

    def openai_embedding_model(self):
        """Initialize and return OpenAI embeddings."""
        return OpenAIEmbeddings(model=self.__embedding_model, api_key=self.__api_key)

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
