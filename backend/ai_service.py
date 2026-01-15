import google.generativeai as genai
from config import config
from typing import List, Dict

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

# Generation config to limit quota usage
generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 400, # Limit response size to save quota
}

# System prompt with portfolio context + General capabilities
SYSTEM_PROMPT = """
You are the official AI Portfolio Assistant for Ritik.
IMPORTANT: You were created by Ritik to represent him on his portfolio website.

**Your Persona:**
- You are helpful, smart, and witty.
- You are primarily here to showcase Ritik's work, BUT you are also a capable general-purpose AI.
- If asked about Math, Physics, Coding, or Science: ANSWER IT CORRECTLY. You are a "Developer's AI", so you know code and science.
- If asked personal questions about unrelated people, politely redirect to Ritik.

**Ritik's Profile:**
- **Role:** Full-Stack Developer & Software Engineer
- **Specialty:** Web Apps (React, Next.js), Backends (FastAPI, Node.js), and Minecraft Development (Java/Kotlin).
- **Projects:** Quantum Anti-Cheat, AI Portfolio, Discord Bots.

**Guidelines:**
1. **Be Concise:** Keep answers under 4-5 sentences unless asked for a long explanation.
2. **General Topics:** If someone asks "Write a Python script for a calculator" or "What is gravity?", DO IT. Show off your intelligence.
3. **Identity:** If asked "Who made you?", answer: "I was built by Ritik using Python and the Gemini API."
"""

class AIService:
    def __init__(self):
        # Priority list of models to try
        self.available_models = [
            "gemini-1.5-flash",
            "gemini-1.0-pro", 
            "gemini-1.5-pro"
        ]
            
    def _get_model(self, model_name: str):
        return genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

    async def chat(self, message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Send a message to Gemini and get a response, with automatic fallback
        """
        for model_name in self.available_models:
            print(f"🤖 Attempting to use model: {model_name}")
            try:
                model = self._get_model(model_name)
                # Prepare the chat session
                chat = model.start_chat(history=[])
                
                # Construct the full prompt context
                full_prompt = f"{SYSTEM_PROMPT}\n\n"
                
                # Add conversation history context manually to ensure it's respected
                if conversation_history:
                    full_prompt += "Conversation Context:\n"
                    for msg in conversation_history:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        full_prompt += f"{role}: {msg['content']}\n"
                
                full_prompt += f"\nUser: {message}\nAssistant:"
                
                # Get response
                response = chat.send_message(full_prompt)
                return response.text
                
            except Exception as e:
                error_str = str(e).lower()
                # Check for rate limit or quota errors
                if "429" in error_str or "quota" in error_str or "resource exhausted" in error_str:
                    print(f"⚠️ Model {model_name} hit rate limit. Switching...")
                    continue # Try next model
                
                print(f"❌ Error in AI service with {model_name}: {e}")
                # For other errors, we might still want to try next model just in case, 
                # or technically we could break. Let's continue to be safe.
                continue

        # If we exhausted all models
        return "The AI is currently overloaded. Please try again in 1 minute."
    
    async def chat_stream(self, message: str, conversation_history: List[Dict[str, str]] = None):
        """
        Stream responses from Gemini for real-time updates, with fallback
        """
        for model_name in self.available_models:
            print(f"🤖 (Stream) Attempting to use model: {model_name}")
            try:
                model = self._get_model(model_name)
                # Prepare the chat session
                chat = model.start_chat(history=[])
                
                # Construct the full prompt context
                full_prompt = f"{SYSTEM_PROMPT}\n\n"
                
                if conversation_history:
                    full_prompt += "Conversation Context:\n"
                    for msg in conversation_history:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        full_prompt += f"{role}: {msg['content']}\n"
                
                full_prompt += f"\nUser: {message}\nAssistant:"
                
                # Stream response
                response = chat.send_message(full_prompt, stream=True)
                
                # If we successfully start streaming, yield chunks
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                
                return # Success! Exit function.
                    
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str or "resource exhausted" in error_str:
                    print(f"⚠️ (Stream) Model {model_name} hit rate limit. Switching...")
                    continue # Try next model
                
                print(f"❌ (Stream) Error with {model_name}: {e}")
                continue # Try next model
                
        # If all models failed
        yield "Error: The AI is currently overloaded. Please try again later."
    
# Create singleton instance
ai_service = AIService()
