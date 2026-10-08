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
from services.vector_store import VectorStoreService
from services.llm import LLMService
from uuid import uuid4
from logger_app import setup_logger
from core.config import settings

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
    """Manages LangGraph nodes and execution pipeline for video analysis and RAG Q&A."""

    def __init__(self):
        self.__vector_service = VectorStoreService()
        self.__llm_service = LLMService()
        self.__logger = setup_logger(__name__)
        self.__graph = None

    def upload_video(self, state: MainState):
        """Read uploaded video file from disk into memory bytes."""
        path = state.get("video_path")
        if not path or not os.path.exists(path):
            raise FileNotFoundError("Video path not provided or invalid")

        mime_type, _ = mimetypes.guess_type(path)
        mime_type = mime_type or "video/mp4"

        with open(path, "rb") as f:
            video_bytes = f.read()

        return {"uploaded_file": {"mime_type": mime_type, "data": video_bytes}}

    def summarize_video(self, state: MainState):
        """Send video content to LLM for scene description and summary generation."""
        uploaded_file = state["uploaded_file"]
        prompt = """
            You are a video analysis expert.
            Provide a detailed and comprehensive description of this video. 
            Your response must be in a natural human-readable format describing 
            what happens in the video, including scenes, actions, objects, and emotions. 
            Do not include any meta phrases like 'Here is the summary' — start directly.
        """

        if "prompt" in state and state["prompt"] != "":
            prompt = f"You are a video analysis expert. {state['prompt']} Avoid adding introductory phrases like 'Here is the summary' or 'Okay, here’s the explanation'. Start directly with the summary content."

        encoded_video = base64.b64encode(uploaded_file["data"]).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "media" if settings.llm_provider != "openai" else "video",
                    "data": encoded_video,
                    "mime_type": uploaded_file["mime_type"],
                },
            ]
        )

        response = self.__llm_service.get_chat_model().invoke([message])
        return {"summary": response.content}

    def store_summary_in_db(self, state: MainState):
        """Chunk video summary text and store embeddings into Chroma vector database."""
        vector_db = self.__vector_service.vector_db()
        if state.get("is_new_video") and state["is_new_video"] is True:
            try:
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
        """Answer user questions via RAG using Chroma stored video summary embeddings."""
        question = state.get("question")
        video_name = state.get("video_name")
        messages = state.get("messages", [])

        vector_db = self.__vector_service.vector_db()
        search_kwargs = {"filter": {"source": video_name}}
        retriever = vector_db.as_retriever(search_kwargs=search_kwargs)

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
        """Route flow based on whether user is asking a question or processing a new video."""
        if state.get("question") and state["question"] != "":
            return "ask_question"
        return "upload_video"

    def build_pipeline(self):
        """Compile state graph pipeline with memory saver checkpointer."""
        if self.__graph is not None:
            return self.__graph

        pipeline = StateGraph(MainState)
        checkpointer = MEMORY_SAVER
        # Add nodes
        pipeline.add_node("upload_video", self.upload_video)
        pipeline.add_node("summarize_video", self.summarize_video)
        pipeline.add_node("store_summary_in_db", self.store_summary_in_db)
        pipeline.add_node("ask_question", self.ask_question)

        # Conditional edges
        pipeline.add_conditional_edges(
            START,
            self.conditional_node,
            {
                "ask_question": "ask_question",
                "upload_video": "upload_video",
            },
        )

        # Sequential edges
        pipeline.add_edge("upload_video", "summarize_video")
        pipeline.add_edge("summarize_video", "store_summary_in_db")
        pipeline.add_edge("store_summary_in_db", END)
        pipeline.add_edge("ask_question", END)

        self.__graph = pipeline.compile(checkpointer=checkpointer)
        return self.__graph
