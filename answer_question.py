import sys
import json
from app.services.vector_store import VectorStore
from app.services.llm import LLMService
from app.config import TOP_K_RESULTS

def main():
    print("StarBot CLI (with conversational memory). Type 'exit' to quit.\n")
    vector_store = VectorStore(store_type="chroma")
    llm_service = LLMService()
    history = []
    while True:
        try:
            if len(sys.argv) > 1:
                question = " ".join(sys.argv[1:])
                sys.argv = [sys.argv[0]]  # Reset for next loop
            else:
                question = input("You: ").strip()
            if not question or question.lower() in {"exit", "quit"}:
                print("Exiting StarBot CLI.")
                break
            print(f"Question: {question}")
            results = vector_store.search(question, TOP_K_RESULTS)
            answer = llm_service.generate_response(question, results, history=history)
            print(f"\nStarBot: {answer}\n")
            # Add to history
            history.append({"role": "user", "content": question})
            history.append({"role": "bot", "content": answer})
        except KeyboardInterrupt:
            print("\nExiting StarBot CLI.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()
