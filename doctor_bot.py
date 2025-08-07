import os
import json
from fastapi import HTTPException
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
import logging
from dotenv import load_dotenv
from typing import Optional

from schemas.pydantic_schemas import DoctorResponse
from system_messages.doctor_message import DOCTOR_SYSTEM_PROMPT
from utils.logger import setup_logging

load_dotenv()
setup_logging()

class DoctorBot:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.system_prompt = DOCTOR_SYSTEM_PROMPT

    async def generate_reply(self, user_input: str) -> DoctorResponse:
        """Generate a structured medical response"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input.strip())
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            return self._parse_response(response.content)
        except Exception as e:
            logging.error(f"Error generating doctor reply: {str(e)}")
            raise HTTPException(status_code=500, detail="Error processing your request")

    async def stream_reply(self, user_input: str):
        """Stream response in real-time"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input.strip())
        ]
        
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                print(chunk.content)
                yield chunk.content

    def _parse_response(self, content: str) -> DoctorResponse:
        """Parse and validate the LLM response"""
        try:
            parsed = json.loads(content.strip())
            parsed = parsed.get("response", parsed)
            
            return DoctorResponse(
                summary=parsed.get("summary", "Unable to generate summary. Please consult a healthcare professional."),
                confidence_level=parsed.get("confidence_level", "low"),
                possible_conditions=parsed.get("possible_conditions", []),
                recommended_care=parsed.get("recommended_care", {
                    "self-care": ["Get rest and stay hydrated."],
                    "medications": [],
                    "lifestyle": []
                }),
                urgent_flags=parsed.get("urgent_flags", []),
                disclaimer=parsed.get("disclaimer", "This is not medical advice. Always consult a licensed doctor.")
            )
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid response format from AI model")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing AI response: {str(e)}")

# Initialize with configured LLM
from model.ollama import llm as ollama_llm
doctor_bot = DoctorBot(ollama_llm)