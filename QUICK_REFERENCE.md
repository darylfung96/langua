# Quick Reference Guide - Story Weaver Feature

## 📁 File Locations

### Frontend
- **Main Component**: `/frontend/src/pages/StoryWeaver.tsx` (695 lines)
- **Styling**: `/frontend/src/pages/StoryWeaver.css`
- **API Base URL**: `http://localhost:8000`
- **Gemini API Key**: `VITE_GEMINI_API_KEY` env var

### Backend
- **API Routes**: `/backend/routes/stories.py`
- **Business Logic**: `/backend/services/story_service.py`
- **Database Model**: `/backend/database.py` → `Story` class
- **Request Schema**: `/backend/schemas.py` → `StoryRequest`
- **File Storage**: `/backend/file_storage.py`
- **Database File**: `/backend/stories.db` (SQLite)
- **Uploaded Audio**: `/backend/uploads/` directory

## 🔗 API Endpoints

```
POST   /stories              Save story with audio
GET    /stories              List all stories
GET    /stories/{id}         Get story details
DELETE /stories/{id}         Delete story + audio
```

All require header: `X-API-Key: {WHISPER_API_KEY}`

## 🧠 Gemini Models Used

| Purpose | Model | Location |
|---------|-------|----------|
| Story Generation | `gemini-3.1-flash-lite-preview` | StoryWeaver.tsx:362-365 |
| Audio Generation | `gemini-2.5-flash-preview-tts` | StoryWeaver.tsx:400-413 |
| Image Generation | GeminiClient WebAPI | routes/image.py:51 |

## 📊 Data Flow - Single Sentence Each

1. **User enters words** → Form validation ✓
2. **Call Gemini API** → Get JSON story + vocabulary
3. **Parse response** → Display story with highlights
4. **Generate audio** (optional) → Stream Gemini TTS → Play
5. **Save to backend** → POST /stories with base64 audio
6. **Backend saves** → Audio to `/uploads/`, metadata to DB
7. **Load saved story** → GET /stories/{id} → Display with audio link

## 📋 Key Data Structures

### Story in Database (SQLite)
```python
Story(
  id = "550e8400-e29b-41d4-a716-446655440000",
  user_id = "default_user",
  title = "My Story Title",
  story_content = "HTML with <span> tags for highlighted words",
  language = "French",
  vocabulary = "[{word, meaning_in_target, equivalent_in_english}, ...]",
  audio_file_path = "uploads/abc123_audio.mp3",
  created_at = datetime.utcnow(),
  updated_at = datetime.utcnow()
)
```

### Vocabulary Word Structure
```typescript
{
  word: "gato",                      // User input word
  meaning_in_target: "gato",         // Translation in target lang
  equivalent_in_english: "cat, furry animal" // Memory hint
}
```

### Story Response from Gemini
```json
{
  "title": "Story Title",
  "story": "Text with <span class='highlight' title='English'>word</span>",
  "vocabulary": [
    {"word": "...", "meaning_in_target": "...", "equivalent_in_english": "..."},
    ...
  ]
}
```

## 🔄 Full Story Lifecycle

```
Generate → Display → [Generate Audio] → [Save] → [Load] → [Delete]
            │                             │        │       │
            └─ Highlighted words ─────────┘        │       │
              Jump on click                        │       │
                                                   │       │
            Read from DB ─────────────────────────┘       │
                                                          │
            Remove from DB ────────────────────────────────┘
```

## 🎯 Key Functions Quick Map

### Frontend (StoryWeaver.tsx)

**Generation & Audio**
- `handleGenerate()` (line 329) - Story generation
- `generateAudio()` (line 388) - Audio generation
- `createWavUrl()` (line 25) - PCM to WAV conversion

**Save & Load**
- `saveStory()` (line 111) - POST story to backend
- `loadSavedStories()` (line 94) - GET all stories
- `loadStoryFromSaved()` (line 180) - GET single story
- `deleteStory()` (line 211) - DELETE story

**Interaction**
- `jumpToWord()` (line 312) - Seek audio to word time
- `toggleAudio()` (line 444) - Play/Pause or generate

### Backend (Services & Routes)

**story_service.py**
- `save_story()` - Validates JSON, saves audio file, commits to DB
- `get_all_stories()` - Returns list ordered by creation date
- `get_story_by_id()` - Returns single story with full content
- `delete_story()` - Removes from DB and deletes audio file

**stories.py (routes)**
- `POST /stories` - Calls `save_story_db()`
- `GET /stories` - Calls `get_all_stories_db()`
- `GET /stories/{id}` - Calls `get_story_by_id_db()`
- `DELETE /stories/{id}` - Calls `delete_story_db()`

## 🔐 Authentication

- **Type**: API Key Header
- **Header Name**: `X-API-Key`
- **Validation File**: `backend/security.py`
- **Env Variable**: `WHISPER_API_KEY`

## 📦 Audio File Handling

1. **Frontend**: Convert audio to base64 string
2. **Send**: In JSON body as `"audio": "base64string..."`
3. **Backend**: Decode base64 → binary bytes
4. **Save**: `save_media_file(bytes, "audio.mp3")`
   - Saves to: `/backend/uploads/{uuid}_{filename}`
   - Returns: Relative path `"uploads/..."`
5. **Store**: Path in DB `Story.audio_file_path`
6. **Retrieve**: Frontend accesses via `http://localhost:8000/{path}`

## 🎨 HTML Story Format

**Input (from Gemini)**
```html
<span class='highlight' title='English meaning'>word</span> more text
```

**Frontend Processing**
- Title attribute → Shows on hover in table
- Text → Appears as vocabulary word
- Click → Seeks audio to that word's time position (calculated by word index)

## ⚙️ Environment Variables Needed

### Frontend (.env)
```
VITE_GEMINI_API_KEY=your_google_genai_key
VITE_BACKEND_API_KEY=your_whisper_api_key
```

### Backend (.env)
```
WHISPER_API_KEY=your_whisper_api_key
GEMINI_COOKIE_1PSID=your_1psid_cookie
GEMINI_COOKIE_1PSIDTS=your_1psidts_cookie
```

## 🚀 Development URLs

```
Frontend:    http://localhost:5173
Backend:     http://localhost:8000
API Docs:    http://localhost:8000/docs
Database:    ./backend/stories.db
```

## 📈 Story Metadata

Each story stores:
- ✅ Unique ID (UUID)
- ✅ Title (from Gemini)
- ✅ Full story content (HTML with highlights)
- ✅ Target language
- ✅ Vocabulary array (JSON)
- ✅ Audio file path (if saved)
- ✅ Creation timestamp
- ✅ Last modified timestamp
- ✅ User ID (currently "default_user")

## 🎯 Word Highlighting in Story

**How Words are Highlighted**
1. Gemini wraps vocabulary words in `<span class='highlight' title='English'>`
2. Frontend parses HTML using regex to extract word list
3. Words indexed by position in story
4. Audio time = (word_index / total_words) × audio_duration
5. Click word → seek to calculated time

**Example**
- Story: "One cat sat" (3 words)
- Audio duration: 9 seconds
- Click "cat" (word 2) → Jump to 6 seconds (2/3 × 9)

## 🔍 Common Issues & Solutions

### Issue: Audio not saving
- Check: Is base64 being extracted correctly from blob/data URL?
- Check: Is backend receiving audio parameter?
- Check: Is file_storage.py accessible and `/uploads` writable?

### Issue: Story not displaying
- Check: Is vocabulary valid JSON?
- Check: Is story HTML parsing correctly?
- Check: Are span tags present in story content?

### Issue: Gemini API errors
- Check: Is API key valid and not expired?
- Check: Is model name spelled correctly?
- Check: Are response formats matching expected JSON?

## 📚 Related Features

- **Melody**: YouTube lyrics extraction and learning (routes/lyrics.py)
- **VisualMemory**: Image generation for words (routes/image.py)
- **ResourceLearner**: Transcribe uploaded media (routes/resources.py)
- **Transcribe**: Speech-to-text (routes/transcribe.py)

## 🧪 Testing Checklist

- [ ] Generate story with 2-3 words
- [ ] Verify vocabulary table displays
- [ ] Generate audio and play/pause
- [ ] Save story to database
- [ ] List saved stories
- [ ] Click saved story to reload
- [ ] Delete saved story
- [ ] Verify audio file removed from /uploads

---

**Last Updated:** 2024-03-12
**Feature Status:** ✅ Production Ready
**Quiz Feature:** ❌ Not Implemented
