from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx

# Create FastAPI app
app = FastAPI(
    title="Star College Chatbot",
    description="A chatbot for Star College in Durban",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get environment variables
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Main page route
@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Star College Chatbot</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            h1 { color: #0a3d62; text-align: center; margin-bottom: 30px; }
            .status { background: #2ecc71; color: white; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; }
            .chat-container { background: #f8f9fa; border-radius: 10px; padding: 20px; margin: 20px 0; }
            .chat-input { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
            .chat-button { background: #0a3d62; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 10px; }
            .chat-button:hover { background: #2c5282; }
            .response { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #2196f3; }
            .info { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌟 Star College Chatbot</h1>
            <div class="status">✅ Successfully Deployed on Vercel!</div>

            <div class="info">
                <strong>🚀 Deployment Status:</strong>
                <ul>
                    <li>✅ FastAPI application running</li>
                    <li>✅ CORS configured</li>
                    <li>✅ API endpoints active</li>
                    <li>🔑 DeepSeek API: """ + ("✅ Configured" if DEEPSEEK_API_KEY else "❌ Not configured") + """</li>
                </ul>
            </div>

            <div class="chat-container">
                <h3>💬 Test Chat Interface</h3>
                <form id="chatForm">
                    <input type="text" id="messageInput" class="chat-input" placeholder="Ask me about Star College..." required>
                    <button type="submit" class="chat-button">Send Message</button>
                </form>
                <div id="response" class="response" style="display: none;"></div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
                <p><a href="/health" style="color: #0a3d62;">🔍 Check API Health</a> |
                   <a href="/docs" style="color: #0a3d62;">📚 API Documentation</a></p>
            </div>
        </div>

        <script>
            document.getElementById('chatForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const message = document.getElementById('messageInput').value;
                const responseDiv = document.getElementById('response');

                responseDiv.style.display = 'block';
                responseDiv.innerHTML = '🤔 Thinking...';

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: 'message=' + encodeURIComponent(message)
                    });
                    const data = await response.json();
                    responseDiv.innerHTML = '🤖 ' + data.response;
                } catch (error) {
                    responseDiv.innerHTML = '❌ Error: ' + error.message;
                }
            });
        </script>
    </body>
    </html>
    """)

@app.post("/chat")
async def chat(message: str = Form(...)):
    """Simple chat endpoint using DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        return {"response": "Sorry, the AI service is not configured. Please contact the administrator."}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant for Star College in Durban, South Africa. Provide helpful information about the college."},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return {"response": data["choices"][0]["message"]["content"]}
            else:
                return {"response": f"Sorry, I'm having trouble connecting to the AI service. (Error: {response.status_code})"}

    except Exception as e:
        return {"response": f"Sorry, I encountered an error: {str(e)}"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Star College Chatbot API is running on Vercel",
        "deepseek_configured": bool(DEEPSEEK_API_KEY)
    }

# This is required for Vercel
app = app
