from typing import List, Dict, Any

from langchain_huggingface import HuggingFaceEmbeddings  # Updated import as per deprecation warning
from langchain_core.documents import Document

from app.config import EMBEDDING_MODEL

class EmbeddingService:
    """Service for creating text embeddings using LangChain."""

    def __init__(self):
        self.model = None
        self.model_name = EMBEDDING_MODEL

    def load_model(self):
        """Load the embedding model using LangChain HuggingFaceEmbeddings."""
        if self.model is None:
            print(f"Loading embedding model: {self.model_name}")
            self.model = HuggingFaceEmbeddings(model_name=self.model_name)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        self.load_model()

        # Create embeddings using LangChain
        embeddings = self.model.embed_documents(texts)
        return embeddings

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        self.load_model()

        # Create embedding using LangChain
        embedding = self.model.embed_query(text)
        return embedding

    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Embed a list of document chunks."""
        if not documents:
            return []

        # Extract text from documents
        texts = [doc["text"] for doc in documents]

        # Get embeddings
        embeddings = self.get_embeddings(texts)

        # Add embeddings to documents
        for i, doc in enumerate(documents):
            doc["embedding"] = embeddings[i]

        return documents

    def create_langchain_documents(self, documents: List[Dict[str, Any]]) -> List[Document]:
        """Convert our document format to LangChain Document format."""
        langchain_docs = []

        for doc in documents:
            langchain_docs.append(
                Document(
                    page_content=doc["text"],
                    metadata=doc["metadata"]
                )
            )

        return langchain_docs
