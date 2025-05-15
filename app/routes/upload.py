from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List

from app.services.file_processor import FileProcessor
from app.services.vector_store import VectorStore
from app.utils.helpers import is_allowed_file

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = [
    ".pdf", ".docx", ".doc",  # Documents
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff",  # Images
    ".txt", ".md", ".html"  # Text files
]

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    store_type: str = Query("chroma", description="Vector store type: 'chroma' or 'faiss'"),
    file_processor: FileProcessor = Depends(lambda: FileProcessor()),
    vector_store: VectorStore = Depends(lambda: VectorStore(store_type=store_type))
):
    """Upload and process files using LangChain document loaders."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if store_type not in ["chroma", "faiss"]:
        raise HTTPException(status_code=400, detail="Invalid store_type. Must be 'chroma' or 'faiss'")

    results = []

    for file in files:
        filename = file.filename

        # Check if file has an allowed extension
        if not is_allowed_file(filename, ALLOWED_EXTENSIONS):
            results.append({
                "filename": filename,
                "status": "error",
                "message": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            })
            continue

        try:
            # Save the uploaded file
            file_path = await file_processor.save_uploaded_file(file, filename)

            # Process the file using LangChain document loaders
            chunks = file_processor.process_file(file_path)

            if not chunks:
                results.append({
                    "filename": filename,
                    "status": "error",
                    "message": "No text content could be extracted from the file"
                })
                continue

            # Add chunks to vector store (ChromaDB or FAISS)
            vector_store.add_documents(chunks)

            results.append({
                "filename": filename,
                "status": "success",
                "chunks_extracted": len(chunks),
                "message": f"File processed successfully. {len(chunks)} chunks extracted and stored in {store_type}."
            })

        except Exception as e:
            results.append({
                "filename": filename,
                "status": "error",
                "message": f"Error processing file: {str(e)}"
            })

    return JSONResponse(content={"results": results})
