from typing import List, Dict, Any
import requests
import json

from langchain_community.llms import HuggingFaceHub

from app.config import HUGGINGFACE_API_KEY, DEEPSEEK_API_KEY, LLM_MODEL

class LLMService:
    """Service for interacting with the LLM using DeepSeek API."""

    def __init__(self):
        self.huggingface_api_key = HUGGINGFACE_API_KEY
        self.deepseek_api_key = DEEPSEEK_API_KEY
        self.model_name = LLM_MODEL
        self.llm = None
        self.qa_chain = None

        # Check if DeepSeek API key is available
        if self.deepseek_api_key:
            print("DeepSeek API key found. Will use DeepSeek API for generation.")
        else:
            # Initialize the Hugging Face LLM if API key is available
            if self.huggingface_api_key:
                self._initialize_huggingface_llm()

    def _initialize_huggingface_llm(self):
        """Initialize the LangChain LLM with Hugging Face."""
        try:
            self.llm = HuggingFaceHub(
                huggingfacehub_api_token=self.huggingface_api_key,
                repo_id=self.model_name,
                model_kwargs={
                    "temperature": 0.7,
                    "max_new_tokens": 512,
                    "top_p": 0.95,
                    "repetition_penalty": 1.1
                }
            )
            print(f"Initialized Hugging Face LLM: {self.model_name}")
        except Exception as e:
            print(f"Error initializing Hugging Face LLM: {str(e)}")
            self.llm = None

    def _call_deepseek_api(self, prompt: str, messages: List[Dict[str, str]] = None) -> str:
        """Call the DeepSeek API to generate a response."""
        try:
            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }

            # If messages are provided, use them directly
            # Otherwise, create a single message with the prompt
            if not messages:
                messages = [{"role": "user", "content": prompt}]

            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.5,  # Lower temperature for more focused, predictable responses
                "max_tokens": 300,   # Limit token count to encourage brevity
                "top_p": 0.9,
                "presence_penalty": 0.2,  # Increased penalty to reduce repetition
                "frequency_penalty": 0.2   # Increased penalty to encourage simpler vocabulary
            }

            print("Generating response...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(data),
                timeout=30  # Add timeout to prevent hanging
            )

            if response.status_code != 200:
                print(f"Error: API returned status code {response.status_code}")
                return f"Error from DeepSeek API: Status code {response.status_code}. Please try again later."

            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                print(f"Generated answer length: {len(answer)} characters")
                return answer
            else:
                print("No choices in DeepSeek API response")
                return "Error: No response generated from DeepSeek API."

        except Exception as e:
            print(f"Error calling DeepSeek API: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error calling DeepSeek API: {str(e)}"

    def generate_response(self, query: str, context: List[Dict[str, Any]], history: List[Dict[str, str]] = None) -> str:
        """Generate a dynamic, thoughtful response to the query using the provided context and conversation history."""
        # Always proceed with the available context, even if it's empty
        # This ensures we use the processed data

        # Format context for the prompt
        formatted_context = self._format_context(context)

        # Prepare messages for the chat API
        messages = []

        # System message with instructions
        system_message = {
            "role": "system",
            "content": """You are a concise and helpful assistant for Star College in Durban, South Africa.
Your purpose is to provide short, precise, and straightforward responses to questions about the school.

IMPORTANT GUIDELINES:
1. NEVER say you don't have information unless the context is completely unrelated to education or schools.
2. Base your answers primarily on the provided context information.
3. When the context doesn't contain exact information, provide a helpful response based on related information.
4. For specific queries (like "2020 results"), if you don't have exact data, provide the closest available information and clearly state what year it's from.
5. If asked about results or achievements, mention any performance data you can find in the context.
6. Keep all responses SHORT and TO THE POINT - typically 1-3 sentences.
7. Use simple, clear language without academic or flowery phrasing.
8. Answer directly what was asked without adding tangential information.

Remember: Your goal is to be helpful by providing the most relevant information available, even if it's not a perfect match for the query."""
        }
        messages.append(system_message)

        # Add conversation history if available
        if history:
            # Only include the last few turns to keep context manageable
            recent_history = history[-6:] if len(history) > 6 else history
            for turn in recent_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                # Map 'bot' role to 'assistant' for the API
                api_role = "assistant" if role == "bot" else role
                messages.append({"role": api_role, "content": content})

        # Add the context and current query as the final user message
        user_message = f"""Question: {query}

Here is the relevant information about Star College to help you answer:

{formatted_context}

IMPORTANT: Even if the information doesn't perfectly match the question, provide a helpful response using what's available. For example, if asked about "2020 results" but you only have data from 2019 or 2021, provide that information and specify the year.

Please provide a short, direct answer (1-3 sentences) based on this information. Be extremely concise but informative."""

        messages.append({"role": "user", "content": user_message})

        try:
            if self.deepseek_api_key:
                # Pass the full messages array to the API
                return self._call_deepseek_api("", messages=messages)
            elif self.llm:
                # For HuggingFace, we need to format as a single prompt
                formatted_messages = ""
                for msg in messages:
                    role = msg["role"].capitalize()
                    content = msg["content"]
                    formatted_messages += f"{role}: {content}\n\n"

                response = self.llm.invoke(formatted_messages)
                return response
            else:
                # Fallback if no LLM is available
                response = "Based on the information I have about Star College:\n\n"
                for item in context[:3]:  # Include more context
                    text = item.get("text", "").strip()
                    if text:
                        response += f"- {text}\n\n"
                return response
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I'm sorry, I encountered an error while generating a response. Please try again later."

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format the context for the prompt."""
        formatted_chunks = []

        for i, item in enumerate(context):
            text = item.get("text", "")
            source = self._format_source(item)
            formatted_chunks.append(f"[{i+1}] {text}\nSource: {source}")

        return "\n\n".join(formatted_chunks)

    def _format_source(self, item: Dict[str, Any]) -> str:
        """Format the source information."""
        metadata = item.get("metadata", {})
        source_type = metadata.get("source_type", "unknown")

        if source_type == "file":
            file_type = metadata.get("file_type", "document")
            filename = metadata.get("filename", "unknown")
            page = metadata.get("page", "")

            if page:
                return f"{file_type.upper()}: {filename}, Page {page}"
            else:
                return f"{file_type.upper()}: {filename}"

        elif source_type == "web":
            url = metadata.get("url", "unknown")
            title = metadata.get("title", "")

            if title:
                return f"WEB: {title} ({url})"
            else:
                return f"WEB: {url}"

        else:
            return "Unknown source"
