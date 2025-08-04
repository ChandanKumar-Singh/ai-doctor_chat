from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from src.doctor_bot import generate_doctor_reply, stream_doctor_reply
from src.schemas.pydantic_schemas import DoctorResponse, DoctorResponseWrapped

app = FastAPI(title="Medical AI Chatbot", version="1.0.0")
# Allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 👈 or ["*"] for all origins (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Prompt(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

@app.get("/health-check", response_model=ChatResponse)
def health_check():
    return {"response": "✅ Medical AI Chatbot is running."}

@app.get("/chat-stream")
def chat_get(q: str):
    return stream_doctor_reply(q)

@app.get("/chat", response_model=DoctorResponseWrapped)
def chat_get(q: str = Query(..., description="Health question to ask the AI doctor")):
    reply = generate_doctor_reply(q)
    return {"response": reply}

@app.post("/chat", response_model=ChatResponse)
def chat(prompt: Prompt):
    reply = generate_doctor_reply(prompt.query)
    return {"response": reply}

@app.post("/diagnose", response_model=ChatResponse)
def diagnose(prompt: Prompt):
    query = f"Diagnose this: {prompt.query}"
    reply = generate_doctor_reply(query)
    return {"response": reply}

@app.post("/symptoms", response_model=ChatResponse)
def symptom_checker(prompt: Prompt):
    query = f"What conditions might be related to these symptoms: {prompt.query}?"
    reply = generate_doctor_reply(query)
    return {"response": reply}

@app.post("/upload", response_model=ChatResponse)
async def upload(query: str = Form(...), file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    contents = await file.read()
    file_summary = f"Received attachment: {file.filename} ({len(contents)} bytes)"
    full_prompt = f"{query}\n\nAlso attached: {file_summary}"
    reply = generate_doctor_reply(full_prompt)
    return {"response": reply}

@app.post("/multi-upload", response_model=ChatResponse)
async def multi_upload(query: str = Form(...), files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    attachment_descriptions = []
    for file in files:
        contents = await file.read()
        attachment_descriptions.append(f"{file.filename} ({len(contents)} bytes)")

    file_summary = "\n".join(attachment_descriptions)
    full_prompt = f"{query}\n\nAttachments:\n{file_summary}"
    reply = generate_doctor_reply(full_prompt)
    return {"response": reply}
