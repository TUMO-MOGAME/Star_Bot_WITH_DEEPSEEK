import os
import http.server
import socketserver

# Create directory structure if it doesn't exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)

# Simple HTTP server
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Map root to star_college_chatbot.html
        if self.path == '/':
            self.path = '/star_college_chatbot.html'
        # Map /widget to chatbot_widget_demo.html
        elif self.path == '/widget':
            self.path = '/chatbot_widget_demo.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Set up the server
handler_object = MyHttpRequestHandler
PORT = 8080
my_server = socketserver.TCPServer(("0.0.0.0", PORT), handler_object)

# Start the server
print(f"Server started at http://localhost:{PORT}")
print(f"Main chatbot: http://localhost:{PORT}/")
print(f"Widget demo: http://localhost:{PORT}/widget")
print("Press Ctrl+C to stop the server")

try:
    my_server.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    my_server.server_close()
