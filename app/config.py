import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# API Keys
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Model Settings
# Use a simpler embedding model to avoid PyTorch compatibility issues
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-ai/deepseek-coder-7b-instruct")

# Application Settings
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "data/uploads")
PROCESSED_FOLDER = BASE_DIR / os.getenv("PROCESSED_FOLDER", "data/processed")
CHROMA_INDEX_FOLDER = BASE_DIR / os.getenv("CHROMA_INDEX_FOLDER", "data/chroma_index")

# Vector Store Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma")

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
CHROMA_INDEX_FOLDER.mkdir(parents=True, exist_ok=True)
