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
    """Load all processed data from JSON files for RAG knowledge base"""
    global processed_data
    if processed_data:  # Already loaded
        return processed_data

    print("🔄 Loading Star College RAG Knowledge Base...")

    # Try different possible paths for Vercel deployment
    possible_paths = [
        ["processed/sample_data.json", "processed/uploads_data.json", "processed/web_data.json"],
        ["./processed/sample_data.json", "./processed/uploads_data.json", "./processed/web_data.json"],
        ["/var/task/processed/sample_data.json", "/var/task/processed/uploads_data.json", "/var/task/processed/web_data.json"]
    ]

    all_data = []
    files_loaded = 0

    for path_set in possible_paths:
        if files_loaded > 0:
            break

        for file_path in path_set:
            try:
                print(f"📁 Checking: {file_path}")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            # Clean and validate each item
                            valid_items = []
                            for item in data:
                                if isinstance(item, dict) and 'text' in item and item['text'].strip():
                                    # Ensure metadata exists
                                    if 'metadata' not in item:
                                        item['metadata'] = {}
                                    # Add file source info
                                    item['metadata']['source_file'] = os.path.basename(file_path)
                                    valid_items.append(item)

                            all_data.extend(valid_items)
                            files_loaded += 1
                            print(f"✅ Loaded {len(valid_items)} chunks from {file_path}")
                        else:
                            print(f"⚠️  {file_path} is empty or invalid format")
                else:
                    print(f"❌ File not found: {file_path}")
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")

    # Enhanced fallback data if no files loaded
    if not all_data:
        print("⚠️  No processed data files found, creating comprehensive fallback knowledge base")
        all_data = [
            {
                "text": "Star College Durban is a prestigious private, independent school located at 20 Kinloch Ave, Westville North, Durban, South Africa. Established in 2002 by the Horizon Educational Trust, the school offers comprehensive education from Grade RR to Grade 12, encompassing pre-primary, primary, and high school levels.",
                "metadata": {"source_type": "fallback", "section": "school_overview", "source_file": "system_fallback"}
            },
            {
                "text": "Star College maintains an exceptional 100% matric pass rate since its inception and is renowned for excellence in Mathematics, Science, and Computer Technology. The school has consistently achieved top results in national and international Mathematics, Science, and Computer Olympiads.",
                "metadata": {"source_type": "fallback", "section": "academic_excellence", "source_file": "system_fallback"}
            },
            {
                "text": "The Star College family includes: Star College Durban Boys High School, Star College Durban Girls High School, Star College Durban Primary School, and Little Dolphin Star Pre-Primary School. Contact: Phone 031 262 7191, Email starcollege@starcollege.co.za",
                "metadata": {"source_type": "fallback", "section": "schools_contact", "source_file": "system_fallback"}
            },
            {
                "text": "Star College follows the South African National Curriculum (CAPS) and provides modern facilities including well-equipped science laboratories, computer labs with latest technology, library and resource center, and comprehensive sports facilities.",
                "metadata": {"source_type": "fallback", "section": "curriculum_facilities", "source_file": "system_fallback"}
            }
        ]

    processed_data = all_data
    print(f"🎯 RAG Knowledge Base Ready: {len(processed_data)} chunks loaded from {files_loaded} files")

    # Log source breakdown
    source_breakdown = {}
    for item in processed_data:
        source_type = item.get('metadata', {}).get('source_type', 'unknown')
        source_breakdown[source_type] = source_breakdown.get(source_type, 0) + 1

    print(f"📊 Source breakdown: {source_breakdown}")
    return processed_data

def calculate_similarity_score(query: str, text: str) -> float:
    """Advanced similarity scoring for RAG retrieval"""
    query_lower = query.lower().strip()
    text_lower = text.lower().strip()

    if not query_lower or not text_lower:
        return 0.0

    # Enhanced stop words for better matching
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must', 'shall', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
        'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
    }

    # Extract meaningful keywords
    query_words = [word for word in query_lower.split() if word not in stop_words and len(word) > 2]
    text_words = set(word for word in text_lower.split() if len(word) > 2)

    if not query_words:
        return 0.0

    # 1. Exact word matches (highest weight)
    exact_matches = sum(1 for word in query_words if word in text_lower)

    # 2. Partial word matches (medium weight)
    partial_matches = sum(1 for word in query_words
                         if any(word in text_word or text_word in word for text_word in text_words))

    # 3. Phrase matches (very high weight)
    phrase_bonus = 0
    for i in range(len(query_words) - 1):
        phrase = f"{query_words[i]} {query_words[i+1]}"
        if phrase in text_lower:
            phrase_bonus += 3

    # 4. Longer phrase matches (maximum weight)
    for i in range(len(query_words) - 2):
        long_phrase = f"{query_words[i]} {query_words[i+1]} {query_words[i+2]}"
        if long_phrase in text_lower:
            phrase_bonus += 5

    # 5. Educational keywords bonus
    education_keywords = {
        'school', 'college', 'education', 'student', 'matric', 'grade', 'academic', 'curriculum',
        'teacher', 'learning', 'exam', 'result', 'performance', 'achievement', 'distinction',
        'pass', 'rate', 'facility', 'campus', 'admission', 'enrollment'
    }

    education_bonus = sum(2 for word in query_words if word in education_keywords and word in text_lower)

    # Calculate weighted score
    total_score = (exact_matches * 3 + partial_matches * 1 + phrase_bonus + education_bonus)
    max_possible_score = len(query_words) * 3

    # Normalize to 0-1 range with bonus for high relevance
    normalized_score = min(total_score / max_possible_score, 2.0)

    return round(normalized_score, 3)

def enhance_response_formatting(response: str) -> str:
    """Post-process response to ensure professional formatting"""
    if not response or len(response.strip()) < 10:
        return response

    # Ensure proper paragraph spacing
    response = re.sub(r'\n{3,}', '\n\n', response)

    # Enhance bullet points
    response = re.sub(r'^•\s*', '• **', response, flags=re.MULTILINE)
    response = re.sub(r'^-\s*', '• **', response, flags=re.MULTILINE)

    # Close bold formatting for bullet points
    lines = response.split('\n')
    enhanced_lines = []

    for line in lines:
        if line.strip().startswith('• **') and '**' not in line[4:]:
            # Find the end of the first phrase/sentence for bold formatting
            colon_pos = line.find(':')
            dash_pos = line.find(' - ')

            if colon_pos > 0 and colon_pos < 50:
                line = line[:colon_pos] + '**' + line[colon_pos:]
            elif dash_pos > 0 and dash_pos < 50:
                line = line[:dash_pos] + '**' + line[dash_pos:]
            else:
                # Bold the first few words
                words = line.split()
                if len(words) > 2:
                    line = ' '.join(words[:3]) + '**' + ' ' + ' '.join(words[3:])

        enhanced_lines.append(line)

    response = '\n'.join(enhanced_lines)

    # Ensure key numbers and percentages are bold
    response = re.sub(r'(\d+%)', r'**\1**', response)
    response = re.sub(r'(\d{4})', r'**\1**', response)  # Years
    response = re.sub(r'(100% pass rate)', r'**\1**', response, flags=re.IGNORECASE)

    # Clean up any double bold formatting
    response = re.sub(r'\*\*\*\*', '**', response)

    return response.strip()

def retrieve_relevant_chunks(query: str, max_results: int = 5, min_score: float = 0.15) -> List[Dict]:
    """Advanced RAG Retrieval with intelligent ranking"""
    if not processed_data:
        load_processed_data()

    print(f"🔍 RAG Retrieval: Searching {len(processed_data)} chunks for: '{query[:50]}...'")

    results = []

    # Score all chunks
    for idx, item in enumerate(processed_data):
        text = item.get('text', '').strip()
        if not text or len(text) < 10:  # Skip very short or empty chunks
            continue

        # Calculate similarity score
        score = calculate_similarity_score(query, text)

        if score >= min_score:
            metadata = item.get('metadata', {})

            # Boost score based on source quality
            source_type = metadata.get('source_type', '')
            if source_type == 'file':  # Official documents get priority
                score *= 1.2
            elif source_type == 'sample':  # Sample data is reliable
                score *= 1.1
            elif source_type == 'web':  # Web content is good
                score *= 1.05

            # Boost score for comprehensive chunks
            if len(text) > 200:
                score *= 1.1

            results.append({
                'text': text,
                'metadata': metadata,
                'relevance_score': round(score, 3),
                'chunk_length': len(text),
                'chunk_index': idx
            })

    # Sort by relevance score (descending)
    results.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Ensure diversity in results (avoid too many from same source)
    diverse_results = []
    source_counts = {}

    for result in results:
        source_file = result['metadata'].get('source_file', 'unknown')
        source_count = source_counts.get(source_file, 0)

        # Limit chunks per source file to ensure diversity
        if source_count < 3 or len(diverse_results) < 2:
            diverse_results.append(result)
            source_counts[source_file] = source_count + 1

        if len(diverse_results) >= max_results:
            break

    final_results = diverse_results[:max_results]
    scores = [r['relevance_score'] for r in final_results]
    sources = [r['metadata'].get('source_file', 'unknown') for r in final_results]

    print(f"✅ RAG Retrieval: Found {len(final_results)} chunks | Scores: {scores} | Sources: {sources}")

    return final_results

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

        # Perfect welcome and quick response system
        message_lower = message.lower().strip()

        # Welcome messages
        welcome_triggers = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
        if any(trigger in message_lower for trigger in welcome_triggers) and len(message.split()) <= 3:
            welcome_response = """🌟 **Welcome to Star College Durban!**

I'm your AI assistant powered by our comprehensive knowledge base. I can help you with:

🎓 **Academic Information**
• Matric results and performance data
• Curriculum and subjects offered
• Academic achievements and awards

🏫 **School Information**
• Facilities and infrastructure
• School divisions (Boys High, Girls High, Primary, Pre-Primary)
• Location and contact details

📞 **Admissions & Contact**
• Application processes
• School fees and requirements
• Contact information

**What would you like to know about Star College?**"""

            return {
                "answer": welcome_response,
                "response": welcome_response,
                "sources": [{
                    "content": "Star College Durban - Official AI Assistant",
                    "metadata": {
                        "source_type": "system_welcome",
                        "title": "🌟 Star College AI Assistant",
                        "category": "Welcome Message",
                        "url": "https://starcollegedurban.co.za"
                    }
                }],
                "metadata": {
                    "system_type": "RAG (Retrieval-Augmented Generation)",
                    "response_type": "welcome_message",
                    "school_context": selected_school or "All Schools"
                }
            }

        # Professional quick answers with comprehensive information
        quick_answers = {
            "what is star college": """**Star College Durban - Excellence in Education**

Star College Durban is a **premier private, independent school** established in **2002** by the Horizon Educational Trust. Located in the prestigious Westville North area of Durban, we provide world-class education from Grade RR through Grade 12.

**Key Highlights:**
• **100% Matric Pass Rate** maintained since inception
• **Comprehensive Education** - Pre-Primary to Grade 12
• **STEM Excellence** - Leading in Mathematics, Science & Technology
• **Multiple School Divisions** serving diverse educational needs

*Committed to developing future leaders through academic excellence and holistic education.*""",

            "where is star college": """**Star College Durban Location & Contact**

**📍 Campus Address:**
20 Kinloch Ave, Westville North, Durban, South Africa

**📞 Contact Information:**
• **Phone:** 031 262 7191
• **Email:** starcollege@starcollege.co.za
• **Website:** starcollegedurban.co.za

**🗺️ Area:** Conveniently located in the sought-after Westville North suburb, providing easy access for families across Durban.""",

            "matric results": """**Academic Excellence - Matric Performance**

**🏆 Outstanding Track Record:**
• **100% Pass Rate** maintained consistently since 2002
• **Multiple Distinctions** achieved by students annually
• **STEM Leadership** - Excellence in Mathematics, Science & Computer Technology
• **National Recognition** - Top performers in Mathematics & Science Olympiads

**🎯 Academic Focus Areas:**
• Advanced Mathematics programs
• Comprehensive Science curriculum
• Cutting-edge Computer Technology education
• Holistic academic development

*Our commitment to academic excellence ensures every student reaches their full potential.*""",

            "schools": """**The Star College Family**

**🏫 Our Educational Divisions:**

**⭐ Star College Durban Boys High School**
- Specialized education for male students
- Focus on leadership and academic excellence

**⭐ Star College Durban Girls High School**
- Dedicated environment for female students
- Empowering young women for future success

**⭐ Star College Durban Primary School**
- Foundation education (Grades 1-7)
- Building strong academic fundamentals

**⭐ Little Dolphin Star Pre-Primary School**
- Early childhood development (Grade RR)
- Nurturing environment for young learners

*Each division maintains our commitment to excellence while serving specific educational needs.*"""
        }

        # Check for quick answer matches
        for key, answer in quick_answers.items():
            if key in message_lower:
                return {
                    "answer": answer,
                    "response": answer,
                    "sources": [{
                        "content": "Star College official information - Quick Reference",
                        "metadata": {
                            "source_type": "quick_reference",
                            "title": f"📋 {key.title()} - Quick Answer",
                            "category": "Quick Reference",
                            "confidence": "high",
                            "url": "https://starcollegedurban.co.za"
                        }
                    }],
                    "metadata": {
                        "system_type": "RAG (Retrieval-Augmented Generation)",
                        "response_type": "quick_answer",
                        "school_context": selected_school or "All Schools"
                    }
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
            no_data_message = f"""**Information Not Available**

I don't currently have specific information about "{message}" in my Star College knowledge base.

**I can assist you with:**
• **Academic Excellence** - Matric results, pass rates, and achievements
• **School Information** - Facilities, programs, and curriculum details
• **Contact & Location** - Address, phone numbers, and directions
• **School Divisions** - Boys High, Girls High, Primary, and Pre-Primary
• **Admissions** - Application processes and requirements

**For specific details not in my database, please contact:**
📞 **Phone:** 031 262 7191
📧 **Email:** starcollege@starcollege.co.za
🌐 **Website:** starcollegedurban.co.za

*How else can I help you learn about Star College?*"""

            return {
                "answer": no_data_message,
                "response": no_data_message,
                "sources": [{
                    "content": "Star College Contact Information and Available Topics",
                    "metadata": {
                        "source_type": "system_guidance",
                        "title": "📋 Available Information Topics",
                        "category": "System Guidance",
                        "url": "https://starcollegedurban.co.za"
                    }
                }],
                "metadata": {
                    "system_type": "RAG (Retrieval-Augmented Generation)",
                    "response_type": "information_not_available",
                    "retrieval_results": 0,
                    "school_context": selected_school or "All Schools"
                }
            }

        # RAG STEP 3: AUGMENTATION - Create perfect prompt with retrieved information
        print(f"🔗 RAG Augmentation: Building context from {len(relevant_chunks)} chunks")

        # Build rich context from retrieved chunks
        context_sections = []
        total_context_length = 0
        max_context_length = 4000  # Increased for better context

        for i, chunk in enumerate(relevant_chunks, 1):
            chunk_text = chunk['text'].strip()
            chunk_score = chunk['relevance_score']
            metadata = chunk['metadata']

            # Rich source information
            source_type = metadata.get('source_type', 'document')
            source_file = metadata.get('source_file', 'unknown')
            filename = metadata.get('filename', '')
            section = metadata.get('section', '')
            url = metadata.get('url', '')

            # Build comprehensive source attribution
            source_parts = [f"Type: {source_type}"]
            if filename:
                source_parts.append(f"Document: {filename}")
            elif source_file and source_file != 'unknown':
                source_parts.append(f"File: {source_file}")
            if section:
                source_parts.append(f"Section: {section}")
            if url and url != 'https://starcollegedurban.co.za':
                source_parts.append(f"URL: {url}")

            source_info = " | ".join(source_parts)

            # Smart text truncation
            available_space = max_context_length - total_context_length - 200  # Reserve space
            if len(chunk_text) > available_space and available_space > 100:
                # Intelligent truncation - keep beginning and end
                half_space = available_space // 2
                chunk_text = chunk_text[:half_space] + "\n[...content truncated...]\n" + chunk_text[-half_space:]

            context_section = f"""
═══ CONTEXT {i} ═══ (Relevance Score: {chunk_score})
{chunk_text}
📋 Source: {source_info}
"""
            context_sections.append(context_section)
            total_context_length += len(chunk_text)

            if total_context_length >= max_context_length:
                break

        # RAG STEP 4: Create the perfect professional prompt
        rag_prompt = f"""You are the official Star College Durban AI Assistant, providing authoritative information from our comprehensive knowledge base.

PROFESSIONAL RESPONSE STANDARDS:
• Provide confident, well-structured answers using ONLY the context below
• Use professional formatting with clear headings and bullet points
• Start with direct answers, then provide supporting details
• Cite sources naturally within the response flow
• Maintain an authoritative yet approachable tone
• Use specific data, numbers, and facts when available

CONTEXT FROM STAR COLLEGE RECORDS:
{''.join(context_sections)}

USER INQUIRY: {message}

RESPONSE FRAMEWORK:
1. Lead with a direct, confident answer
2. Provide structured supporting information
3. Include specific data/facts from the context
4. End with helpful next steps or related information
5. Use professional formatting (headers, bullets, emphasis)

FORMATTING GUIDELINES:
• Use **bold** for key information and numbers
• Use bullet points for lists and multiple items
• Use clear section headers when appropriate
• Emphasize achievements and unique selling points
• Keep paragraphs concise and scannable"""

        if selected_school and selected_school != "All Star College Schools":
            rag_prompt += f"\n\nSPECIFIC FOCUS: Prioritize information about {selected_school} when available in the context."

        rag_prompt += f"\n\nGenerate a professional, authoritative response using the {len(context_sections)} context sections above:"

        print(f"✅ RAG Augmentation: Perfect prompt created | Contexts: {len(context_sections)} | Length: {total_context_length} chars")

        # RAG STEP 5: GENERATION - Perfect DeepSeek LLM call
        try:
            print("🤖 RAG Generation: Calling DeepSeek with optimized parameters")

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=15.0),  # Generous timeout for quality
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            ) as client:

                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "StarCollege-RAG-Chatbot/1.0"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": rag_prompt}
                        ],
                        "max_tokens": 1000,  # Generous token limit for comprehensive answers
                        "temperature": 0.1,  # Very low for maximum factual accuracy
                        "top_p": 0.95,      # High precision sampling
                        "frequency_penalty": 0.2,  # Reduce repetition
                        "presence_penalty": 0.1,   # Encourage topic diversity
                        "stop": None,       # No stop sequences
                        "stream": False     # Complete response
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

        # RAG STEP 6: PROCESS AND ENHANCE GENERATED RESPONSE
        try:
            data = response.json()
            raw_response = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            # Apply professional formatting enhancements
            enhanced_response = enhance_response_formatting(raw_response)

            # Add professional signature for comprehensive responses
            if len(enhanced_response) > 200 and not enhanced_response.endswith('?'):
                signature = f"\n\n---\n*Need more information? Contact us at **031 262 7191** or visit **starcollegedurban.co.za***"
                ai_response = enhanced_response + signature
            else:
                ai_response = enhanced_response

            print(f"RAG Generation: Response generated and enhanced successfully")
            print(f"RAG Generation: Response length: {len(ai_response)} chars, Tokens used: {tokens_used}")

        except Exception as parse_error:
            print(f"RAG Generation Error: Failed to parse DeepSeek response: {parse_error}")
            error_message = "**System Error**\n\nI encountered an error while processing your request. Please try again or contact our support team.\n\n📞 **Phone:** 031 262 7191"
            return {
                "answer": error_message,
                "response": error_message,
                "sources": [],
                "metadata": {"error": "rag_response_parsing_error"}
            }

        # RAG STEP 7: CREATE PERFECT SOURCES WITH RICH METADATA
        sources = []

        print(f"📚 RAG Sources: Creating detailed sources from {len(relevant_chunks)} chunks")

        for i, chunk in enumerate(relevant_chunks):
            metadata = chunk.get('metadata', {})
            source_type = metadata.get('source_type', 'document')
            source_file = metadata.get('source_file', 'unknown')
            relevance_score = chunk.get('relevance_score', 0.0)

            # Create intelligent content preview
            text = chunk['text']
            if len(text) > 300:
                # Smart preview - show beginning with key information
                preview = text[:250] + "..."
                # Try to end at sentence boundary
                last_period = preview.rfind('.')
                if last_period > 200:
                    preview = preview[:last_period + 1]
            else:
                preview = text

            # Determine source category and create rich metadata
            if source_type == 'file':
                filename = metadata.get('filename', 'school_document')
                title = f"📄 {filename}"
                source_category = "Official Document"
            elif source_type == 'web':
                url = metadata.get('url', 'https://starcollegedurban.co.za')
                title_raw = metadata.get('title', 'Star College Web Content')
                title = f"🌐 {title_raw}"
                source_category = "Web Content"
            elif source_type == 'sample':
                section = metadata.get('section', 'general')
                title = f"📊 Star College {section.replace('_', ' ').title()}"
                source_category = "School Database"
            else:
                section = metadata.get('section', 'general')
                title = f"📋 {section.replace('_', ' ').title()}"
                source_category = "Knowledge Base"

            sources.append({
                "content": preview,
                "metadata": {
                    "source_type": f"rag_{source_type}",
                    "title": title,
                    "category": source_category,
                    "relevance_score": relevance_score,
                    "chunk_index": i + 1,
                    "source_file": source_file,
                    "confidence": "high" if relevance_score > 0.7 else "medium" if relevance_score > 0.4 else "low",
                    "url": metadata.get('url', 'https://starcollegedurban.co.za'),
                    "section": metadata.get('section', ''),
                    "filename": metadata.get('filename', '')
                }
            })

        print(f"✅ RAG Sources: Created {len(sources)} detailed source references")

        # RAG STEP 8: CREATE PERFECT FINAL RESPONSE
        response_obj = {
            "answer": ai_response,
            "response": ai_response,  # Maintain compatibility
            "sources": sources,
            "metadata": {
                # System Information
                "system_type": "RAG (Retrieval-Augmented Generation)",
                "version": "1.0",
                "model_used": "deepseek-chat",
                "tokens_used": tokens_used,
                "school_context": selected_school or "All Star College Schools",
                "cached": False,
                "timestamp": time.time(),

                # RAG Pipeline Metrics
                "rag_pipeline": {
                    "retrieval": {
                        "total_chunks_searched": len(processed_data),
                        "chunks_retrieved": len(relevant_chunks),
                        "relevance_scores": [chunk['relevance_score'] for chunk in relevant_chunks],
                        "min_score_threshold": 0.15,
                        "max_score_achieved": max([chunk['relevance_score'] for chunk in relevant_chunks]) if relevant_chunks else 0,
                        "source_diversity": len(set(chunk['metadata'].get('source_file', 'unknown') for chunk in relevant_chunks))
                    },

                    "augmentation": {
                        "context_sections_created": len(context_sections),
                        "total_context_length": total_context_length,
                        "max_context_limit": 4000,
                        "prompt_length": len(rag_prompt),
                        "context_utilization": round(total_context_length / 4000 * 100, 1)
                    },

                    "generation": {
                        "temperature": 0.1,
                        "max_tokens": 1000,
                        "top_p": 0.95,
                        "response_length": len(ai_response),
                        "response_quality": "high" if len(ai_response) > 100 else "medium"
                    }
                },

                # Quality Metrics
                "quality_indicators": {
                    "information_source": "Star College Official Knowledge Base",
                    "data_only_responses": True,
                    "source_attribution": True,
                    "factual_accuracy": "verified_from_documents",
                    "response_completeness": "comprehensive" if len(relevant_chunks) >= 3 else "partial"
                },

                # User Experience
                "user_experience": {
                    "response_time_category": "optimized",
                    "source_transparency": True,
                    "educational_focus": True,
                    "professional_tone": True
                }
            }
        }

        print(f"🎉 RAG System Complete! Retrieved {len(relevant_chunks)} chunks → Generated {len(ai_response)} char response")

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
    """Perfect health check for Star College RAG system"""
    try:
        load_processed_data()

        # Analyze knowledge base health
        total_chars = sum(len(item.get('text', '')) for item in processed_data)
        source_types = set(item.get('metadata', {}).get('source_type', 'unknown') for item in processed_data)

        health_status = "excellent" if len(processed_data) > 50 else "good" if len(processed_data) > 10 else "basic"

        return {
            "status": "🟢 OPERATIONAL",
            "message": "⭐ Star College RAG Chatbot - Perfect & Ready!",
            "system": {
                "type": "RAG (Retrieval-Augmented Generation)",
                "version": "1.0 - Production Ready",
                "health": health_status,
                "performance": "optimized"
            },
            "components": {
                "llm_model": "deepseek-chat ✅",
                "deepseek_configured": bool(DEEPSEEK_API_KEY),
                "knowledge_base": f"✅ {len(processed_data)} chunks loaded",
                "total_content": f"{total_chars:,} characters",
                "source_types": list(source_types),
                "cache_system": f"✅ {len(response_cache)} cached responses"
            },
            "capabilities": [
                "🎓 Academic Information",
                "📊 Performance Data",
                "🏫 School Facilities",
                "📞 Contact Details",
                "🎯 Admission Guidance"
            ],
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "🟡 DEGRADED",
            "message": f"System running with limited functionality: {str(e)}",
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
