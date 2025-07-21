from typing import List, Dict, Any, Literal
from pathlib import Path
import warnings

from langchain_chroma import Chroma

from app.config import CHROMA_INDEX_FOLDER, TOP_K_RESULTS
from app.services.embedding import EmbeddingService

warnings.filterwarnings("ignore", category=UserWarning)

class VectorStore:
    """Vector store for document retrieval using LangChain with ChromaDB."""

    def __init__(self, store_type: Literal["chroma"] = "chroma"):
        self.store_type = store_type
        self.index_folder: Path = Path(CHROMA_INDEX_FOLDER)
        self.embedding_service = EmbeddingService()
        self.vector_store = None

        # Ensure index folder exists
        self.index_folder.mkdir(parents=True, exist_ok=True)

        # Attempt to load existing index
        self._load_index()

    def _load_index(self) -> None:
        try:
            self.embedding_service.load_model()

            if self.index_folder.exists() and any(self.index_folder.iterdir()):
                self.vector_store = Chroma(
                    persist_directory=str(self.index_folder),
                    embedding_function=self.embedding_service.model,  # Pass embedding object here
                    collection_name="starbot"
                )
                print(f"Loaded ChromaDB index from {self.index_folder}")
            else:
                print(f"No existing ChromaDB index found at {self.index_folder}")

        except Exception as e:
            print(f"Error loading Chroma index: {e}")
            self.vector_store = None

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        if not documents:
            return

        self.embedding_service.load_model()

        langchain_docs = self.embedding_service.create_langchain_documents(documents)

        if self.vector_store is None:
            try:
                if self.embedding_service.model is None:
                    raise ValueError("Embedding model is not loaded")

                self.vector_store = Chroma.from_documents(
                    documents=langchain_docs,
                    embedding_function=self.embedding_service.model,  # Pass embedding object here
                    persist_directory=str(self.index_folder),
                    collection_name="starbot"
                )
                print(f"Created new ChromaDB index at {self.index_folder}")

            except Exception as e:
                print(f"Error creating ChromaDB index: {e}")
        else:
            self.vector_store.add_documents(langchain_docs)
            print(f"Added documents to existing ChromaDB index at {self.index_folder}")

        # Persistence is automatic; no manual persist needed

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        if self.vector_store is None:
            return []

        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)
            return [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                }
                for doc, score in docs_with_scores
            ]
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return []
