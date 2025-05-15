import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path
sys.path.append(os.getcwd())

# Import our services
from app.services.vector_store import VectorStore
from app.services.llm import LLMService

def main():
    try:
        print("Initializing vector store...")
        vector_store = VectorStore(store_type="chroma")
        
        print("Initializing LLM service...")
        llm_service = LLMService()
        
        # Test question
        question = "What is the history of Star College?"
        print(f"Searching for: {question}")
        
        # Search for relevant documents
        results = vector_store.search(question, 5)
        print(f"Found {len(results)} results")
        
        # Print the results
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"Text: {result.get('text', '')[:100]}...")
            print(f"Score: {result.get('score', 0)}")
            print(f"Metadata: {result.get('metadata', {})}")
            print()
        
        # Generate response
        print("Generating response...")
        answer = llm_service.generate_response(question, results)
        
        print("\nFinal Answer:")
        print(answer)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
