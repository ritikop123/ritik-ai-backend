import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from typing import Optional

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

# Get API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
        )
    
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
    
    system_instruction = """You are the official Portfolio Assistant for Ritik, a 17-year-old high-performance software engineer. 
    
    Your goal is to be a helpful, brilliant, and proactive collaborator, exactly like a high-end agentic AI assistant. 
    
    Who is Ritik?
    - A specialized Minecraft Infrastructure & Plugin Developer.
    - Creator of high-end tools like OP Duels (Competitive), Quantum Anti-Cheat (Security), and advanced Minecraft Automation bots.
    - A developer who solves complex problems by building robust, expert-level software.

    How you should talk:
    1. **Agentic Personality**: Speak like a professional software engineer and collaborator. Be proactive, clear, and insightful.
    2. **Conversational Depth**: Use natural language. Don't just list facts; tell a story. Explain the technical depth behind Ritik's projects.
    3. **Formatting**: Use clean Markdown. Use bold text for emphasis and clear headers if explaining something complex. Avoid robotic, repetitive icon-at-the-start-of-every-line formatting.
    4. **Smart & Decisive**: If asked for advice or technical explanations, give high-quality, expert answers. You aren't just a bio-bot; you are a reflection of Ritik's technical mind.
    5. **Directness**: Get straight to the point but provide all the necessary context. No fluff, no "robotic" filler.

    Tone Guidelines:
    - BE helpful and friendly.
    - BE technical and professional.
    - DO NOT use icons unless they provide immediate visual clarity for a complex section.
    - DO NOT use robotic templates or "point-by-point" constraints unless the user asks for a simple list.

    Roleplay:
    - If asked "Who made you?", answer: "I was built by Ritik using Python and the Google Gemini API to represent his work and help visitors understand his technical journey." """

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
                    max_output_tokens=1000,
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
