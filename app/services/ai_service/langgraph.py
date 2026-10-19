from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Optional, Annotated
from langgraph.graph import StateGraph, START, END
import os
import mimetypes
import base64
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.ai_service.vector_store import VectorStoreService
from app.services.ai_service.llm import LLMService
from uuid import uuid4
from logger_app import setup_logger
from app.core.config import settings

# Persistent in-memory checkpointer for thread memory across invocations
MEMORY_SAVER = MemorySaver()


class UploadedFile(TypedDict):
    """Uploaded video metadata and binary payload."""

    mime_type: str
    data: bytes


class MainState(TypedDict):
    """Shared state for the video processing and Q&A LangGraph workflow."""

    video_path: Optional[str]
    video_name: str
    uploaded_file: Optional[UploadedFile]
    summary: Optional[str]
    is_new_video: bool
    prompt: Optional[str]
    question: Optional[str]
    answer: Optional[str]
    messages: Annotated[list[AnyMessage], add_messages]


class LanggraphService:
    """Manages the LangGraph state machine for video processing, summarization, and RAG Q&A."""

    def __init__(self):
        self.__vector_service = VectorStoreService()
        self.__llm_service = LLMService()
        self.__logger = setup_logger(__name__)
        self.__graph = None

    def upload_video(self, state: MainState):
        """Reads the video file from disk into memory bytes and detects its MIME type for multimodal LLM consumption."""
        path = state.get("video_path")
        if not path or not os.path.exists(path):
            raise FileNotFoundError("Video path not provided or invalid")

        # Fall back to video/mp4 if file extension doesn't match standard registry
        mime_type, _ = mimetypes.guess_type(path)
        mime_type = mime_type or "video/mp4"

        with open(path, "rb") as f:
            video_bytes = f.read()

        return {"uploaded_file": {"mime_type": mime_type, "data": video_bytes}}

    def summarize_video(self, state: MainState):
        """Encodes video bytes into base64 and prompts the multimodal LLM to describe scenes, actions, and tone."""
        uploaded_file = state["uploaded_file"]
        
        # Default prompt instructs the model to produce a thorough description without robotic meta-intros
        prompt = """
            You are a video analysis expert.
            Provide a detailed and comprehensive description of this video. 
            Your response must be in a natural human-readable format describing 
            what happens in the video, including scenes, actions, objects, and emotions. 
            Do not include any meta phrases like 'Here is the summary' — start directly.
        """

        # If user supplied custom constraints (duration, bullet points, content rating), append them
        if "prompt" in state and state["prompt"] != "":
            prompt = f"You are a video analysis expert. {state['prompt']} Avoid adding introductory phrases like 'Here is the summary' or 'Okay, here’s the explanation'. Start directly with the summary content."

        # Multimodal models expect base64 payload in the message content block
        encoded_video = base64.b64encode(uploaded_file["data"]).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    # Gemini expects 'media' while OpenAI expects 'video' block type
                    "type": "media" if settings.llm_provider != "openai" else "video",
                    "data": encoded_video,
                    "mime_type": uploaded_file["mime_type"],
                },
            ]
        )

        response = self.__llm_service.get_chat_model().invoke([message])
        return {"summary": response.content}

    def store_summary_in_db(self, state: MainState):
        """Splits the newly generated summary into chunks and saves them in Chroma for chat Q&A."""
        vector_db = self.__vector_service.vector_db()

        # Only index into Chroma if this is an initial upload.
        # For repeat queries or custom re-summaries, we don't want duplicate chunks in the vector store.
        if state.get("is_new_video") and state["is_new_video"] is True:
            try:
                # Keep chunks short (~200 chars) with slight overlap so small question lookups match specific facts
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=200,
                    chunk_overlap=50,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""],
                )

                chunks = text_splitter.split_text(state["summary"])
                documents = []
                if chunks and len(chunks) > 0:
                    for chunk in chunks:
                        # Tag every chunk with the video name so RAG queries can isolate this specific video
                        documents.append(
                            Document(
                                page_content=chunk,
                                metadata={"source": state["video_name"]},
                            )
                        )
                if len(documents) > 0:
                    uuids = [str(uuid4()) for _ in range(len(documents))]
                    vector_db.add_documents(documents=documents, ids=uuids)
                return {}
            except Exception as e:
                self.__logger.error(f"Error saving summary: {e}")
        return {}

    def ask_question(self, state: MainState):
        """Answers user questions via RAG using Chroma embeddings filtered to the current video."""
        question = state.get("question")
        video_name = state.get("video_name")
        messages = state.get("messages", [])

        # Isolate semantic search strictly to chunks belonging to this specific video
        vector_db = self.__vector_service.vector_db()
        search_kwargs = {"filter": {"source": video_name}}
        retriever = vector_db.as_retriever(search_kwargs=search_kwargs)

        # Feed previous chat messages so multi-turn follow-up questions understand context
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant. Answer only using conversation history and provided video context. "
                    "If the question is about previous conversation, use the chat history. "
                    "If the question is about the video, use the context below.\n\n"
                    "Video Context:\n{context}",
                ),
                *messages,
                ("human", "{input}"),
            ]
        )

        combine_docs_chain = create_stuff_documents_chain(
            self.__llm_service.get_chat_model(), prompt
        )
        retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
        result = retrieval_chain.invoke({"input": question})

        return {
            "answer": result["answer"],
            "messages": [
                HumanMessage(content=question),
                AIMessage(content=result["answer"]),
            ],
        }

    def conditional_node(self, state: MainState) -> str:
        """Determines workflow branch: routes directly to Q&A if a question is provided, or video processing otherwise."""
        if state.get("question") and state["question"] != "":
            return "ask_question"
        return "upload_video"

    def build_pipeline(self):
        """Constructs and compiles the StateGraph workflow with persistent memory checkpointing."""
        # Return existing compiled graph if already initialized
        if self.__graph is not None:
            return self.__graph

        pipeline = StateGraph(MainState)
        checkpointer = MEMORY_SAVER
        
        # Register workflow task nodes
        pipeline.add_node("upload_video", self.upload_video)
        pipeline.add_node("summarize_video", self.summarize_video)
        pipeline.add_node("store_summary_in_db", self.store_summary_in_db)
        pipeline.add_node("ask_question", self.ask_question)

        # Entrypoint decision: branch to Q&A or start video upload sequence
        pipeline.add_conditional_edges(
            START,
            self.conditional_node,
            {
                "ask_question": "ask_question",
                "upload_video": "upload_video",
            },
        )

        # Video ingestion pipeline: read disk -> call LLM -> store chunks in vector DB -> finish
        pipeline.add_edge("upload_video", "summarize_video")
        pipeline.add_edge("summarize_video", "store_summary_in_db")
        pipeline.add_edge("store_summary_in_db", END)
        
        # Q&A pipeline: ask question -> finish
        pipeline.add_edge("ask_question", END)

        self.__graph = pipeline.compile(checkpointer=checkpointer)
        return self.__graph
