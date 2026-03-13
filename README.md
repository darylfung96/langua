# Language Learner

An AI-powered language learning app with story generation, audio transcription, vocabulary quizzes, and YouTube transcript support.

## Project Structure

```
language_learner/
├── backend/    # FastAPI server (Python)
└── frontend/   # React + Vite app (TypeScript)
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- A [Whisper API](https://github.com/openai/whisper) key
- (Optional) Google OAuth2 credentials for social login
- (Optional) Gemini API cookies for AI image generation

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment template and fill in the required values:

```bash
cp .env.template .env
```

**Required variables in `backend/.env`:**

| Variable | Description |
|---|---|
| `WHISPER_API_KEY` | API key for audio transcription |
| `JWT_SECRET_KEY` | Secret for signing JWTs — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |

See [`backend/.env.template`](backend/.env.template) for the full list of options.

Start the API server:

```bash
python main.py
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
```

Copy the environment template:

```bash
cp .env.template .env
```

Start the dev server:

```bash
npm run dev
```

The app is available at `http://localhost:5173`.

## Security Notes

- **Never commit `.env` files.** They are gitignored. Use `.env.template` as a guide.
- **Rotate credentials** if you suspect they have been exposed.
- For production, set `CORS_ORIGINS` to your actual domain(s) and use HTTPS.
- The `JWT_SECRET_KEY` **must** be set — the server will refuse to start without it.
- Uploaded media files are served at `/uploads/{filename}` and require a valid JWT.

## Environment Variables

### Backend (`backend/.env`)

See [`backend/.env.template`](backend/.env.template) for the full annotated list.

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|---|---|---|
| `VITE_BACKEND_URL` | URL of the backend API | `http://localhost:8000` |

## Development

Run both servers in separate terminals:

```bash
# Terminal 1 — backend
cd backend && python main.py

# Terminal 2 — frontend
cd frontend && npm run dev
```
