from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import hashlib
import time

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

# Simple in-memory cache for faster responses
response_cache = {}
CACHE_DURATION = 300  # 5 minutes cache

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

        # Check for quick answers to common questions first
        quick_answers = {
            "what is star college": "Star College Durban is a private, independent school in Westville North, Durban, established in 2002. It offers education from Grade RR to Grade 12 with a 100% matric pass rate since inception.",
            "when was star college established": "Star College Durban was established in 2002 by the Horizon Educational Trust.",
            "where is star college located": "Star College Durban is located in Westville North, Durban, South Africa.",
            "what is the pass rate": "Star College has maintained a 100% pass rate in the National Senior Certificate (Matric) exams since its inception in 2002.",
            "what is the school motto": "The school motto is 'Excellence in Education'.",
            "what schools are part of star college": "Star College includes: Boys High School, Girls High School, Primary School, and Little Dolphin Star Pre-Primary School."
        }

        # Check for quick answer match
        message_lower = message.lower().strip()
        for key, answer in quick_answers.items():
            if key in message_lower:
                return {
                    "answer": answer,
                    "response": answer,
                    "sources": [{
                        "content": "Star College official information",
                        "metadata": {
                            "source_type": "knowledge_base",
                            "title": "Star College Information",
                            "url": "https://starcollegedurban.co.za"
                        }
                    }],
                    "metadata": {"quick_answer": True, "school_context": selected_school or "All Schools"}
                }

        # Check cache for faster responses
        cache_key = hashlib.md5(f"{message.lower().strip()}_{selected_school}".encode()).hexdigest()
        current_time = time.time()

        if cache_key in response_cache:
            cached_response, cache_time = response_cache[cache_key]
            if current_time - cache_time < CACHE_DURATION:
                print(f"Cache hit for: {message[:30]}...")
                cached_response["metadata"]["cached"] = True
                return cached_response

        # Create comprehensive system prompt with detailed Star College information
        system_prompt = """You are a knowledgeable assistant for Star College Durban. Use the following accurate information to answer questions:

ABOUT STAR COLLEGE DURBAN:
Star College Durban is a private, independent school located in Westville North, Durban, South Africa. Established in 2002 by the Horizon Educational Trust, it offers comprehensive education from Grade RR to Grade 12, encompassing pre-primary, primary, and high school levels.

SCHOOLS WITHIN STAR COLLEGE:
- Star College Durban Boys High School
- Star College Durban Girls High School
- Star College Durban Primary School
- Little Dolphin Star Pre-Primary School

CURRICULUM & ACADEMICS:
- Follows the South African National Curriculum
- Known for strong academic performance in Mathematics, Science, and Computer Technology
- 100% pass rate in National Senior Certificate (Matric) exams since inception
- Many students achieve multiple distinctions
- Recognized as best-performing school in South Africa in Maths and Science Olympiad (2009)
- Consistently achieves top results in national and international Mathematics, Science, and Computer Olympiads

FACILITIES & ACTIVITIES:
- Specialized classrooms and sports facilities
- Cultural programs and extracurricular activities
- Balanced approach to education encouraging both academic and extracurricular participation

VALUES & ETHOS:
- School motto: "Excellence in Education"
- Fosters culture of respect, responsibility, and community
- Develops students who are compassionate, knowledgeable, and respectful
- Prepares students to be ethical leaders in society

WEBSITES: starcollegedurban.co.za, starboyshigh.co.za, starprimary.co.za

Provide helpful, accurate responses based on this information. Be friendly and informative."""

        if selected_school and selected_school != "All Star College Schools":
            system_prompt += f"\n\nThe user is specifically asking about {selected_school}. Focus your response on this particular school when relevant."

        # Optimize for faster responses
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),  # Faster timeout
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        ) as client:
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
                    "max_tokens": 400,  # Reduced for faster responses
                    "temperature": 0.5,  # Lower temperature for faster, more focused responses
                    "top_p": 0.9,  # Add top_p for better performance
                    "frequency_penalty": 0.1,  # Slight penalty to avoid repetition
                    "stream": False  # Ensure no streaming for consistent timing
                },
                timeout=15.0  # Faster timeout
            )

            print(f"DeepSeek API response status: {response.status_code}")  # Debug log

            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]

                # Create response object
                response_obj = {
                    "answer": ai_response,  # Your frontend expects 'answer', not 'response'
                    "response": ai_response,  # Keep both for compatibility
                    "sources": [
                        {
                            "content": "Star College Durban official information and knowledge base",
                            "metadata": {
                                "source_type": "knowledge_base",
                                "model": "deepseek-chat",
                                "title": "Star College Information Database",
                                "url": "https://starcollegedurban.co.za"
                            }
                        },
                        {
                            "content": "Additional school information from starboyshigh.co.za and starprimary.co.za",
                            "metadata": {
                                "source_type": "school_websites",
                                "title": "Star College School Websites",
                                "url": "https://starboyshigh.co.za"
                            }
                        }
                    ],
                    "metadata": {
                        "model_used": "deepseek-chat",
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                        "school_context": selected_school or "All Schools",
                        "cached": False,
                        "information_source": "Star College knowledge base"
                    }
                }

                # Cache the response for faster future responses
                response_cache[cache_key] = (response_obj, current_time)

                # Clean old cache entries (keep cache size manageable)
                if len(response_cache) > 100:
                    oldest_key = min(response_cache.keys(), key=lambda k: response_cache[k][1])
                    del response_cache[oldest_key]

                return response_obj
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
        "deepseek_configured": bool(DEEPSEEK_API_KEY),
        "cache_size": len(response_cache),
        "timestamp": time.time()
    }

@app.get("/warmup")
async def warmup():
    """Endpoint to keep the serverless function warm"""
    return {
        "status": "warm",
        "message": "Function is ready",
        "timestamp": time.time()
    }

# This is required for Vercel
app = app
