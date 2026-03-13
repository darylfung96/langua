# Language Learner - Codebase Documentation

This directory contains comprehensive analysis of the Language Learner application codebase.

## 📚 Documentation Files

### 1. **CODEBASE_ANALYSIS.md** (Primary Reference)
   Comprehensive analysis covering:
   - Overall architecture and structure
   - Story Weaver feature file map
   - Complete story creation and saving flow
   - Gemini AI integration (3 implementations)
   - Word meanings table generation
   - Data models and schemas
   - All API endpoints
   - Environment variables
   - Key implementation details

   **Best for:** Understanding the big picture and complete feature architecture

### 2. **STORY_WEAVER_FLOW.md** (Visual Reference)
   Detailed flow diagrams showing:
   - Architecture overview with all components
   - User interaction flows (generation → saving → loading → deletion)
   - Backend processing steps with code references
   - Database schema
   - Data structure examples
   - API endpoint summary
   - File paths reference
   - Function location reference

   **Best for:** Understanding user flows and data movement through the system

### 3. **QUICK_REFERENCE.md** (Quick Lookup)
   Quick reference guide with:
   - File locations
   - API endpoints
   - Gemini models used
   - Data structures
   - Key functions with line numbers
   - Authentication details
   - Audio file handling
   - Environment variables
   - Testing checklist

   **Best for:** Quick lookups, development, and testing

## 🎯 Quick Start: Story Weaver Feature

### Files You Need to Know

**Frontend:**
- `/frontend/src/pages/StoryWeaver.tsx` (695 lines) - Main component
- `/frontend/src/pages/StoryWeaver.css` - Styling

**Backend:**
- `/backend/routes/stories.py` - API endpoints
- `/backend/services/story_service.py` - Business logic
- `/backend/database.py` - Story model
- `/backend/schemas.py` - Request/response models

### Core Flow (3 Steps)

1. **Generate**: User inputs words → Gemini API generates story with vocabulary
2. **Save**: Story + audio → Backend saves to DB and `/uploads` directory
3. **Load**: Fetch from DB → Display with audio playback

### Key Endpoints

```bash
# Save story
POST /stories
  ├─ Body: {title, story_content, language, vocabulary (JSON), audio (base64)}
  └─ Response: {id, title, language, created_at}

# List stories
GET /stories
  └─ Response: {stories: [{id, title, language, created_at}, ...]}

# Get single story
GET /stories/{id}
  └─ Response: {id, title, story_content, language, vocabulary, audio_file_path, ...}

# Delete story
DELETE /stories/{id}
  └─ Response: {success: true}
```

### Data Models

**Story Table (SQLite)**
```
id                 : UUID (primary key)
user_id            : String ("default_user")
title              : String
story_content      : Text (HTML with <span> tags)
language           : String
vocabulary         : Text (JSON string)
audio_file_path    : String (path to /uploads/...)
created_at         : DateTime
updated_at         : DateTime
```

**Vocabulary Word**
```json
{
  "word": "original_word",
  "meaning_in_target": "translation_in_target_language",
  "equivalent_in_english": "mnemonic_phrase"
}
```

## 🧠 Gemini Integration

### Three Implementations in This Project

1. **Story Generation** (Frontend)
   - Model: `gemini-3.1-flash-lite-preview`
   - Location: `StoryWeaver.tsx:344-378`
   - Returns: JSON with title, story HTML, vocabulary

2. **Audio Generation** (Frontend)
   - Model: `gemini-2.5-flash-preview-tts`
   - Location: `StoryWeaver.tsx:400-413`
   - Voice: "Leda"
   - Returns: Base64 audio (PCM or standard format)

3. **Image Generation** (Backend)
   - API: `GeminiClient` WebAPI
   - Location: `routes/image.py:51`
   - Auth: Browser cookies
   - Returns: Images as URL + base64

## 🔄 Complete Story Lifecycle

```
User enters words
    ↓
Gemini generates story (title + content + vocabulary)
    ↓
Frontend displays story with highlighted words
    ↓
User can generate audio (optional)
    ↓
User saves to backend
    ├─ Audio: base64 → decoded → saved to /uploads/ → path stored in DB
    └─ Story: metadata + vocabulary JSON → saved to DB
    ↓
Saved stories list appears in UI
    ↓
User can load saved story
    ├─ Frontend fetches story by ID
    ├─ Audio file path retrieved
    └─ Story displayed with playable audio
    ↓
User can delete story
    ├─ Story removed from DB
    └─ Audio file deleted from disk
```

## 📁 Directory Structure

```
language_learner/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── StoryWeaver.tsx          ← Main feature (695 lines)
│   │   │   ├── VisualMemory.tsx         ← Image generation UI
│   │   │   ├── Melody.tsx               ← Lyrics learning
│   │   │   ├── ResourceLearner.tsx      ← Media transcription
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Podcasts.tsx
│   │   │   └── Writing.tsx
│   │   ├── components/
│   │   │   └── layout/Header.tsx
│   │   ├── utils/YoutubeTranscript.ts
│   │   ├── App.tsx                      ← Router (7 routes)
│   │   └── main.tsx
│   ├── package.json
│   └── ... (vite config, tsconfig, etc)
│
├── backend/
│   ├── routes/
│   │   ├── stories.py                   ← Story CRUD endpoints
│   │   ├── visual.py                    ← Image save/load endpoints
│   │   ├── lyrics.py                    ← YouTube lyrics endpoints
│   │   ├── resources.py                 ← Media upload endpoints
│   │   ├── transcribe.py                ← Speech-to-text endpoint
│   │   ├── youtube.py                   ← YouTube transcript endpoint
│   │   └── image.py                     ← Image generation endpoint
│   ├── services/
│   │   ├── story_service.py             ← Story business logic
│   │   ├── visual_service.py
│   │   ├── lyric_service.py
│   │   ├── resource_service.py
│   │   └── __init__.py
│   ├── database.py                      ← ORM models (Story, Lyric, Resource, Visual)
│   ├── schemas.py                       ← Pydantic models
│   ├── main.py                          ← FastAPI app initialization
│   ├── config.py                        ← Configuration + env vars
│   ├── security.py                      ← API key validation
│   ├── file_storage.py                  ← File I/O utilities
│   ├── utils.py                         ← Helper functions
│   ├── requirements.txt
│   ├── stories.db                       ← SQLite database
│   ├── uploads/                         ← Audio files directory
│   └── ... (other config files)
│
├── CODEBASE_ANALYSIS.md                 ← Comprehensive analysis
├── STORY_WEAVER_FLOW.md                 ← Flow diagrams
├── QUICK_REFERENCE.md                   ← Quick lookup guide
└── README_ANALYSIS.md                   ← This file
```

## 🔐 Authentication

**Type:** API Key in Header

```
Header: X-API-Key: {WHISPER_API_KEY}
Validation: security.py → get_api_key()
Stored in: config.py → WHISPER_API_KEY
```

All endpoints require this key.

## ⚙️ Configuration

### Environment Variables

**Frontend (.env)**
```
VITE_GEMINI_API_KEY=your_google_genai_api_key
VITE_BACKEND_API_KEY=your_whisper_api_key
```

**Backend (.env)**
```
WHISPER_API_KEY=your_whisper_api_key
GEMINI_COOKIE_1PSID=your_1psid_cookie
GEMINI_COOKIE_1PSIDTS=your_1psidts_cookie (optional)
```

### Database

- **Type:** SQLite
- **Location:** `backend/stories.db`
- **Tables:** stories, lyrics, resources, visuals

## 📊 Technology Stack

**Frontend:**
- React 19.2
- TypeScript
- Vite (build)
- React Router (navigation)
- @google/genai (Gemini API)
- lucide-react (icons)

**Backend:**
- FastAPI 0.115
- SQLAlchemy 2.0 (ORM)
- Uvicorn (ASGI)
- SQLite
- faster-whisper (speech recognition)
- gemini_webapi (image generation)
- youtube-transcript-api

## 🚀 Development

```bash
# Frontend
cd frontend
npm install
npm run dev    # http://localhost:5173

# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
# http://localhost:8000/docs (API documentation)
```

## ✅ Feature Checklist

- ✅ Story Generation via Gemini
- ✅ Audio Generation via Gemini TTS
- ✅ Save Stories to Database
- ✅ Load Saved Stories
- ✅ Delete Stories (with audio cleanup)
- ✅ Vocabulary Table Display
- ✅ Audio Playback Controls
- ✅ Word-to-Audio Synchronization
- ❌ Quiz Functionality (NOT IMPLEMENTED)

## 🎓 Learning Resources

### For Understanding Story Weaver:
1. Read **QUICK_REFERENCE.md** first (5 min) - Get oriented
2. Read **CODEBASE_ANALYSIS.md** section 3-4 (15 min) - Understand flows
3. Read **STORY_WEAVER_FLOW.md** (10 min) - See visual diagrams
4. Examine code files:
   - `StoryWeaver.tsx` - UI implementation
   - `stories.py` - API layer
   - `story_service.py` - Business logic

### For Extending the Feature:
1. Check **QUICK_REFERENCE.md** for function locations
2. Review data structures in section on "Key Data Structures"
3. Follow existing patterns (generation → save → load → delete)
4. Add tests following the existing structure

## 🐛 Debugging Tips

### Story not saving?
- Check API key in headers
- Check if audio is being converted to base64 correctly
- Check `/uploads` directory permissions
- Check SQLite database write access

### Audio not playing?
- Check browser console for audio element errors
- Check if audio file path is correct
- Check file exists in `/uploads`
- Check MIME type is correct

### Gemini API errors?
- Check if API key is valid
- Check model names are spelled correctly
- Check response format matches expectations
- Check JSON parsing for story response

## 📞 Support

Refer to the three documentation files:
- **Quick question?** → Check **QUICK_REFERENCE.md**
- **Understanding flow?** → Check **STORY_WEAVER_FLOW.md**
- **Deep dive?** → Check **CODEBASE_ANALYSIS.md**

---

**Documentation Version:** 1.0
**Last Updated:** 2024-03-12
**Coverage:** Story Weaver Feature Complete

