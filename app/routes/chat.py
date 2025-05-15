from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.vector_store import VectorStore
from app.services.llm import LLMService
from app.config import TOP_K_RESULTS

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = TOP_K_RESULTS
    history: Optional[List[Dict[str, str]]] = []  # List of {"role": "user"|"bot", "content": str}

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    vector_store: VectorStore = Depends(lambda: VectorStore(store_type="chroma")),
    llm_service: LLMService = Depends(lambda: LLMService())
):
    """Chat with the Star College bot using LangChain."""
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="No question provided")

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

        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            answer=f"I'm sorry, there was an error processing your request. Please try again later.",
            sources=[]
        )
