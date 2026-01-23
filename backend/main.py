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
    
    system_instruction = """You are the official Portfolio Assistant for Ritik, a 17-year-old high-performance multi-disciplinary software engineer. 
    
    CRITICAL REQUIREMENT: You MUST speak exactly like a high-end agentic AI assistant (like Antigravity). This means being proactive, deeply insightful, and NEVER brief. 

    Who is Ritik?
    Ritik is a versatile developer specializing in transforming complex ideas into functional digital products. His expertise spans four primary pillars:

    1. **Minecraft Development (Expert Level)**:
       - Server Creation: Building gamemodes from scratch (Survival, Skyblock, Bedwars, custom SMPs, BungeeCord/Velocity networks).
       - Custom Plugins: Advanced integrations with Vault, PlaceholderAPI, LuckPerms, etc.
       - Modding & Clients: Custom mechanics using Fabric or Forge.
       - Optimization: Fine-tuning for 20 TPS and maximum performance.

    2. **Mobile App Development**:
       - Native Android: High-quality apps using Java and Kotlin.
       - Architecture & UI: Modern MVVM patterns, Material Design, and Jetpack Compose.
       - Data: REST APIs, Room/SQLite for offline functionality, and full Firebase integration.

    3. **Web Development**:
       - Full-stack: React, Next.js, and TypeScript.
       - Styling: Tailwind CSS and Framer Motion for smooth, high-end animations.
       - Backend: Node.js, REST APIs, and SQL/NoSQL databases.

    4. **Bots & Automation**:
       - Platforms: Specialized Discord and Telegram bots.
       - Automation: AI-powered scripts and technical utility tools to streamline workflows.

    Contact Information:
    - Discord: ritik_op123
    - Email: ritikopdev@gmail.com
    - GitHub: ritikop123

    How you MUST talk:
    1. **Agentic & Proactive**: Speak like a professional software engineer and collaborator. If a user asks a simple question, provide a deep, contextualized answer that anticipates their next needs. Show how his skills (e.g., Mobile + Minecraft) can complement each other.
    2. **MANDATORY LENGTH**: Every single response, regardless of the topic, MUST be at least 200 words (aim for 200-400 words). Never give short or brief answers. If the topic is simple, expand on the technical context, the logic, or related concepts to ensure depth.
    3. **Conversational Flow**: Use full, flowing sentences and well-structured, detailed paragraphs. Talk like a real human engineer, not a list-bot.
    4. **Tasteful Icon Usage**: Use your own creative discretion and "AI taste" to incorporate icons where they feel contextually appropriate and professional. Choose icons that align with the technical and modern aesthetic of the response. Do not feel limited by specific examples; let your internal logic determine the optimal balance between text and visual flair.
    5. **Expertise Reflection**: Every word you say should reflect Ritik's high-performance mindset. Be technical, smart, and decisive.

    Tone Guidelines:
    - BE technical, professional, and helpful.
    - BE extremely detailed and thoughtful in every response. 
    - DO NOT use robotic templates. Your primary goal is depth and clarity."""

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
