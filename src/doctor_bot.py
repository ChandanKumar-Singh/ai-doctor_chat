import os
import json
from fastapi import HTTPException
from langchain.schema import HumanMessage, SystemMessage
import logging

from src.utils.markdown_formatter import format_markdown_from_json
logging.basicConfig(level=logging.INFO)


USE_OPENAI = os.getenv("USE_OPENAI", "false") == "true"
if USE_OPENAI:
    from src.model.openai import llm
else:
    from src.model.ollama import llm

from src.schemas.pydantic_schemas import DoctorResponse
from src.system_messages.doctor_message import DOCTOR_SYSTEM_PROMPT

def generate_doctor_reply(user_input: str):
    messages = [
        SystemMessage(content=DOCTOR_SYSTEM_PROMPT),
        HumanMessage(content=user_input.strip())
    ]

    content_buffer = ""
    for chunk in llm.stream(messages):
        token = chunk.content
        if token:
            print(token, end="", flush=True)  # stream to console or UI
            content_buffer += token

    logging.info(f"Raw streamed model response: {content_buffer}")

    try:
        parsed = json.loads(content_buffer.strip())
        parsed = parsed.get("response", parsed)  # unwrap if nested

        return DoctorResponse(
            summary=parsed.get("summary", "We couldn't generate a summary. Please consult a medical professional."),
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
        raise HTTPException(status_code=500, detail="Invalid JSON from model")


# def generate_doctor_reply(user_input: str):
#     messages = [
#         SystemMessage(content=DOCTOR_SYSTEM_PROMPT),
#         HumanMessage(content=user_input.strip())
#     ]
#     response = llm.invoke(messages)
#     logging.info(f"Raw model response: {response.content}")

#     try:
#         parsed = json.loads(response.content.strip())
#         parsed = parsed.get("response", parsed)  # unwrap if nested

#         # Fill in default structure if any part is missing
#         return DoctorResponse(
#             summary=parsed.get("summary", "We couldn't generate a summary. Please consult a medical professional."),
#             confidence_level=parsed.get("confidence_level", "low"),
#             possible_conditions=parsed.get("possible_conditions", []),
#             recommended_care=parsed.get("recommended_care", {
#                 "self-care": ["Get rest and stay hydrated."],
#                 "medications": [],
#                 "lifestyle": []
#             }),
#             urgent_flags=parsed.get("urgent_flags", []),
#             disclaimer=parsed.get("disclaimer", "This is not medical advice. Always consult a licensed doctor.")
#         )

#     except json.JSONDecodeError:
#         raise HTTPException(status_code=500, detail="Invalid JSON from model")


from fastapi.responses import StreamingResponse


def stream_doctor_reply(user_input: str) -> StreamingResponse:
    """
    Streams a doctor-style AI response in real-time, formatted as JSON.

    This function takes a user's medical-related query, processes it through an LLM 
    (configured with a doctor persona system prompt), and streams the response 
    incrementally in a JSON-compatible format. The response is escaped for proper 
    JSON formatting and streamed for low-latency display in web interfaces.

    Args:
        user_input (str): The user's medical query or conversation input. 
                          Leading/trailing whitespace is automatically stripped.

    Returns:
        StreamingResponse: A FastAPI/Starlette streaming response with:
                          - Media type: application/json
                          - Chunked encoding of the LLM's output
                          - Properly escaped JSON structure:
                            {
                              "response": {
                                "raw": "AI's generated text here..."
                              }
                            }

    Example Client-Side Handling:
        ```javascript
        const response = await fetch('/doctor-chat', {method: 'POST', body: userInput});
        const reader = response.body.getReader();
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            console.log(new TextDecoder().decode(value));
        }
        ```
    """
    messages = [
        SystemMessage(content=DOCTOR_SYSTEM_PROMPT),  # Pre-configured doctor persona
        HumanMessage(content=user_input.strip())      # Sanitized user input
    ]

    # def token_generator():
    #     """Yields JSON-wrapped tokens for streaming response."""
    #     yield '{"response":{"raw": "'
    #     for chunk in llm.stream(messages):
    #         token = chunk.content
    #         if token:
    #             safe_token = token.replace('"', '\\"')  # JSON escape
    #             yield safe_token
    #     yield '"}}'  # Close JSON structure

    # return StreamingResponse(
    #     token_generator(),
    #     media_type="application/json"
    # )
    async def event_stream():
        full_content = ""
        async for chunk in llm.astream(messages):  # ⬅️ use `astream` for async streaming
            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end="", flush=True)  # Real-time console output
                yield chunk.content
                # At the end, emit formatted markdown
                # full_content += chunk.content
                # markdown = format_markdown_from_json(chunk.content)
                # yield f"{markdown}"

    return StreamingResponse(event_stream(), media_type="text/plain")