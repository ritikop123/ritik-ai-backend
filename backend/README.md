# Portfolio AI Chatbot Backend

Python FastAPI backend for the AI-powered portfolio chatbot using Google Gemini.

## Features

- 🤖 Google Gemini AI integration
- 🚀 FastAPI for high performance
- 📡 Streaming responses for real-time chat
- 🔒 Secure API key management
- 🌐 CORS enabled for frontend communication

## Setup

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The `.env` file is already configured with your Gemini API key:
```
GEMINI_API_KEY=AIzaSyCKJSdz72PVBZIjqwIKEwry5XY1utrGoM
FRONTEND_URL=http://localhost:5173
```

### 3. Run the Backend

```bash
# From the backend directory
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET `/`
Health check endpoint
```json
{
  "message": "Portfolio AI Chatbot API",
  "status": "running"
}
```

### POST `/api/chat`
Send a message and get AI response

**Request:**
```json
{
  "message": "What technologies does Ritik work with?",
  "conversation_history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help you?"}
  ]
}
```

**Response:**
```json
{
  "response": "Ritik works with React, TypeScript, Python...",
  "timestamp": "2026-01-15T12:38:00Z"
}
```

### POST `/api/chat/stream`
Stream AI responses in real-time (Server-Sent Events)

Same request format as `/api/chat`, but responses are streamed.

## System Prompt

The AI is configured with context about Ritik's portfolio:
- Skills: React, TypeScript, Python, Java/Kotlin, etc.
- Projects: Web apps, Minecraft plugins, Discord bots
- Experience: Full-stack development, AI integration
- Contact: Available via website contact form

## Development

### Project Structure
```
backend/
├── main.py           # FastAPI application
├── ai_service.py     # Gemini AI integration
├── config.py         # Configuration management
├── requirements.txt  # Python dependencies
├── .env             # Environment variables
└── README.md        # This file
```

### Testing

Test the API using curl:
```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about Ritik", "conversation_history": []}'
```

## Deployment

For production deployment:

1. **Never commit `.env` file** - Use environment variables on your hosting platform
2. **Use a production ASGI server** - Uvicorn with workers or Gunicorn
3. **Add rate limiting** - Prevent API abuse
4. **Monitor API usage** - Track Gemini API costs
5. **Add logging** - For debugging and analytics

### Recommended Platforms
- **Railway** - Easy Python deployment
- **Render** - Free tier available
- **Vercel** - Serverless functions
- **Heroku** - Classic platform

## Troubleshooting

### "GEMINI_API_KEY not found"
Make sure `.env` file exists in the backend directory with your API key.

### CORS errors
Check that `FRONTEND_URL` in `.env` matches your frontend URL.

### Import errors
Make sure all dependencies are installed: `pip install -r requirements.txt`

## License

MIT
