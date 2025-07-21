"""
Run the Star College Chatbot with processed data.
This script ensures that the chatbot uses only the processed data from uploads_data.json and web_data.json.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import colorama
from app.services.llm import LLMService
from app.config import TOP_K_RESULTS

# Initialize colorama for colored terminal output
colorama.init()

# Load environment variables
load_dotenv()

# Get folder paths from environment variables
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")

def load_processed_data():
    """Load data from processed files."""
    all_data = []
    processed_dir = Path(PROCESSED_FOLDER)
    
    # Load uploads data
    uploads_data_path = processed_dir / "uploads_data.json"
    if uploads_data_path.exists():
        try:
            with open(uploads_data_path, 'r', encoding='utf-8') as f:
                uploads_data = json.load(f)
                print(f"Loaded {len(uploads_data)} documents from {uploads_data_path}")
                all_data.extend(uploads_data)
        except Exception as e:
            print(f"Error loading uploads data: {str(e)}")
    
    # Load web data
    web_data_path = processed_dir / "web_data.json"
    if web_data_path.exists():
        try:
            with open(web_data_path, 'r', encoding='utf-8') as f:
                web_data = json.load(f)
                print(f"Loaded {len(web_data)} documents from {web_data_path}")
                all_data.extend(web_data)
        except Exception as e:
            print(f"Error loading web data: {str(e)}")
    
    print(f"Total processed documents loaded: {len(all_data)}")
    return all_data

def check_deepseek_api_key():
    """Check if DeepSeek API key is set."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment variables.")
        return False
    
    print("DeepSeek API key found. Will use DeepSeek API for generation.")
    return True

def main():
    # Check if DeepSeek API key is set
    if not check_deepseek_api_key():
        return

    print("Star College Chatbot - Using Processed Data - Type 'exit' to quit.\n")
    
    # Initialize LLM service with DeepSeek
    llm_service = LLMService()
    
    # Load processed data
    processed_data = load_processed_data()
    
    if not processed_data:
        print("No processed data found. Please run refresh_data.bat first.")
        return
    
    print("\nChatbot is ready! Ask a question about Star College.\n")
    
    # Keep track of conversation history
    history = []
    
    # Main chat loop
    while True:
        try:
            # Get user question
            question = input(f"{colorama.Fore.CYAN}You: {colorama.Style.RESET_ALL}").strip()
                
            # Check for exit command
            if not question or question.lower() in {"exit", "quit"}:
                print("Exiting Star College Chatbot.")
                break
                
            print(f"Question: {colorama.Fore.YELLOW}{question}{colorama.Style.RESET_ALL}")
            
            # Use processed data directly
            print("Searching in processed data...")
            
            # Simple keyword matching
            query_terms = question.lower().split()
            matched_results = []
            
            for doc in processed_data:
                text = doc.get("text", "").lower()
                # Count how many query terms appear in the text
                matches = sum(1 for term in query_terms if term in text)
                if matches > 0:
                    # Add a simple relevance score based on number of matches
                    matched_doc = doc.copy()
                    matched_doc["score"] = matches / len(query_terms)
                    matched_results.append(matched_doc)
            
            # Sort by score and take top_k
            matched_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            results = matched_results[:TOP_K_RESULTS]
            print(f"Found {len(results)} relevant documents")
            
            # Generate response using DeepSeek model
            answer = llm_service.generate_response(question, results, history=history)
            
            # Display the answer in green color
            print(f"\nStarBot: {colorama.Fore.GREEN}{answer}{colorama.Style.RESET_ALL}\n")
            
            # Add to conversation history
            history.append({"role": "user", "content": question})
            history.append({"role": "bot", "content": answer})
            
        except KeyboardInterrupt:
            print("\nExiting Star College Chatbot.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
