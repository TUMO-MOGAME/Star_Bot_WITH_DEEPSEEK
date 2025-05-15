from typing import List, Dict, Any, Literal

from langchain_community.vectorstores import Chroma, FAISS

from app.config import FAISS_INDEX_FOLDER, TOP_K_RESULTS
from app.services.embedding import EmbeddingService

class VectorStore:
    """Vector store for document retrieval using LangChain with ChromaDB and FAISS."""

    def __init__(self, store_type: Literal["chroma", "faiss"] = "chroma"):
        self.store_type = store_type
        self.index_folder = FAISS_INDEX_FOLDER
        self.embedding_service = EmbeddingService()
        self.vector_store = None

        # Create index folder if it doesn't exist
        self.index_folder.mkdir(parents=True, exist_ok=True)

        # Load existing index if available
        self._load_index()

    def _load_index(self) -> None:
        """Load the vector store if it exists."""
        try:
            # Load the embedding model
            self.embedding_service.load_model()

            # Check if the index exists
            if self.store_type == "chroma":
                chroma_path = self.index_folder / "chroma"
                if chroma_path.exists():
                    self.vector_store = Chroma(
                        persist_directory=str(chroma_path),
                        embedding_function=self.embedding_service.model
                    )
                    print(f"Loaded ChromaDB index from {chroma_path}")
            else:  # faiss
                faiss_path = self.index_folder / "faiss"
                if faiss_path.exists():
                    self.vector_store = FAISS.load_local(
                        folder_path=str(faiss_path),
                        embeddings=self.embedding_service.model
                    )
                    print(f"Loaded FAISS index from {faiss_path}")
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            self.vector_store = None

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store."""
        if not documents:
            return

        # Convert to LangChain Document format
        langchain_docs = self.embedding_service.create_langchain_documents(documents)

        # Create or update the vector store
        if self.vector_store is None:
            # Create a new vector store
            if self.store_type == "chroma":
                chroma_path = self.index_folder / "chroma"
                self.vector_store = Chroma.from_documents(
                    documents=langchain_docs,
                    embedding=self.embedding_service.model,
                    persist_directory=str(chroma_path)
                )
                self.vector_store.persist()
                print(f"Created new ChromaDB index at {chroma_path}")
            else:  # faiss
                self.vector_store = FAISS.from_documents(
                    documents=langchain_docs,
                    embedding=self.embedding_service.model
                )
                # Save the FAISS index
                faiss_path = self.index_folder / "faiss"
                self.vector_store.save_local(str(faiss_path))
                print(f"Created new FAISS index at {faiss_path}")
        else:
            # Add to existing vector store
            self.vector_store.add_documents(langchain_docs)

            # Persist if using ChromaDB
            if self.store_type == "chroma":
                self.vector_store.persist()
            elif self.store_type == "faiss":
                # Save the FAISS index
                faiss_path = self.index_folder / "faiss"
                self.vector_store.save_local(str(faiss_path))

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """Search for documents similar to the query."""
        if self.vector_store is None:
            return []

        try:
            # Search the vector store
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=top_k)

            # Format results
            results = []
            for doc, score in docs_with_scores:
                result = {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)  # Ensure score is a float for JSON serialization
                }
                results.append(result)

            return results
        except Exception as e:
            print(f"Error searching vector store: {str(e)}")
            return []
