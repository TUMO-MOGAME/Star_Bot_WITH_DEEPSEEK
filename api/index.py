from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import hashlib
import time
import json
import re
from typing import List, Dict

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

# Load processed data
processed_data = []

def load_processed_data():
    """Load all processed data from JSON files"""
    global processed_data
    if processed_data:  # Already loaded
        return processed_data

    data_files = [
        "processed/sample_data.json",
        "processed/uploads_data.json",
        "processed/web_data.json"
    ]

    all_data = []
    for file_path in data_files:
        try:
            print(f"Checking file: {file_path}, exists: {os.path.exists(file_path)}")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                        print(f"Loaded {len(data)} items from {file_path}")
                    else:
                        print(f"Warning: {file_path} does not contain a list")
            else:
                print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    # Add fallback data if no files are loaded
    if not all_data:
        print("No processed data files found, using fallback data")
        all_data = [
            {
                "text": "Star College Durban is a private, independent school located in Westville North, Durban, South Africa. The school offers comprehensive education from Grade RR to Grade 12.",
                "metadata": {"source_type": "fallback", "section": "basic_info"}
            },
            {
                "text": "Star College maintains a 100% matric pass rate and is known for excellence in Mathematics, Science, and Computer Technology.",
                "metadata": {"source_type": "fallback", "section": "academics"}
            }
        ]

    processed_data = all_data
    print(f"Total processed data loaded: {len(processed_data)} items")
    return processed_data

def calculate_similarity_score(query: str, text: str) -> float:
    """Calculate similarity score between query and text using keyword matching and context"""
    query_lower = query.lower()
    text_lower = text.lower()

    # Split into words and remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}

    query_words = [word for word in query_lower.split() if word not in stop_words and len(word) > 2]
    text_words = text_lower.split()

    if not query_words:
        return 0.0

    # Calculate different types of matches
    exact_matches = sum(1 for word in query_words if word in text_lower)
    partial_matches = sum(1 for word in query_words if any(word in text_word for text_word in text_words))

    # Bonus for phrase matches
    phrase_bonus = 0
    for i in range(len(query_words) - 1):
        phrase = f"{query_words[i]} {query_words[i+1]}"
        if phrase in text_lower:
            phrase_bonus += 2

    # Calculate final score
    score = (exact_matches * 2 + partial_matches + phrase_bonus) / len(query_words)
    return score

def retrieve_relevant_chunks(query: str, max_results: int = 5, min_score: float = 0.1) -> List[Dict]:
    """RAG Retrieval: Search and retrieve most relevant chunks from processed data"""
    if not processed_data:
        load_processed_data()

    query_lower = query.lower()
    results = []

    print(f"RAG Retrieval: Searching through {len(processed_data)} documents for: '{query}'")

    # Calculate relevance scores for all chunks
    for item in processed_data:
        text = item.get('text', '')
        if not text:
            continue

        # Calculate similarity score
        score = calculate_similarity_score(query, text)

        if score >= min_score:
            results.append({
                'text': text,
                'metadata': item.get('metadata', {}),
                'relevance_score': score,
                'chunk_length': len(text)
            })

    # Sort by relevance score (descending)
    results.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Return top results
    top_results = results[:max_results]
    print(f"RAG Retrieval: Found {len(top_results)} relevant chunks with scores: {[r['relevance_score'] for r in top_results]}")

    return top_results

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

        # Try to load processed data
        try:
            load_processed_data()
            print(f"Processed data loaded: {len(processed_data)} items")
        except Exception as data_error:
            print(f"Error loading processed data: {data_error}")
            # Continue without processed data

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

        # RAG STEP 1: RETRIEVAL - Find relevant chunks from processed data
        try:
            print(f"RAG System: Starting retrieval for query: '{message}'")
            relevant_chunks = retrieve_relevant_chunks(message, max_results=5, min_score=0.1)
            print(f"RAG Retrieval: Found {len(relevant_chunks)} relevant chunks")

            if not relevant_chunks:
                print("RAG Retrieval: No relevant chunks found, trying with lower threshold")
                relevant_chunks = retrieve_relevant_chunks(message, max_results=3, min_score=0.05)

        except Exception as search_error:
            print(f"RAG Retrieval Error: {search_error}")
            relevant_chunks = []

        # Check cache for faster responses
        cache_key = hashlib.md5(f"{message.lower().strip()}_{selected_school}".encode()).hexdigest()
        current_time = time.time()

        if cache_key in response_cache:
            cached_response, cache_time = response_cache[cache_key]
            if current_time - cache_time < CACHE_DURATION:
                print(f"Cache hit for: {message[:30]}...")
                cached_response["metadata"]["cached"] = True
                return cached_response

        # RAG STEP 2: CHECK RETRIEVAL RESULTS
        if not relevant_chunks:
            print("RAG System: No relevant information found in knowledge base")
            no_data_message = """I don't have specific information about that topic in my Star College knowledge base.

I can help you with information about:
• Academic performance and matric results
• School facilities and programs
• Contact information and location
• Extracurricular activities
• School history and achievements

Please try asking about one of these topics."""

            return {
                "answer": no_data_message,
                "response": no_data_message,
                "sources": [{
                    "content": "Star College RAG Knowledge Base",
                    "metadata": {
                        "source_type": "rag_system",
                        "title": "Star College RAG Database",
                        "url": "https://starcollegedurban.co.za"
                    }
                }],
                "metadata": {
                    "rag_system": True,
                    "retrieval_results": 0,
                    "school_context": selected_school or "All Schools"
                }
            }

        # RAG STEP 3: AUGMENTATION - Create enhanced prompt with retrieved information
        print(f"RAG Augmentation: Creating prompt with {len(relevant_chunks)} retrieved chunks")

        # Build the context from retrieved chunks
        context_sections = []
        total_context_length = 0
        max_context_length = 3000  # Limit context to avoid token limits

        for i, chunk in enumerate(relevant_chunks, 1):
            chunk_text = chunk['text']
            chunk_score = chunk['relevance_score']
            metadata = chunk['metadata']

            # Add source information
            source_type = metadata.get('source_type', 'document')
            filename = metadata.get('filename', '')
            url = metadata.get('url', '')
            section = metadata.get('section', '')

            source_info = f"Source: {source_type}"
            if filename:
                source_info += f" - {filename}"
            if section:
                source_info += f" ({section})"
            if url:
                source_info += f" | {url}"

            # Limit chunk size to prevent token overflow
            if total_context_length + len(chunk_text) > max_context_length:
                chunk_text = chunk_text[:max_context_length - total_context_length] + "..."

            context_section = f"""
CONTEXT {i} (Relevance: {chunk_score:.2f}):
{chunk_text}
[{source_info}]
"""
            context_sections.append(context_section)
            total_context_length += len(chunk_text)

            if total_context_length >= max_context_length:
                break

        # RAG STEP 4: Create the augmented prompt
        rag_prompt = f"""You are a RAG-powered assistant for Star College Durban. You must answer the user's question using ONLY the retrieved context provided below. This is a Retrieval-Augmented Generation (RAG) system.

CRITICAL INSTRUCTIONS:
1. Use ONLY the information in the CONTEXT sections below
2. Do NOT use any external knowledge or training data
3. If the context doesn't contain enough information, clearly state this
4. Cite specific context sections when possible
5. Be accurate and helpful based solely on the retrieved information

RETRIEVED CONTEXT FROM STAR COLLEGE DATABASE:
{''.join(context_sections)}

USER QUESTION: {message}

RESPONSE GUIDELINES:
- Answer based exclusively on the context above
- Reference specific context sections when relevant (e.g., "According to Context 1...")
- If information is incomplete, acknowledge this and suggest related topics from the context
- Maintain a helpful and professional tone
- Focus specifically on Star College Durban"""

        if selected_school and selected_school != "All Star College Schools":
            rag_prompt += f"\n- The user is asking about {selected_school} specifically - focus on this school if mentioned in the context"

        print(f"RAG Augmentation: Created prompt with {len(context_sections)} context sections, total length: {total_context_length} chars")

        # RAG STEP 5: GENERATION - Use DeepSeek LLM with augmented prompt
        try:
            print("RAG Generation: Calling DeepSeek LLM with augmented prompt")

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(25.0, connect=10.0)
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
                            {"role": "system", "content": rag_prompt}
                        ],
                        "max_tokens": 800,  # Allow longer responses for detailed RAG answers
                        "temperature": 0.2,  # Low temperature for factual, consistent responses
                        "top_p": 0.9,
                        "frequency_penalty": 0.1,  # Reduce repetition
                        "presence_penalty": 0.1,   # Encourage diverse vocabulary
                        "stream": False
                    }
                )

                print(f"DeepSeek API response status: {response.status_code}")

                if response.status_code != 200:
                    error_text = response.text
                    print(f"DeepSeek API error response: {error_text}")
                    raise Exception(f"DeepSeek API returned status {response.status_code}: {error_text}")

        except httpx.TimeoutException:
            error_message = "The AI service is taking too long to respond. Please try again."
            return {
                "answer": error_message,
                "response": error_message,
                "sources": [],
                "metadata": {"error": "timeout"}
            }
        except httpx.ConnectError:
            error_message = "Unable to connect to the AI service. Please check your internet connection and try again."
            return {
                "answer": error_message,
                "response": error_message,
                "sources": [],
                "metadata": {"error": "connection_error"}
            }
        except Exception as api_error:
            print(f"DeepSeek API error: {str(api_error)}")
            error_message = f"AI service error: {str(api_error)}"
            return {
                "answer": error_message,
                "response": error_message,
                "sources": [],
                "metadata": {"error": str(api_error)}
            }

        # RAG STEP 6: PROCESS GENERATED RESPONSE
        try:
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            print(f"RAG Generation: Response generated successfully")
            print(f"RAG Generation: Response length: {len(ai_response)} chars, Tokens used: {tokens_used}")

        except Exception as parse_error:
            print(f"RAG Generation Error: Failed to parse DeepSeek response: {parse_error}")
            error_message = "Error processing RAG response. Please try again."
            return {
                "answer": error_message,
                "response": error_message,
                "sources": [],
                "metadata": {"error": "rag_response_parsing_error"}
            }

        # RAG STEP 7: CREATE SOURCES FROM RETRIEVED CHUNKS
        sources = []

        print(f"RAG Sources: Creating sources from {len(relevant_chunks)} retrieved chunks")

        for i, chunk in enumerate(relevant_chunks):
            metadata = chunk.get('metadata', {})
            source_type = metadata.get('source_type', 'document')
            relevance_score = chunk.get('relevance_score', 0.0)

            # Create source content preview
            content_preview = chunk['text'][:400] + "..." if len(chunk['text']) > 400 else chunk['text']

            if source_type == 'file':
                filename = metadata.get('filename', 'school_document')
                sources.append({
                    "content": content_preview,
                    "metadata": {
                        "source_type": "rag_document",
                        "title": f"Star College Document: {filename}",
                        "filename": filename,
                        "relevance_score": relevance_score,
                        "chunk_index": i + 1,
                        "url": "https://starcollegedurban.co.za"
                    }
                })
            elif source_type == 'web':
                url = metadata.get('url', 'https://starcollegedurban.co.za')
                title = metadata.get('title', 'Star College Web Content')
                sources.append({
                    "content": content_preview,
                    "metadata": {
                        "source_type": "rag_web_content",
                        "title": f"Star College Web: {title}",
                        "relevance_score": relevance_score,
                        "chunk_index": i + 1,
                        "url": url
                    }
                })
            else:
                section = metadata.get('section', 'general')
                sources.append({
                    "content": content_preview,
                    "metadata": {
                        "source_type": "rag_database",
                        "title": f"Star College Database: {section}",
                        "section": section,
                        "relevance_score": relevance_score,
                        "chunk_index": i + 1,
                        "url": "https://starcollegedurban.co.za"
                    }
                })

        # RAG STEP 8: CREATE FINAL RAG RESPONSE
        response_obj = {
            "answer": ai_response,
            "response": ai_response,
            "sources": sources,
            "metadata": {
                "system_type": "RAG (Retrieval-Augmented Generation)",
                "model_used": "deepseek-chat",
                "tokens_used": tokens_used,
                "school_context": selected_school or "All Schools",
                "cached": False,

                # RAG-specific metadata
                "rag_retrieval": {
                    "chunks_retrieved": len(relevant_chunks),
                    "relevance_scores": [chunk['relevance_score'] for chunk in relevant_chunks],
                    "total_context_length": total_context_length,
                    "min_score_threshold": 0.1
                },

                "rag_augmentation": {
                    "context_sections": len(context_sections),
                    "prompt_length": len(rag_prompt)
                },

                "rag_generation": {
                    "temperature": 0.2,
                    "max_tokens": 800,
                    "response_length": len(ai_response)
                },

                "information_source": "Star College RAG Knowledge Base",
                "data_only_responses": True
            }
        }

        print(f"RAG System: Complete! Retrieved {len(relevant_chunks)} chunks, generated {len(ai_response)} char response")

        # Cache the response for faster future responses
        response_cache[cache_key] = (response_obj, current_time)

        # Clean old cache entries (keep cache size manageable)
        if len(response_cache) > 100:
            oldest_key = min(response_cache.keys(), key=lambda k: response_cache[k][1])
            del response_cache[oldest_key]

        return response_obj

    except Exception as e:
        print(f"RAG System Error: {str(e)}")
        error_message = f"RAG system encountered an error while processing your request. Please try again. Error: {str(e)}"
        return {
            "answer": error_message,
            "response": error_message,
            "sources": [],
            "metadata": {
                "system_type": "RAG (Retrieval-Augmented Generation)",
                "error": str(e),
                "error_type": "rag_system_error"
            }
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
        "message": "Star College RAG Chatbot API is running on Vercel",
        "system_type": "RAG (Retrieval-Augmented Generation)",
        "llm_model": "deepseek-chat",
        "deepseek_configured": bool(DEEPSEEK_API_KEY),
        "knowledge_base_loaded": len(processed_data) > 0,
        "total_documents": len(processed_data),
        "cache_size": len(response_cache),
        "timestamp": time.time()
    }

@app.get("/rag-status")
async def rag_status():
    """Get detailed RAG system status"""
    try:
        load_processed_data()

        # Analyze the knowledge base
        source_types = {}
        total_chars = 0

        for item in processed_data:
            source_type = item.get('metadata', {}).get('source_type', 'unknown')
            source_types[source_type] = source_types.get(source_type, 0) + 1
            total_chars += len(item.get('text', ''))

        return {
            "system_type": "RAG (Retrieval-Augmented Generation)",
            "status": "operational",
            "components": {
                "retrieval": {
                    "status": "active",
                    "algorithm": "keyword_similarity_scoring",
                    "knowledge_base_size": len(processed_data),
                    "total_characters": total_chars,
                    "source_breakdown": source_types
                },
                "augmentation": {
                    "status": "active",
                    "max_context_length": 3000,
                    "context_sections": "dynamic"
                },
                "generation": {
                    "status": "active",
                    "llm_model": "deepseek-chat",
                    "configured": bool(DEEPSEEK_API_KEY),
                    "max_tokens": 800,
                    "temperature": 0.2
                }
            },
            "knowledge_base": {
                "files_loaded": [
                    "processed/sample_data.json",
                    "processed/uploads_data.json",
                    "processed/web_data.json"
                ],
                "total_chunks": len(processed_data),
                "source_types": list(source_types.keys())
            },
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "system_type": "RAG (Retrieval-Augmented Generation)",
            "status": "error",
            "error": str(e),
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

@app.get("/test-data")
async def test_data():
    """Test endpoint to check processed data loading"""
    try:
        load_processed_data()
        return {
            "status": "success",
            "data_loaded": len(processed_data),
            "sample_data": processed_data[:2] if processed_data else [],
            "files_checked": [
                {"file": "processed/sample_data.json", "exists": os.path.exists("processed/sample_data.json")},
                {"file": "processed/uploads_data.json", "exists": os.path.exists("processed/uploads_data.json")},
                {"file": "processed/web_data.json", "exists": os.path.exists("processed/web_data.json")}
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "files_checked": [
                {"file": "processed/sample_data.json", "exists": os.path.exists("processed/sample_data.json")},
                {"file": "processed/uploads_data.json", "exists": os.path.exists("processed/uploads_data.json")},
                {"file": "processed/web_data.json", "exists": os.path.exists("processed/web_data.json")}
            ]
        }

# Initialize processed data on startup
@app.on_event("startup")
async def startup_event():
    """Load processed data when the app starts"""
    load_processed_data()

# This is required for Vercel
app = app
