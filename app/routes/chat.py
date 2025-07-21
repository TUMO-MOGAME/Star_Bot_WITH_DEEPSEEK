from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import os
from pathlib import Path

from app.services.llm import LLMService
from app.config import TOP_K_RESULTS

# Get folder paths from environment variables
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")

router = APIRouter()

# Set up logging
logger = logging.getLogger("starbot.chat")
logging.basicConfig(level=logging.INFO)

def load_processed_data():
    """Load data from processed files."""
    all_data = []

    # Load uploads data
    uploads_data_path = Path(PROCESSED_FOLDER) / "uploads_data.json"
    if uploads_data_path.exists():
        try:
            with open(uploads_data_path, 'r', encoding='utf-8') as f:
                uploads_data = json.load(f)
                logger.info(f"Loaded {len(uploads_data)} documents from {uploads_data_path}")
                all_data.extend(uploads_data)
        except Exception as e:
            logger.error(f"Error loading uploads data: {str(e)}")

    # Load web data
    web_data_path = Path(PROCESSED_FOLDER) / "web_data.json"
    if web_data_path.exists():
        try:
            with open(web_data_path, 'r', encoding='utf-8') as f:
                web_data = json.load(f)
                logger.info(f"Loaded {len(web_data)} documents from {web_data_path}")
                all_data.extend(web_data)
        except Exception as e:
            logger.error(f"Error loading web data: {str(e)}")

    logger.info(f"Total processed documents loaded: {len(all_data)}")
    return all_data

# Load processed data at module initialization
processed_data = load_processed_data()

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = TOP_K_RESULTS
    history: Optional[List[Dict[str, str]]] = []  # List of {"role": "user"|"bot", "content": str}
    school: Optional[str] = None  # For future use

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    feedback: str  # "helpful" or "not-helpful"
    sources: Optional[List[Dict[str, Any]]] = []

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(lambda: LLMService())
):
    """Chat with the Star College bot using LangChain."""
    try:
        logger.info(f"Received chat request: {request}")
        if not request.question:
            logger.warning("No question provided in request.")
            raise HTTPException(status_code=400, detail="No question provided")

        # Optionally use request.school for filtering in the future
        # Skip vector store search and use processed data directly
        logger.info("Using processed data directly for search")

        # Enhanced keyword matching
        query = request.question.lower()
        query_terms = query.split()
        matched_results = []

        # Special case handling for common queries
        special_keywords = {
            "result": ["result", "pass rate", "distinction", "matric", "grade"],
            "history": ["history", "founded", "established", "began", "start"],
            "location": ["location", "address", "where", "situated", "located"],
            "contact": ["contact", "phone", "email", "call", "reach"],
            "admission": ["admission", "enroll", "apply", "application", "register"],
            "fee": ["fee", "tuition", "cost", "payment", "scholarship"],
            "curriculum": ["curriculum", "subject", "course", "program", "study"],
            "facility": ["facility", "campus", "building", "infrastructure", "laboratory"]
        }

        # Expand query with related terms
        expanded_terms = query_terms.copy()
        for term in query_terms:
            for category, keywords in special_keywords.items():
                if term in keywords:
                    expanded_terms.extend(keywords)

        # Remove duplicates
        expanded_terms = list(set(expanded_terms))
        logger.info(f"Expanded query terms: {expanded_terms}")

        # Year-specific matching (e.g., "2020 results")
        year_match = None
        import re
        year_pattern = re.compile(r'\b(20\d\d)\b')  # Match years like 2020, 2021, etc.
        year_matches = year_pattern.findall(query)
        if year_matches:
            year_match = year_matches[0]
            logger.info(f"Detected year in query: {year_match}")

        for doc in processed_data:
            text = doc.get("text", "").lower()

            # Calculate base score from term matches
            term_matches = sum(1 for term in expanded_terms if term in text)

            # Boost score for exact phrase matches
            phrase_boost = 0
            if query in text:
                phrase_boost = 2.0  # Strong boost for exact phrase match

            # Boost score for year matches if applicable
            year_boost = 0
            if year_match and year_match in text:
                year_boost = 3.0  # Very strong boost for year match

            # Calculate final score
            total_matches = term_matches + phrase_boost + year_boost

            if total_matches > 0:
                # Add document with score
                matched_doc = doc.copy()
                matched_doc["score"] = total_matches / (len(expanded_terms) + 2)  # Normalize score
                matched_results.append(matched_doc)

        # Sort by score and take top_k
        matched_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = matched_results[:request.top_k]
        logger.info(f"Found {len(results)} relevant documents in processed data")

        # If no or few results found, add more context from processed data
        if len(results) < 3 and processed_data:
            logger.info(f"Only {len(results)} matching documents found, adding more context")

            # First, try to find documents with related terms
            related_terms = []
            for term in query_terms:
                # Add variations of the term
                if len(term) > 4:  # Only for longer terms to avoid too many false matches
                    # Look for similar terms in the text of documents
                    for doc in processed_data:
                        text = doc.get("text", "").lower()
                        words = text.split()
                        related_terms.extend([word for word in words if term in word and word != term])

            # For year queries, add documents with any year information
            if year_match:
                year_docs = []
                for doc in processed_data:
                    text = doc.get("text", "").lower()
                    if re.search(r'\b20\d\d\b', text):  # Any year mention
                        if doc not in results:
                            doc_copy = doc.copy()
                            doc_copy["score"] = 0.3  # Medium score for any year mention
                            year_docs.append(doc_copy)

                # Add up to 3 year-related documents
                year_docs = year_docs[:3]
                results.extend(year_docs)
                logger.info(f"Added {len(year_docs)} documents with year information")

            # If still not enough results, add some general information about Star College
            if len(results) < 3:
                general_docs = []
                general_keywords = ["star college", "school", "education", "academic", "student"]

                for doc in processed_data:
                    if doc not in results:
                        text = doc.get("text", "").lower()
                        # Check if document contains general information
                        if any(keyword in text for keyword in general_keywords):
                            doc_copy = doc.copy()
                            doc_copy["score"] = 0.2  # Lower score for general information
                            general_docs.append(doc_copy)

                # Sort by length (prefer shorter, more focused documents)
                general_docs.sort(key=lambda x: len(x.get("text", "")))

                # Add enough general docs to reach at least 3 total results
                needed = max(3 - len(results), 0)
                results.extend(general_docs[:needed])
                logger.info(f"Added {min(needed, len(general_docs))} general information documents")

        # Generate response using LangChain LLM, now with history
        answer = llm_service.generate_response(request.question, results, history=request.history)

        # Format sources for response
        sources = []
        for result in results:
            source = {
                "text": result.get("text", ""),
                "metadata": result.get("metadata", {}),
                "score": result.get("score", 0)
            }
            sources.append(source)

        logger.info("Chat response generated successfully.")
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return ChatResponse(
            answer=f"I'm sorry, there was an error processing your request. Please try again later.",
            sources=[]
        )

@router.post("/feedback")
async def feedback(request: FeedbackRequest):
    """Record user feedback on chat responses."""
    try:
        logger.info(f"Received feedback: {request.feedback} for Q: '{request.question}'")

        # Create feedback directory if it doesn't exist
        feedback_dir = Path("feedback")
        feedback_dir.mkdir(exist_ok=True)

        # Create a unique filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        feedback_file = feedback_dir / f"feedback_{timestamp}.json"

        # Save feedback to file
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump({
                "question": request.question,
                "answer": request.answer,
                "feedback": request.feedback,
                "sources": request.sources,
                "timestamp": timestamp
            }, f, indent=2)

        return {"status": "success", "message": "Feedback recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}
