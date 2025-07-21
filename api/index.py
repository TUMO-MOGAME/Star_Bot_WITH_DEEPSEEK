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

# Main page route - serve the existing index.html
@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        # Try to read the index.html file from the project root
        index_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback if index.html is not found
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Star College Chatbot</title></head>
        <body>
            <h1>Star College Chatbot</h1>
            <p>Welcome! The main interface is loading...</p>
            <p>If you see this message, please check that index.html is properly deployed.</p>
        </body>
        </html>
        """)

@app.post("/chat")
async def chat(request: Request):
    """Chat endpoint that matches the frontend's expectations"""
    if not DEEPSEEK_API_KEY:
        return {
            "response": "Sorry, the AI service is not configured. Please contact the administrator.",
            "sources": [],
            "metadata": {}
        }

    try:
        # Parse the JSON request body
        body = await request.json()
        message = body.get("message", "")
        selected_school = body.get("selectedSchool", "")

        # Create system prompt based on selected school
        system_prompt = "You are a helpful assistant for Star College in Durban, South Africa. Provide helpful and accurate information about the college."
        if selected_school:
            system_prompt += f" The user is specifically asking about {selected_school}."

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
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 800,
                    "temperature": 0.7
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]

                # Return response in the format expected by the frontend
                return {
                    "response": ai_response,
                    "sources": [
                        {
                            "content": "Response generated using DeepSeek AI",
                            "metadata": {
                                "source_type": "ai",
                                "model": "deepseek-chat",
                                "title": "AI Generated Response"
                            }
                        }
                    ],
                    "metadata": {
                        "model_used": "deepseek-chat",
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                    }
                }
            else:
                return {
                    "response": f"Sorry, I'm having trouble connecting to the AI service. (Error: {response.status_code})",
                    "sources": [],
                    "metadata": {"error": f"API Error {response.status_code}"}
                }

    except Exception as e:
        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "sources": [],
            "metadata": {"error": str(e)}
        }

@app.post("/feedback")
async def feedback(request: Request):
    """Feedback endpoint for user ratings"""
    try:
        body = await request.json()
        # For now, just log the feedback (in production, you'd save to database)
        print(f"Feedback received: {body}")
        return {"status": "success", "message": "Thank you for your feedback!"}
    except Exception as e:
        return {"status": "error", "message": f"Error processing feedback: {str(e)}"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Star College Chatbot API is running on Vercel",
        "deepseek_configured": bool(DEEPSEEK_API_KEY)
    }

# This is required for Vercel
app = app
