from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import os

from agent import SYSTEM_PROMPT, run_agent_turn
from summary import generate_call_summary

app = FastAPI(title="Aura Skincare AI Voice Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static folder exists
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatTurnRequest(BaseModel):
    messages: List[Dict[str, Any]]
    user_utterance: str

class ChatTurnResponse(BaseModel):
    agent_utterance: str
    updated_messages: List[Dict[str, Any]]

class EndCallRequest(BaseModel):
    messages: List[Dict[str, Any]]

class EndCallResponse(BaseModel):
    transcript: List[Dict[str, str]]
    structured_summary: Dict[str, Any]

@app.get("/")
def serve_home():
    return FileResponse("static/index.html")

@app.post("/chat/turn", response_model=ChatTurnResponse)
def handle_chat_turn(payload: ChatTurnRequest):
    messages = payload.messages
    if not messages:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    messages.append({"role": "user", "content": payload.user_utterance})
    agent_reply, updated_messages = run_agent_turn(messages)
    
    return ChatTurnResponse(
        agent_utterance=agent_reply,
        updated_messages=updated_messages
    )

@app.post("/chat/end", response_model=EndCallResponse)
def handle_end_call(payload: EndCallRequest):
    transcript = []
    for msg in payload.messages:
        role = msg.get("role")
        content = msg.get("content")
        if role in ["user", "assistant"] and content:
            speaker = "Customer" if role == "user" else "Aria (Agent)"
            transcript.append({"speaker": speaker, "text": content})
            
    summary_data = generate_call_summary(transcript)
    
    return EndCallResponse(
        transcript=transcript,
        structured_summary=summary_data
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "agent": "Aria - Aura Skincare"}