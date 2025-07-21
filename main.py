import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Import from app module
from app.routes import upload, scrape, chat

# Create FastAPI app
app = FastAPI(
    title="Star College Chatbot",
    description="A chatbot for Star College in Durban that answers questions based on uploaded information using LangChain, ChromaDB, and DeepSeek AI.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Route for root to serve the custom index.html
@app.get("/", response_class=HTMLResponse)
async def custom_index():
    try:
        with open("index.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Star College Chatbot</h1><p>Welcome to the Star College Chatbot!</p>")

@app.get("/upload-page", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Render the upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Star College Chatbot is running"}

# For Vercel
def handler(request):
    return app
