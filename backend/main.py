from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import time
import hashlib
from backend.config import config
from ai_service import ai_service

# Validate configuration
config.validate()

app = FastAPI(title="Portfolio AI Chatbot API")

# CORS middleware - Allow all for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Memory Optimization & Protection ---
# Simple in-memory cache: {query_hash: response_text}
RESPONSE_CACHE = {} 
# Rate limiting: {ip_address: last_request_timestamp}
RATE_LIMITS = {} 

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str

def get_client_ip(request: Request):
    """Get real IP behind proxies (Render/Cloudflare)"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

def is_spam(message: str) -> bool:
    """Basic spam filters"""
    if not message or not message.strip():
        return True
    if len(message) > 500: # Limit input length
        return True
    if len(set(message)) < 5 and len(message) > 10: # Repeated characters check (e.g. "aaaaa")
        return True
    return False

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Limit users to 1 request every 3 seconds to save Free Tier quota.
    """
    if request.url.path.startswith("/api/chat"):
        client_ip = get_client_ip(request)
        current_time = time.time()
        
        last_request = RATE_LIMITS.get(client_ip, 0)
        if current_time - last_request < 3.0: # 3 Seconds cooldown
            # Calculate wait time
            wait_time = int(3.0 - (current_time - last_request))
            return StreamingResponse(
                iter([f"data: Error: Please wait {wait_time} seconds before sending another message.\n\n"]),
                media_type="text/event-stream"
            )
            
        RATE_LIMITS[client_ip] = current_time
        
        # Cleanup old rate limits occasionally (simple logic)
        if len(RATE_LIMITS) > 1000:
            RATE_LIMITS.clear()

    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {"message": "Portfolio AI Chatbot API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/chat")
async def chat(request: ChatRequest, req: Request):
    """
    Handle chat messages and return AI response
    """
    try:
        # Spam Check
        if is_spam(request.message):
             raise HTTPException(status_code=400, detail="Invalid message detected.")

        # Cache Check (Only for requests without history to ensure context isn't lost)
        msg_hash = hashlib.md5(request.message.lower().strip().encode()).hexdigest()
        if not request.conversation_history and msg_hash in RESPONSE_CACHE:
            from datetime import datetime
            print(f"Serving from cache: {request.message}")
            return ChatResponse(
                response=RESPONSE_CACHE[msg_hash],
                timestamp=datetime.utcnow().isoformat()
            )

        print(f"Received chat request: {request.message}")
        history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
        
        response = await ai_service.chat(request.message, history)
        
        # Save to cache if short enough (don't cache massive essays)
        if not request.conversation_history and len(response) < 1000:
            RESPONSE_CACHE[msg_hash] = response
        
        from datetime import datetime
        return ChatResponse(
            response=response,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    """
    Stream AI responses for real-time updates
    """
    # Spam Check
    if is_spam(request.message):
        async def spam_msg():
             yield "data: Error: Message blocked by spam filter.\n\n"
        return StreamingResponse(spam_msg(), media_type="text/event-stream")

    # Cache Check (Only if no history)
    msg_hash = hashlib.md5(request.message.lower().strip().encode()).hexdigest()
    if not request.conversation_history and msg_hash in RESPONSE_CACHE:
        print(f"Serving stream from cache: {request.message}")
        async def cached_generator():
            await asyncio.sleep(0.1) # Simulate slight network delay
            import json
            yield f"data: {json.dumps(RESPONSE_CACHE[msg_hash])}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(cached_generator(), media_type="text/event-stream")

    print(f"Received stream request: {request.message}")
    
    async def generate():
        full_response = ""
        try:
            history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
            
            async for chunk in ai_service.chat_stream(request.message, history):
                import json
                full_response += chunk
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.01)
            
            # Cache the full response after successful generation
            if not request.conversation_history and len(full_response) < 1000:
                RESPONSE_CACHE[msg_hash] = full_response
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"Error in stream endpoint: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

