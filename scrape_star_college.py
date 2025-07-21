import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

LINKS_FILE = os.getenv("LINKS_FILE", "data/links/links.txt")
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")
CHROMA_INDEX_FOLDER = os.getenv("CHROMA_INDEX_FOLDER", "data/chroma_index")

Path("data/links").mkdir(parents=True, exist_ok=True)
Path(PROCESSED_FOLDER).mkdir(parents=True, exist_ok=True)
Path(CHROMA_INDEX_FOLDER).mkdir(parents=True, exist_ok=True)

from app.services.web_scraper import WebScraper
from app.services.vector_store import VectorStore

def read_urls_from_file(file_path):
    try:
        with open(file_path, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except Exception as e:
        print(f"Error reading URLs from {file_path}: {str(e)}")
        return []

async def main():
    web_scraper = WebScraper()

    store_type = os.getenv("VECTOR_STORE_TYPE", "chroma")
    vector_store = VectorStore(store_type=store_type)

    urls = read_urls_from_file(LINKS_FILE)
    if not urls:
        print(f"No URLs found in {LINKS_FILE}. Please add URLs.")
        return

    print(f"Starting to scrape {len(urls)} websites...")

    all_chunks = []
    for url in urls:
        print(f"Scraping: {url}")
        try:
            chunks = await web_scraper.scrape_url_async(url)
            if not chunks:
                print(f"No content extracted from {url}")
                continue
            all_chunks.extend(chunks)
            print(f"Successfully processed: {url}")
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")

    if not all_chunks:
        print("No content extracted from any URL.")
        return

    processed_dir = Path(PROCESSED_FOLDER)
    web_data_path = processed_dir / "web_data.json"
    with open(web_data_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_chunks)} chunks to {web_data_path}")

    vector_store.add_documents(all_chunks)
    print(f"Added {len(all_chunks)} chunks to {store_type} vector store.")

    print("Web scraping completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
