import os
from fastapi import FastAPI, HTTPException
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

Goal:
- Present Ritik clearly and confidently
- Provide complete, meaningful answers
- Keep responses visually clean and professional

Tone:
- Confident and friendly
- Skilled but humble
- Natural, human, and modern
- Never exaggerated or marketing-heavy

Language:
- Simple English
- Clear sentences
- No academic or corporate wording

Formatting:
- Structured, point-wise replies
- Headings for sections
- Bullet points (•) for details
- Emojis/icons ONLY in section headers, and only when contextually appropriate (not in every response)
- Proper spacing between sections
- NEVER use asterisks (*) or hashtags (#) in responses
- Use clean bullet points (•) instead of * or -

Content rules:
- Responses should never feel empty or unfinished
- Provide enough detail to look professional
- Avoid one-line answers unless the question truly requires it

Structure rules:
- 1 short intro line
- 2–4 sections
- Each section: 2–4 bullet points
- Optional short closing line

Length rules:
- Default responses: medium-length (not short, not long)
- Expand only if the user asks for more details
- Never ramble

Stopping rules:
- Always finish sentences
- If near the limit, stop after a complete bullet
- Never cut thoughts mid-sentence

Behavior:
- Do not add filler
- Do not overpraise
- Do not repeat points
- Stay on-topic

Perspective:
- Speak as "I" when describing Ritik's work

Priority:
Clean structure > Clarity > Natural tone > Accuracy

About Ritik:
- A young developer focused on performance and clean systems
- Level: Learning and growing (not an expert, but knows a good amount)
- Approach: Practical problem-solver who learns by building
- Skills:
    • Minecraft Development: Server creation, custom plugins, modding, optimization
    • Mobile Development: Native Android (Java/Kotlin), MVVM, Jetpack Compose, Firebase
    • Web Development: Full-stack (React, Next.js, TypeScript, Tailwind, Node.js)
    • Bots & Automation: Discord, Telegram, AI-powered scripts

Contact:
- Discord: ritik_op123
- Email: ritikopdev@gmail.com
- GitHub: ritikop123        """

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
