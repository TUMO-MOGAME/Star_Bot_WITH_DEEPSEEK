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
        error_message = "Sorry, the AI service is not configured. Please contact the administrator."
        return {
            "answer": error_message,
            "response": error_message,
            "sources": [],
            "metadata": {}
        }

    try:
        # Parse the JSON request body
        body = await request.json()
        # Your frontend sends 'question' and 'school', not 'message' and 'selectedSchool'
        message = body.get("question", "") or body.get("message", "")
        selected_school = body.get("school", "") or body.get("selectedSchool", "")
        chat_history = body.get("history", [])

        print(f"Received question: {message}")  # Debug log
        print(f"Selected school: {selected_school}")  # Debug log
        print(f"Chat history length: {len(chat_history)}")  # Debug log

        if not message.strip():
            empty_message = "Please enter a message to get started!"
            return {
                "answer": empty_message,
                "response": empty_message,
                "sources": [],
                "metadata": {}
            }

        # Create system prompt based on selected school
        system_prompt = """You are a helpful assistant for Star College in Durban, South Africa.

Star College is a prestigious educational institution with multiple schools:
- Star College Durban Boys High School
- Star College Durban Girls High School
- Star College Durban Primary School
- Little Dolphin Star Pre-Primary School

Provide helpful, accurate, and friendly information about Star College. Be conversational and informative."""

        if selected_school and selected_school != "All Star College Schools":
            system_prompt += f"\n\nThe user is specifically asking about {selected_school}. Focus your response on this particular school when relevant."

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

            print(f"DeepSeek API response status: {response.status_code}")  # Debug log

            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]

                # Return response in the format expected by the frontend (data.answer, data.sources)
                return {
                    "answer": ai_response,  # Your frontend expects 'answer', not 'response'
                    "response": ai_response,  # Keep both for compatibility
                    "sources": [
                        {
                            "content": "Response generated using DeepSeek AI with Star College knowledge",
                            "metadata": {
                                "source_type": "ai",
                                "model": "deepseek-chat",
                                "title": "AI Generated Response",
                                "url": "https://api.deepseek.com"
                            }
                        }
                    ],
                    "metadata": {
                        "model_used": "deepseek-chat",
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "school_context": selected_school or "All Schools"
                    }
                }
            else:
                error_text = response.text if hasattr(response, 'text') else "Unknown error"
                print(f"DeepSeek API error: {error_text}")  # Debug log
                error_message = f"I'm having trouble connecting to the AI service right now. Please try again in a moment. (Error: {response.status_code})"
                return {
                    "answer": error_message,
                    "response": error_message,
                    "sources": [],
                    "metadata": {"error": f"API Error {response.status_code}"}
                }

    except Exception as e:
        print(f"Chat endpoint error: {str(e)}")  # Debug log
        error_message = f"I encountered an error while processing your request. Please try again. Error: {str(e)}"
        return {
            "answer": error_message,
            "response": error_message,
            "sources": [],
            "metadata": {"error": str(e)}
        }

@app.post("/feedback")
async def feedback(request: Request):
    """Feedback endpoint for user ratings"""
    try:
        body = await request.json()
        question = body.get("question", "")
        answer = body.get("answer", "")
        feedback_type = body.get("feedback", "")
        sources = body.get("sources", [])

        # Log the feedback (in production, you'd save to database)
        print(f"Feedback received - Question: {question[:50]}..., Feedback: {feedback_type}")

        return {"status": "success", "message": "Thank you for your feedback!"}
    except Exception as e:
        print(f"Feedback error: {str(e)}")
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
