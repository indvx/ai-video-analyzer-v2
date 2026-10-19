from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings


class LLMService:
    """Factory service that instantiates LLM chat models and embedding functions.
    
    Supports switching between Google Gemini and OpenAI simply by updating the 
    `LLM_PROVIDER` environment variable, avoiding provider vendor-lock across the app.
    """

    def __init__(self):
        # Resolve active provider and model identities from environment settings
        self.__provider = str(settings.llm_provider)
        self.__chat_model = str(settings.llm_model_name)
        self.__embedding_model = str(settings.llm_embedding_model)
        # Pick matching API key based on the chosen provider
        self.__api_key = (
            str(settings.openai_api_key)
            if self.__provider == "openai"
            else str(settings.google_api_key)
        )

    def gemini_chat_model(self):
        """Builds Google Gemini chat client.
        
        Temperature is set to 0 for deterministic, factual summaries and RAG answers.
        """
        return ChatGoogleGenerativeAI(
            model=self.__chat_model,
            temperature=0,
            max_output_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def gemini_embedding_model(self):
        """Builds Google Gemini embeddings client for vectorizing summaries and search queries."""
        return GoogleGenerativeAIEmbeddings(
            model=self.__embedding_model, api_key=self.__api_key
        )

    def openai_chat_model(self):
        """Builds OpenAI GPT chat client with deterministic zero-temperature settings."""
        return ChatOpenAI(
            model=self.__chat_model,
            temperature=0,
            api_key=self.__api_key,
            verbose=True,
        )

    def openai_embedding_model(self):
        """Builds OpenAI embeddings client for text vectorization."""
        return OpenAIEmbeddings(model=self.__embedding_model, api_key=self.__api_key)

    def get_chat_model(self):
        """Returns the active chat model based on the configured `LLM_PROVIDER`."""
        if self.__provider == "openai":
            return self.openai_chat_model()
        return self.gemini_chat_model()

    def get_embedding_model(self):
        """Returns the active embedding model based on the configured `LLM_PROVIDER`."""
        if self.__provider == "openai":
            return self.openai_embedding_model()
        return self.gemini_embedding_model()
