# process_uploads.py
"""
Process all files in data/uploads/ and save the processed data to the processed/ folder.
Run this script before using answer_question.py to ensure all uploaded data is processed.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from app.services.file_processor import FileProcessor
from app.services.vector_store import VectorStore

# Load environment variables
load_dotenv()

# Get folder paths from environment variables
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "data/uploads")
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")

def main():
    print("Processing all files in 'data/uploads/'...")

    # Initialize file processor
    file_processor = FileProcessor()

    # Initialize vector store for embedding and storage
    store_type = os.getenv("VECTOR_STORE_TYPE", "chroma")
    vector_store = VectorStore(store_type=store_type)

    # Prepare paths
    upload_dir = Path(UPLOAD_FOLDER)
    processed_dir = Path(PROCESSED_FOLDER)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Get all files from uploads directory
    files = list(upload_dir.glob("*"))
    if not files:
        print("No files found in uploads directory.")
        return

    # Process each file
    all_docs = []
    for file_path in files:
        print(f"Processing: {file_path.name}")
        chunks = file_processor.process_file(file_path)
        if not chunks:
            print(f"  No text extracted from {file_path.name}.")
            continue
        all_docs.extend(chunks)

    # Save processed data to processed folder
    uploads_data_path = processed_dir / "uploads_data.json"
    with open(uploads_data_path, 'w', encoding='utf-8') as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)
    print(f"Saved processed data to {uploads_data_path}")

    # Add documents to vector store for retrieval
    vector_store.add_documents(all_docs)
    print(f"Processed {len(all_docs)} documents and added to {store_type} vector store.")
    print("All uploads processed and indexed.")

if __name__ == "__main__":
    main()
