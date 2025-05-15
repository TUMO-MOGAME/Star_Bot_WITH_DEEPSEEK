from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from app.services.vector_store import VectorStore
from app.services.llm import LLMService

app = FastAPI(
    title="Star College Chatbot",
    description="A chatbot for Star College in Durban that answers questions based on uploaded information.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(
    request: ChatRequest,
    store_type: str = Query("chroma", description="Vector store type: 'chroma' or 'faiss'")
):
    """Chat with the Star College bot."""
    try:
        # Initialize services
        vector_store = VectorStore(store_type=store_type)
        llm_service = LLMService()

        # Search for relevant documents
        results = vector_store.search(request.question, request.top_k)

        # Generate response
        answer = llm_service.generate_response(request.question, results)

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
        import traceback
        traceback.print_exc()
        return ChatResponse(
            answer=f"Error: {str(e)}",
            sources=[]
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082)
