from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
from config import config
from ai_service import ai_service

# Validate configuration
config.validate()

app = FastAPI(title="Portfolio AI Chatbot API")

# CORS middleware - Allow all for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins to rule out CORS issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str

@app.get("/")
async def root():
    return {"message": "Portfolio AI Chatbot API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Handle chat messages and return AI response
    """
    try:
        print(f"Received chat request: {request.message}")
        # Convert conversation history to dict format
        history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
        
        # Get AI response
        response = await ai_service.chat(request.message, history)
        
        from datetime import datetime
        return ChatResponse(
            response=response,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream AI responses for real-time updates
    """
    print(f"Received stream request: {request.message}")
    async def generate():
        try:
            # Convert conversation history to dict format
            history = [{"role": msg.role, "content": msg.content} for msg in request.conversation_history]
            
            # Stream AI response
            async for chunk in ai_service.chat_stream(request.message, history):
                import json
                # JSON encode the chunk to ensure newlines/quotes don't break SSE format
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming
            
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
