import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from the same directory as this file
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path)

print(f"Loading .env from: {dotenv_path}")
print(f"API Key found: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")

# Initialize FastAPI app
app = FastAPI(title="AI Chat API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    model: Optional[str] = None

class HealthResponse(BaseModel):
    status: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that processes messages using a rotating set of Google Gemini models
    to ensure high availability (Rapid Bot Technique).
    """
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    # Models to rotate through (Rapid Bot Technique)
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3-flash"
    ]
    
    system_instruction = """You are Ritik's portfolio assistant.
You represent Ritik and speak on his behalf.

IMPORTANT: Output CLEAN PLAIN TEXT ONLY.
- NO markdown symbols (#, *, -, •)
- NO HTML tags
- NO raw formatting characters

Structure Rules (The UI needs this specific format to apply styling):
1. Main Title
- First line of your response should be a short, welcoming title (can include ONE emoji)
- Follow with a blank line

2. Sections
- Use standalone lines for Section Titles
- Follow section title with a blank line
- Use short lines under the section for points/details
- Separate sections with blank lines

3. Content Style
- Short introduction sentence after main title
- Plain English, no jargon
- Confident but humble tone
- "I" perspective (representing Ritik)

Example Output Structure:
🚀 Ritik's Portfolio Assistant

I can help you explore Ritik's projects and skills.

Core Skills

Minecraft Server Development
Native Android Apps (Java/Kotlin)
Full-Stack Web Development

Contact Info

Discord: ritik_op123
Email: ritikopdev@gmail.com

(Note: Do not use the exact text above, just the structure. Do not use - or * for lists, just new lines)

About Ritik:
- A young developer focused on performance and clean systems.
- Learning and growing practical problem-solver who knows an impressive amount for his age.
- Perspective: Highly technical but speaks in simple, clear English.

Skills and Knowledge:

Minecraft Development
Server creation (Survival, Skyblock, Bedwars, BungeeCord).
Custom Plugin Development (Vault, PlaceholderAPI, LuckPerms).
Modding with Fabric and Forge.
Server optimization for 20 TPS.

Mobile App Development
Native Android apps using Java and Kotlin.
Modern Architecture (MVVM, Jetpack Compose, Material Design).
Full Firebase integration and local storage (Room, SQLite).

Web Development
Full-stack apps using React, Next.js, and TypeScript.
Modern styling with Tailwind CSS and Framer Motion.
Backend development with Node.js and FastAPI.

Bots and Automation
Specialized Discord and Telegram bot development.
AI-powered scripts and technical utility tools.

Contact:
Discord: ritik_op123
Email: ritikopdev@gmail.com
GitHub: ritikop123"""

    # Ensure API key is loaded (for local dev)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    genai.configure(api_key=api_key)

    last_error = None
    
    for model_name in models_to_try:
        try:
            # Initialize model with system instruction
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            
            # Generate response
            response = model.generate_content(
                request.message,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.75,
                )
            )
            
            return ChatResponse(
                response=response.text,
                model=model_name
            )
            
        except Exception as e:
            last_error = e
            error_message = str(e).lower()
            
            # If it's a safety block or bad request, don't retry other models
            if "safety" in error_message or "blocked" in error_message or "invalid argument" in error_message:
                raise HTTPException(
                    status_code=400,
                    detail=f"Content blocked or invalid request: {str(e)}"
                )
            
            # Continue to next model for rate limits or other server errors
            print(f"Model {model_name} failed, trying next... Error: {str(e)}")
            continue

    # If all models fail, raise the last error
    raise HTTPException(
        status_code=502,
        detail=f"All available Gemini models failed. Last error: {str(last_error)}"
    )

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured.")
    
    genai.configure(api_key=api_key)
    
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-2.5-flash-lite", 
        "gemini-1.5-flash"
    ]

    async def generate():
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                
                # Use stream=True for chunky output
                response = model.generate_content(
                    request.message,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=2000,
                        temperature=0.75,
                    ),
                    stream=True
                )
                
                for chunk in response:
                    if chunk.text:
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                return
            except Exception as e:
                print(f"Streaming model {model_name} failed: {e}")
                continue
        yield f"data: {json.dumps({'error': 'All models failed'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Chat API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat (POST)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Set to False for production
    )
