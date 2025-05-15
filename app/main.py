from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routes import upload, scrape, chat
from app.config import HOST, PORT, DEBUG

# Create FastAPI app
app = FastAPI(
    title="Star College Chatbot",
    description="A chatbot for Star College in Durban that answers questions based on uploaded information using LangChain, ChromaDB, and FAISS.",
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
app.mount("/images", StaticFiles(directory="images"), name="images")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(scrape.router, tags=["Scrape"])
app.include_router(chat.router, tags=["Chat"])

# Route for root to serve the custom index.html from the project root
@app.get("/", response_class=HTMLResponse)
async def custom_index():
    with open(os.path.join(os.path.dirname(__file__), "..", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/upload-page", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Render the upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
