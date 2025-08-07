from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse 
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Medical AI Chatbot",
    version="1.0.0",
    description="World-class AI medical assistant powered by Ollama",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Serve static files for demo UI
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and initialize DoctorBot
from doctor_bot import doctor_bot
from schemas.pydantic_schemas import DoctorResponse, DoctorResponseWrapped

class Prompt(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

@app.get("/health-check", response_model=ChatResponse)
def health_check():
    return {"response": "✅ Medical AI Chatbot is running."}

@app.get("/api/models")
def get_available_models():
    """List available models on the Ollama server"""
    try:
        import requests
        response = requests.get(f"{os.getenv('OLLAMA_BASE_URL')}/api/tags")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Ollama: {str(e)}")

@app.get("/api/chat-stream")
async def chat_get(q: str):
    return StreamingResponse(
        doctor_bot.stream_reply(q),
        media_type="text/plain"
    )

@app.get("/chat", response_model=DoctorResponseWrapped)
async def chat_get(q: str = Query(..., description="Health question to ask the AI doctor")):
    reply = await doctor_bot.generate_reply(q)
    return {"response": reply}

@app.post("/chat", response_model=ChatResponse)
async def chat(prompt: Prompt):
    reply = await doctor_bot.generate_reply(prompt.query)
    return {"response": reply.dict()}  # Convert DoctorResponse to dict

@app.post("/diagnose", response_model=ChatResponse)
async def diagnose(prompt: Prompt):
    query = f"Diagnose this: {prompt.query}"
    reply = await doctor_bot.generate_reply(query)
    return {"response": reply.dict()}

@app.post("/symptoms", response_model=ChatResponse)
async def symptom_checker(prompt: Prompt):
    query = f"What conditions might be related to these symptoms: {prompt.query}?"
    reply = await doctor_bot.generate_reply(query)
    return {"response": reply.dict()}

@app.post("/upload", response_model=ChatResponse)
async def upload(query: str = Form(...), file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    contents = await file.read()
    file_summary = f"Received attachment: {file.filename} ({len(contents)} bytes)"
    full_prompt = f"{query}\n\nAlso attached: {file_summary}"
    reply = await doctor_bot.generate_reply(full_prompt)
    return {"response": reply.dict()}

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
    reply = await doctor_bot.generate_reply(full_prompt)
    return {"response": reply.dict()}