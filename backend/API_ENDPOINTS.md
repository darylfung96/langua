# Language Learner Backend API Endpoints

## Endpoints

### 1. `/youtube-transcript` (GET)
Extracts transcript from a YouTube video in multiple languages.

**Parameters:**
- `url` (string, required): YouTube URL or Video ID
- `languages` (list of strings, optional): ISO 639-1 language codes
  - Default: `["fr", "ja", "zh-TW", "zh-CN", "ko", "en"]`
- `X-API-Key` (header): API key for authentication

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "text": "Full transcript text...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.0,
      "text": "Segment text"
    }
  ],
  "language": "en"
}
```

---

### 2. `/transcribe` (POST)
Transcribes audio files using the faster-whisper model.

**Parameters:**
- `file` (file, required): Audio file (supports .wav, .mp3, .m4a, .ogg, .flac, .mp4, .mkv, .avi, .mov, .webm)
- `language` (string, optional): ISO 639-1 language code for transcription
- `X-API-Key` (header): API key for authentication

**Response:**
```json
{
  "filename": "audio.mp3",
  "text": "Full transcription text...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "Segment text"
    }
  ],
  "language": "en",
  "language_probability": 0.95
}
```

---

### 3. `/generate-image` (POST)
Generates a memorable image for a word in a specific language using Gemini API. Perfect for language learning flashcards!

**Parameters:**
- `word` (string, required): The word to generate an image for
- `language` (string, optional): ISO 639-1 language code (default: "en")
  - Examples: "es" (Spanish), "fr" (French), "ja" (Japanese), "zh-CN" (Chinese)
- `X-API-Key` (header): API key for authentication

**Example Request:**
```bash
curl -X POST "http://localhost:8000/generate-image?word=manzana&language=es" \
  -H "X-API-Key: your_api_key"
```

**Response:**
```json
{
  "word": "manzana",
  "language": "es",
  "prompt": "Create a vibrant, imaginative, and memorable illustration...",
  "images": [
    {
      "id": 0,
      "type": "GeneratedImage",
      "url": "https://...",
      "base64": "iVBORw0KGgoAAAANS..."
    }
  ],
  "text_response": "Here's a vibrant illustration of a Spanish apple...",
  "success": true
}
```

---

## Authentication

All endpoints require the `X-API-Key` header:
```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/endpoint
```

The API key is configured via the `WHISPER_API_KEY` environment variable.

---

## Setup Requirements

### For Image Generation Endpoint

The `/generate-image` endpoint requires Gemini API credentials:

1. Set environment variables:
   ```bash
   export GEMINI_COOKIE_PSID="your_cookie_psid_value"
   export GEMINI_COOKIE_PSIDTS="your_cookie_psidts_value"  # optional
   ```

2. Get your cookies:
   - Log in to [gemini.google.com](https://gemini.google.com)
   - Use browser developer tools or tools like `browser-cookie3` to extract cookies
   - Look for `Secure_1PSID` and optionally `Secure_1PSIDTS`

3. Configure in `.env` file or set as environment variables before running the server

---

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (validation error)
- `403`: Unauthorized (invalid API key)
- `404`: Not found (e.g., invalid YouTube video)
- `413`: Payload too large (file exceeds 50MB)
- `500`: Internal server error
- `503`: Service unavailable (Gemini service not configured)

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```
