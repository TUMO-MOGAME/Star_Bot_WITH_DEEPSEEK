from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.services.vector_store import VectorStore
from app.services.llm import LLMService
from app.config import TOP_K_RESULTS

router = APIRouter()

# Set up logging
logger = logging.getLogger("starbot.chat")
logging.basicConfig(level=logging.INFO)

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = TOP_K_RESULTS
    history: Optional[List[Dict[str, str]]] = []  # List of {"role": "user"|"bot", "content": str}
    school: Optional[str] = None  # For future use

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    vector_store: VectorStore = Depends(lambda: VectorStore(store_type="qdrant")),
    llm_service: LLMService = Depends(lambda: LLMService())
):
    """Chat with the Star College bot using LangChain."""
    try:
        logger.info(f"Received chat request: {request}")
        if not request.question:
            logger.warning("No question provided in request.")
            raise HTTPException(status_code=400, detail="No question provided")

        # Optionally use request.school for filtering in the future
        # Search for relevant documents using LangChain vector store
        results = vector_store.search(request.question, request.top_k)

        # Generate response using LangChain LLM, now with history
        answer = llm_service.generate_response(request.question, results, history=request.history)

        # Format sources for response
        sources = []
        for result in results:
            source = {
                "text": result.get("text", ""),
                "metadata": result.get("metadata", {}),
                "score": result.get("score", 0)
            }
            sources.append(source)

        logger.info("Chat response generated successfully.")
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return ChatResponse(
            answer=f"I'm sorry, there was an error processing your request. Please try again later.",
            sources=[]
        )
