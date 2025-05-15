from typing import List, Dict, Any
from urllib.parse import urlparse

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.utils.helpers import generate_unique_id

class WebScraper:
    """Scrape and process web content using LangChain."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )

    def scrape_url(self, url: str) -> List[Dict[str, Any]]:
        """Scrape content from a URL using LangChain WebBaseLoader."""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # Use LangChain WebBaseLoader
            loader = WebBaseLoader(url)
            documents = loader.load()

            # Extract title from metadata if available
            title = "Unknown Title"
            if documents and hasattr(documents[0], "metadata") and "title" in documents[0].metadata:
                title = documents[0].metadata["title"]

            # Split documents into chunks
            splits = self.text_splitter.split_documents(documents)

            # Create chunks with metadata
            chunks_with_metadata = []
            for doc in splits:
                # Extract existing metadata
                metadata = doc.metadata.copy() if hasattr(doc, "metadata") else {}

                # Add our custom metadata
                metadata["source_type"] = "web"
                metadata["url"] = url
                if "title" not in metadata:
                    metadata["title"] = title

                chunks_with_metadata.append({
                    "id": generate_unique_id(),
                    "text": doc.page_content,
                    "metadata": metadata
                })

            return chunks_with_metadata

        except Exception as e:
            print(f"Error scraping URL {url}: {str(e)}")
            return []
