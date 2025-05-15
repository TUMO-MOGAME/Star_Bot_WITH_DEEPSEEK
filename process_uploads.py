# process_uploads.py
"""
Process all files in data/uploads/ and add their content to the vector store.
Run this script before using answer_question.py to ensure all uploaded data is indexed.
"""
import os
from pathlib import Path
from app.services.file_processor import FileProcessor
from app.services.vector_store import VectorStore
from app.config import UPLOAD_FOLDER

def main():
    print("Processing all files in 'data/uploads/'...")
    # Choose store_type: 'qdrant', 'chroma', or 'faiss'
    store_type = os.getenv("VECTOR_STORE_TYPE", "qdrant")
    vector_store = VectorStore(store_type=store_type)
    file_processor = FileProcessor()
    all_docs = []
    upload_dir = Path(UPLOAD_FOLDER)
    files = list(upload_dir.glob("*"))
    if not files:
        print("No files found in uploads directory.")
        return
    for file_path in files:
        print(f"Processing: {file_path.name}")
        chunks = file_processor.process_file(file_path)
        if not chunks:
            print(f"  No text extracted from {file_path.name}.")
            continue
        all_docs.extend(chunks)
    vector_store.add_documents(all_docs)
    print(f"Processed {len(all_docs)} documents and added to {store_type} vector store.")
    print("All uploads processed and indexed.")

if __name__ == "__main__":
    main()
