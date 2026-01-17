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
    "max_output_tokens": 800, # Increased to allow for ~500 word responses
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
1. **Response Length:** Provide detailed, helpful answers (aim for 200-400 words). Do not simply be brief. However, keep it under 500 words.
2. **Formatting:** Use normal sentence casing. Do NOT spam uppercase letters (caps) for emphasis or yelling. Use bold or italics if emphasis is needed.
3. **General Topics:** If someone asks "Write a Python script for a calculator" or "What is gravity?", DO IT. Show off your intelligence.
4. **Identity:** If asked "Who made you?", answer: "I was built by Ritik using Python and the Gemini API."
"""

class AIService:
    def __init__(self):
        # Priority list of models to try
        self.available_models = [
            "gemini-1.5-flash",
            "gemini-1.0-pro", 
            "gemini-1.5-pro"
        ]
        self.current_model_index = 0

            
    def _get_model(self, model_name: str):
        return genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

    async def chat(self, message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        send a message to Gemini and get a response, with automatic fallback
        """
        # Try models starting from the current index, cycling through all of them once
        start_index = self.current_model_index
        num_models = len(self.available_models)
        
        for i in range(num_models):
            # Calculate actual index ensuring we wrap around
            idx = (start_index + i) % num_models
            model_name = self.available_models[idx]
            
            print(f"🤖 Attempting to use model: {model_name}" + (" (Fallback)" if i > 0 else ""))
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
                if "429" in error_str or "quota" in error_str or "resource exhausted" in error_str:
                    print(f"⚠️ Model {model_name} hit rate limit. Switching...")
                    # Update sticky index to next model for future requests
                    self.current_model_index = (idx + 1) % num_models
                    continue # Try next model
                
                if "400" in error_str and "api key" in error_str:
                    print(f"❌ Invalid API Key detected with {model_name}")
                    return "Error: The GEMINI_API_KEY provided in the backend .env is invalid. Please check your API key."
                
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
        # Try models starting from the current index, cycling through all of them once
        start_index = self.current_model_index
        num_models = len(self.available_models)

        for i in range(num_models):
            # Calculate actual index ensuring we wrap around
            idx = (start_index + i) % num_models
            model_name = self.available_models[idx]
            
            print(f"🤖 (Stream) Attempting to use model: {model_name}" + (" (Fallback)" if i > 0 else ""))
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
                    # Update sticky index to next model for future requests
                    self.current_model_index = (idx + 1) % num_models
                    continue # Try next model
                
                if "400" in error_str and "api key" in error_str:
                    print(f"❌ (Stream) Invalid API Key detected with {model_name}")
                    yield "Error: The GEMINI_API_KEY provided in the backend .env is invalid. Please check your API key."
                    return
                
                print(f"❌ (Stream) Error with {model_name}: {e}")
                continue # Try next model
                
        # If all models failed
        yield "Error: The AI is currently overloaded. Please try again later."
    
# Create singleton instance
ai_service = AIService()
