# FastAPI AI Chat Backend

Production-ready FastAPI backend for AI-powered chat functionality using **Google Gemini (FREE tier)**, deployable on Fly.io.

## Features

- ✅ FastAPI framework with async support
- ✅ **Rapid Bot Fallback** (Rotates through Gemini 2.5 Flash, 2.5 Flash Lite, and 3 Flash)
- ✅ Health check endpoint
- ✅ Comprehensive error handling
- ✅ CORS middleware configured
- ✅ Environment variable configuration
- ✅ Production-ready with Fly.io support

## Endpoints

### `GET /health`

Health check endpoint that returns server status.

**Response:**

```json
{
  "status": "ok"
}
```

### `POST /chat`

Chat endpoint that processes messages using Google Gemini API.

**Request:**

```json
{
  "message": "Your question here"
}
```

**Response:**

```json
{
  "response": "AI-generated response",
  "model": "gemini-1.5-flash"
}
```

## Local Development

### Prerequisites

- Python 3.9+
- Google Gemini API key (FREE at [Google AI Studio](https://makersuite.google.com/app/apikey))

### Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Get your FREE Gemini API key:**

   - Visit https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy your key

3. **Set environment variables:**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Gemini API key
GEMINI_API_KEY=your_actual_api_key_here
```

4. **Run the server:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### Testing

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

Test the chat endpoint:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## Deployment on Fly.io

### Prerequisites

- [Fly.io CLI installed](https://fly.io/docs/hands-on/install-flyctl/)
- Fly.io account

### Deploy Steps

1. **Login to Fly.io:**

```bash
flyctl auth login
```

2. **Update fly.toml:**

Edit `fly.toml` and change `app = "your-app-name"` to your desired app name.

3. **Set secrets:**

```bash
flyctl secrets set GEMINI_API_KEY=your_actual_api_key_here
```

4. **Deploy:**

```bash
flyctl deploy
```

5. **Check status:**

```bash
flyctl status
```

Your API will be available at `https://your-app-name.fly.dev`

### Monitoring

View logs:

```bash
flyctl logs
```

Check app status:

```bash
flyctl status
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key (FREE at makersuite.google.com) |
| `PORT` | No | Port to run the server (auto-set by Fly.io) |

## Why Gemini?

✅ **100% FREE** on the free tier (60 requests/minute)  
✅ **Fast** - Gemini 1.5 Flash is optimized for speed  
✅ **Smart** - Comparable to GPT-3.5 Turbo  
✅ **No credit card required** for API access  
✅ **Perfect for portfolios** - More than enough quota for personal projects

## Security Notes

- ✅ API keys are read from environment variables only
- ✅ No hardcoded credentials
- ✅ CORS configured (update for production domains)
- ✅ Input validation on all endpoints
- ✅ Comprehensive error handling
- ⚠️ Update CORS origins in production to specific domains

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad request (empty message or content blocked by safety filters)
- `401` - Invalid API key
- `429` - Rate limit exceeded
- `500` - Server configuration error

## Customization

To customize the AI's personality or knowledge, edit the `system_instruction` in `main.py` (around line 70).

## License

MIT
