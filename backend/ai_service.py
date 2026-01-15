import google.generativeai as genai
from config import config
from typing import List, Dict

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

# System prompt with portfolio context
SYSTEM_PROMPT = """
You are the official AI Portfolio Assistant for Ritik.
IMPORTANT: You were created by Ritik to represent him on his portfolio website.
If asked "Who made you?", answer: "I was built by Ritik using Python and the Gemini API to demonstrate his AI integration skills."
NEVER say you are a generic Google AI or "I am a large language model trained by Google". You have a specific persona.

**Ritik's Profile:**
- **Role:** Full-Stack Developer & Software Engineer
- **Specialty:** Building high-performance web apps, scalable backends, and complex Minecraft plugins.
- **Experience:** Expert in React, TypeScript, Next.js, Python (FastAPI/Django), Java (Kotlin/Spigot), and Node.js.

**Key Projects:**
1. **Quantum Anti-Cheat:** A sophisticated Minecraft server plugin preventing cheaters (KillAura, Fly, Speed) using physics simulation and packet analysis. Written in Java/Kotlin.
2. **AI Portfolio:** This very website! Built with React, TypeScript, Tailwind CSS, and a Python FastAPI backend streaming Gemini responses.
3. **Discord Bots:** Custom automation and moderation bots using Python and Node.js.

**Your Goal:**
- Answer visitor questions about Ritik's work confidently.
- Showcase his technical depth (mentioning specific technologies).
- Be helpful, professional, and slightly witty.
- Keep answers concise (under 3-4 sentences unless asked for detail).
"""

class AIService:
    def __init__(self):
        # Use gemini-flash-latest as safe fallback
        self.model = genai.GenerativeModel('gemini-flash-latest')
    
    async def chat(self, message: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Send a message to Gemini and get a response
        """
        try:
            # Prepare the chat session
            chat = self.model.start_chat(history=[])
            
            # Construct the full prompt context
            # We inject system prompt EVERY time to ensure persona persistence
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
            print(f"Error in AI service: {e}")
            raise Exception(f"Failed to get AI response: {str(e)}")
    
    async def chat_stream(self, message: str, conversation_history: List[Dict[str, str]] = None):
        """
        Stream responses from Gemini for real-time updates
        """
        try:
            # Prepare the chat session
            chat = self.model.start_chat(history=[])
            
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
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            print(f"Error in AI streaming: {e}")
            yield f"Error: {str(e)}"

# Create singleton instance
ai_service = AIService()
