from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

from app.ingestion import store
from app.agent import graph
from app.actions import confirm_action, reject_action
from app.analytics import detect_proactive_issues
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

app = FastAPI(title="ParcelPilot AI Support Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ParcelPilot API is running. Please access the frontend UI."}

@app.get("/api/health")
def health_check():
    return "OK"

@app.on_event("startup")
def startup_event():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    resource_dir = os.path.join(base_dir, "resourcePack")
    store.load(resource_dir)
    print(f"Loaded {len(store.accounts)} accounts, {len(store.orders)} orders, {len(store.tickets)} tickets.")

class ChatRequest(BaseModel):
    message: str
    user: Dict[str, Any]
    history: List[Dict[str, Any]] = []

@app.post("/api/chat")
def chat(req: ChatRequest):
    messages = []
    for h in req.history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        elif h["role"] == "assistant":
            messages.append(AIMessage(content=h["content"]))
            
    messages.append(HumanMessage(content=req.message))
    
    state = {"messages": messages, "user": req.user}
    
    import time
    start_time = time.time()

    # Run langgraph
    result = graph.invoke(state)
    final_messages = result["messages"]
    
    tool_activity = []
    action_payload = None
    for m in final_messages[len(messages):]: # Only look at new messages
        if isinstance(m, AIMessage) and getattr(m, 'tool_calls', None):
            for tc in m.tool_calls:
                tool_activity.append({"tool": tc["name"], "args": tc["args"]})
        if isinstance(m, ToolMessage):
            try:
                import json
                parsed = json.loads(m.content)
                if isinstance(parsed, dict) and parsed.get("status") == "PENDING_CONFIRMATION":
                    action_payload = parsed
            except Exception:
                pass
                
    last_msg = final_messages[-1]
    
    latency = time.time() - start_time
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f"Chat request by user {req.user['id']} ({req.user.get('role')}) - Tools: {[t['tool'] for t in tool_activity]} - Latency: {latency:.2f}s")
    
    return {
        "reply": last_msg.content if isinstance(last_msg, AIMessage) else str(last_msg),
        "tool_activity": tool_activity,
        "action": action_payload
    }

class ActionRequest(BaseModel):
    action_id: str

@app.post("/api/action/confirm")
def api_confirm_action(req: ActionRequest):
    return confirm_action(req.action_id)

@app.post("/api/action/reject")
def api_reject_action(req: ActionRequest):
    return reject_action(req.action_id)

@app.get("/api/analytics")
def api_analytics():
    return {"issues": detect_proactive_issues()}
