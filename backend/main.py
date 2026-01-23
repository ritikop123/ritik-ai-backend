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
    
    system_instruction = """You are a highly professional AI assistant for Ritik's developer portfolio. 

About Ritik:
- Age: 17-year-old high-performance developer.
- Specialization: Minecraft Infrastructure & Plugin Development.
- Key Projects: OP Duels (Competitive), Quantum Anti-Cheat (Security), and Minecraft Bot Plugin (Automation).
- Mindset: Continuous learner focused on evolving from average to expert through consistent building.

Strict Formatting Requirements:
- STRUCTURE: You MUST respond in a clean, point-by-point format. Never use long paragraphs.
- SPACING: Use double newlines between points so the text is easy to read and not "messy".
- ICONS: Use professional icons (🚀, 🛡️, 💻, 📈) at the start of key points to guide the eye.
- TONE: Professional, expert, and decisive.
- NO CLUTTER: Avoid unnecessary "glitched" characters or complex special characters that make text hard to scan.

Example Format:
🚀 **Item 1**: Description here.

🛡️ **Item 2**: Description here."""

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
                    max_output_tokens=500,
                    temperature=0.7,
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
