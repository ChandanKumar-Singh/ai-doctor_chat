from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
import os
from dotenv import load_dotenv

load_dotenv()

def get_ollama_llm() -> BaseChatModel:
    model=os.getenv("OLLAMA_MODEL", "phi3"),
    print(model)
    """Create and return a properly configured Ollama LLM instance"""
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "phi3"),
        temperature=0.2,
        streaming=False,
        request_timeout=60,
        stop=["</s>"],
        format="json",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )

# Initialize the LLM instance
llm = get_ollama_llm()