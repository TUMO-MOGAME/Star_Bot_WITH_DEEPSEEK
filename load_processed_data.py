"""
Load processed data from uploads_data.json and web_data.json into the vector store.
This script ensures that only the processed data is used by the chatbot.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get folder paths from environment variables
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")
CHROMA_INDEX_FOLDER = os.getenv("CHROMA_INDEX_FOLDER", "data/chroma_index")

# Import our services
from app.services.vector_store import VectorStore

def load_json_file(file_path):
    """Load data from a JSON file."""
    try:
        print(f"Checking for file: {file_path}")
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return []

        print(f"Opening file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Loaded {len(data)} documents from {file_path}")
        # Print the first document as a sample
        if data and len(data) > 0:
            print(f"Sample document: {data[0]['text'][:100]}...")
        return data
    except Exception as e:
        print(f"Error loading data from {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("Loading processed data into vector store...")

    # Initialize vector store
    store_type = os.getenv("VECTOR_STORE_TYPE", "chroma")
    print(f"Using vector store type: {store_type}")

    # Clear existing vector store
    chroma_dir = Path(CHROMA_INDEX_FOLDER)
    print(f"Checking for existing vector store at: {chroma_dir}")
    if chroma_dir.exists():
        import shutil
        print(f"Clearing existing vector store at {chroma_dir}...")
        shutil.rmtree(chroma_dir)

    # Create fresh vector store
    print(f"Creating directory: {chroma_dir}")
    chroma_dir.mkdir(parents=True, exist_ok=True)
    print("Initializing vector store...")
    vector_store = VectorStore(store_type=store_type)

    # Load data from processed files
    processed_dir = Path(PROCESSED_FOLDER)
    print(f"Processed directory: {processed_dir}")
    uploads_data_path = processed_dir / "uploads_data.json"
    web_data_path = processed_dir / "web_data.json"

    print("\n--- Loading uploads data ---")
    # Load uploads data
    uploads_data = load_json_file(uploads_data_path)

    print("\n--- Loading web data ---")
    # Load web data
    web_data = load_json_file(web_data_path)

    # Combine all data
    all_data = uploads_data + web_data
    print(f"\nTotal documents: {len(all_data)}")

    if not all_data:
        print("No processed data found. Please run process_uploads.py and scrape_star_college.py first.")
        return

    # Add documents to vector store
    print(f"\nAdding {len(all_data)} documents to vector store...")
    try:
        vector_store.add_documents(all_data)
        print("Documents added successfully!")
    except Exception as e:
        print(f"Error adding documents to vector store: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print("\nProcessed data loaded successfully into vector store!")
    print(f"The chatbot will now use only the data from:")
    print(f"1. {uploads_data_path}")
    print(f"2. {web_data_path}")

if __name__ == "__main__":
    main()
