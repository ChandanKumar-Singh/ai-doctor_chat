from langchain_community.chat_models import ChatOllama
from langchain_core import language_models

llm = ChatOllama(
    # model="phi",  # or "mistral", etc.
    model="phi3",
    # model="mistral",
    temperature=0.2,
    stream=True,
    # Only include supported options
    request_timeout=60,
    stop=["</s>"],  # Optional
    format="json",  # Optional; use "json" or "text" based on your model
)
