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

    def _call_deepseek_api(self, prompt: str) -> str:
        """Call the DeepSeek API to generate a response."""
        try:
            print(f"Calling DeepSeek API with API key: {self.deepseek_api_key[:5]}...{self.deepseek_api_key[-5:]}")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.deepseek_api_key}"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.95
            }

            print("Sending request to DeepSeek API...")
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(data),
                timeout=30  # Add timeout to prevent hanging
            )

            print(f"DeepSeek API response status code: {response.status_code}")

            if response.status_code != 200:
                print(f"Error response from DeepSeek API: {response.text}")
                return f"Error from DeepSeek API: Status code {response.status_code}. Please try again later."

            result = response.json()
            print(f"DeepSeek API response: {json.dumps(result)[:200]}...")

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
        """Generate a clear, concise response to the query using the provided context and conversation history."""
        if not context:
            return "I don't have enough information to answer that question about Star College. Please try asking something else or upload more information about the school."

        # Format context for the prompt
        formatted_context = self._format_context(context)

        # Format conversation history
        formatted_history = ""
        if history:
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if role == "user":
                    formatted_history += f"User: {content}\n"
                else:
                    formatted_history += f"Bot: {content}\n"

        # New concise prompt
        prompt = f"""You are a helpful assistant for Star College in Durban. Answer the user's question based ONLY on the provided context.\nIf you don't know the answer based on the context, say \"I don't have enough information to answer that question about Star College.\"\nDo not make up information or use knowledge outside of the provided context.\n\nBe concise and clear. Only provide the most relevant information in your answer. Do not include everything from the context unless the user specifically asks for more details. Avoid long answers unless absolutely necessary.\n\nConversation history:\n{formatted_history}\nContext:\n{formatted_context}\n\nQuestion: {query}\n\nShort, clear answer:"""

        try:
            if self.deepseek_api_key:
                return self._call_deepseek_api(prompt)
            elif self.llm:
                response = self.llm.invoke(prompt)
                return response
            else:
                response = "Based on the information I have about Star College:\n\n"
                for item in context[:1]:  # Only the most relevant
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
