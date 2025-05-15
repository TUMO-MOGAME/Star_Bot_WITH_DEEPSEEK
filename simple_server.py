from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path
sys.path.append(os.getcwd())

# Import our services
from app.services.vector_store import VectorStore
from app.services.llm import LLMService

# Initialize services
vector_store = VectorStore(store_type="chroma")
llm_service = LLMService()

class ChatHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path.startswith('/chat'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            question = request_data.get('question', '')

            if not question:
                self.send_error(400, "No question provided")
                return

            try:
                # Search for relevant documents
                results = vector_store.search(question, 5)

                # Generate response
                answer = llm_service.generate_response(question, results)

                # Format sources for response
                sources = []
                for result in results:
                    # Get full text for context but truncate for display
                    source = {
                        "text": result.get("text", "")[:150] + "...",
                        "metadata": result.get("metadata", {}),
                        "score": float(result.get("score", 0))  # Ensure score is a float for JSON serialization
                    }
                    sources.append(source)

                # Create response
                response = {
                    "answer": answer,
                    "sources": sources
                }

                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()

                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            super().do_POST(self)

    def do_GET(self):
        super().do_GET(self)

def run(server_class=HTTPServer, handler_class=ChatHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
