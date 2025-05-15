import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure data directories exist
Path("data/uploads").mkdir(parents=True, exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)
Path("data/faiss_index").mkdir(parents=True, exist_ok=True)

# Import our services
from app.services.web_scraper import WebScraper
from app.services.vector_store import VectorStore

# Star College websites to scrape
STAR_COLLEGE_URLS = [
    "https://starboyshigh.co.za/",
    "https://starboyshigh.co.za/our-history/",
    "https://starboyshigh.co.za/principals-message/",
    "https://starboyshigh.co.za/enrollment/",
    "https://starboyshigh.co.za/fees/",
    "https://starboyshigh.co.za/high-school/",
    "https://starboyshigh.co.za/scholarship-policy/",
    "https://starboyshigh.co.za/uniform-and-dress-code/",
    "https://starcollegedurban.ed-space.net/onlineapplication.cfm",
    "https://starboyshigh.co.za/boarding/",
    "https://starboyshigh.co.za/contact-us/",
    "https://starboyshigh.co.za/activities/"
]

async def main():
    # Initialize services
    web_scraper = WebScraper()
    
    # Initialize only ChromaDB vector store
    chroma_store = VectorStore(store_type="chroma")
    
    print("Starting to scrape Star College websites...")
    
    # Process each URL
    for url in STAR_COLLEGE_URLS:
        print(f"Scraping: {url}")
        try:
            # Scrape the URL
            chunks = web_scraper.scrape_url(url)
            
            if not chunks:
                print(f"No content could be extracted from: {url}")
                continue
            
            # Add chunks to ChromaDB only
            print(f"Adding {len(chunks)} chunks to ChromaDB...")
            chroma_store.add_documents(chunks)
            
            print(f"Successfully processed: {url}")
        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
    
    print("Scraping completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
