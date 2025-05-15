from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List

from app.services.web_scraper import WebScraper
from app.services.vector_store import VectorStore

router = APIRouter()

class ScrapeRequest(BaseModel):
    urls: List[HttpUrl]

@router.post("/scrape")
async def scrape_urls(
    request: ScrapeRequest,
    store_type: str = Query("chroma", description="Vector store type: 'chroma' or 'faiss'"),
    web_scraper: WebScraper = Depends(lambda: WebScraper()),
    vector_store: VectorStore = Depends(lambda: VectorStore(store_type=store_type))
):
    """Scrape and process URLs using LangChain WebBaseLoader."""
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if store_type not in ["chroma", "faiss"]:
        raise HTTPException(status_code=400, detail="Invalid store_type. Must be 'chroma' or 'faiss'")

    results = []

    for url in request.urls:
        url_str = str(url)

        try:
            # Scrape the URL using LangChain WebBaseLoader
            chunks = web_scraper.scrape_url(url_str)

            if not chunks:
                results.append({
                    "url": url_str,
                    "status": "error",
                    "message": "No content could be extracted from the URL"
                })
                continue

            # Add chunks to vector store (ChromaDB or FAISS)
            vector_store.add_documents(chunks)

            results.append({
                "url": url_str,
                "status": "success",
                "chunks_extracted": len(chunks),
                "message": f"URL processed successfully. {len(chunks)} chunks extracted and stored in {store_type}."
            })

        except Exception as e:
            results.append({
                "url": url_str,
                "status": "error",
                "message": f"Error processing URL: {str(e)}"
            })

    return JSONResponse(content={"results": results})
