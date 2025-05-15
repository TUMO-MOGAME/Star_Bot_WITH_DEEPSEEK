# process_uploads.py
"""
Process all files in data/uploads/ and add their content to the ChromaDB vector store.
Run this script before using answer_question.py to ensure all uploaded data is indexed.
"""
import os
from pathlib import Path
from app.services.file_processor import FileProcessor
from app.services.vector_store import VectorStore
from app.config import UPLOAD_FOLDER

def main():
    print("Processing all files in 'data/uploads/'...")
    file_processor = FileProcessor()
    vector_store = VectorStore(store_type="chroma")
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
        vector_store.add_documents(chunks)
        print(f"  Added {len(chunks)} chunks from {file_path.name} to vector store.")
    print("All uploads processed and indexed.")

if __name__ == "__main__":
    main()
