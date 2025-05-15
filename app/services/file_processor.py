from pathlib import Path
from typing import List, Dict, Any

from langchain_community.document_loaders import (
    PyMuPDFLoader,
    Docx2txtLoader,
    UnstructuredImageLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import UPLOAD_FOLDER, PROCESSED_FOLDER, CHUNK_SIZE, CHUNK_OVERLAP
from app.utils.helpers import generate_unique_id

class FileProcessor:
    """Process different file types using LangChain document loaders."""

    def __init__(self):
        self.upload_folder = UPLOAD_FOLDER
        self.processed_folder = PROCESSED_FOLDER
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )

    async def save_uploaded_file(self, file, filename: str) -> Path:
        """Save an uploaded file to the upload folder."""
        file_path = self.upload_folder / filename

        # Create file content
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return file_path

    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a file based on its extension using LangChain document loaders."""
        extension = file_path.suffix.lower()

        try:
            # Select the appropriate loader based on file extension
            if extension == ".pdf":
                loader = PyMuPDFLoader(str(file_path))
                source_type = "pdf"
            elif extension in [".docx", ".doc"]:
                loader = Docx2txtLoader(str(file_path))
                source_type = "doc"
            elif extension in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                loader = UnstructuredImageLoader(str(file_path))
                source_type = "image"
            elif extension in [".txt", ".md", ".html"]:
                loader = TextLoader(str(file_path))
                source_type = "text"
            else:
                raise ValueError(f"Unsupported file type: {extension}")

            # Load documents
            documents = loader.load()

            # Split documents into chunks
            splits = self.text_splitter.split_documents(documents)

            # Convert to our format with metadata
            chunks_with_metadata = []
            for doc in splits:
                # Extract existing metadata
                metadata = doc.metadata.copy()

                # Add our custom metadata
                metadata["source_type"] = "file"
                metadata["file_type"] = source_type
                metadata["filename"] = file_path.name

                chunks_with_metadata.append({
                    "id": generate_unique_id(),
                    "text": doc.page_content,
                    "metadata": metadata
                })

            return chunks_with_metadata

        except Exception as e:
            print(f"Error processing file {file_path.name}: {str(e)}")
            return []
