# Language Learner Codebase Analysis

## 1. OVERALL STRUCTURE

The application is a full-stack language learning platform with separate frontend and backend:

```
language_learner/
├── frontend/              # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/        # Feature pages (StoryWeaver, Melody, VisualMemory, etc.)
│   │   ├── components/   # Reusable UI components
│   │   ├── utils/        # Utility functions
│   │   ├── App.tsx       # Main router
│   │   └── main.tsx      # Entry point
│   └── package.json      # Dependencies
│
└── backend/              # FastAPI + Python
    ├── routes/          # API endpoint handlers
    ├── services/        # Business logic
    ├── database.py      # SQLAlchemy ORM models
    ├── schemas.py       # Pydantic request/response models
    ├── main.py          # FastAPI app initialization
    ├── config.py        # Configuration and environment
    ├── security.py      # API key authentication
    ├── file_storage.py  # File upload/download utilities
    ├── utils.py         # Helper functions
    └── requirements.txt  # Python dependencies
```

### Technology Stack

**Frontend:**
- React 19.2 + TypeScript
- Vite (build tool)
- React Router (navigation)
- @google/genai (Gemini API client)
- lucide-react (icons)
- react-markdown (markdown rendering)
- react-player (media playback)

**Backend:**
- FastAPI 0.115
- SQLAlchemy 2.0 (ORM)
- Uvicorn (ASGI server)
- SQLite (database)
- faster-whisper (speech transcription)
- gemini_webapi (Gemini API client)
- youtube-transcript-api (YouTube transcript extraction)

---

## 2. STORY WEAVER FEATURE - COMPLETE FILE MAP

### Frontend Files

**Main Component:** `/Users/darylfung/programming/language_learner/frontend/src/pages/StoryWeaver.tsx` (695 lines)
- Contains entire feature implementation (generation, saving, playback, vocabulary display)
- Uses Gemini API directly via @google/genai SDK
- Handles audio generation and playback
- Manages saved stories list

**Styling:** `/Users/darylfung/programming/language_learner/frontend/src/pages/StoryWeaver.css`

### Backend Files

**API Route Handler:** `/Users/darylfung/programming/language_learner/backend/routes/stories.py`
- Endpoints: `POST /stories`, `GET /stories`, `GET /stories/{id}`, `DELETE /stories/{id}`
- Uses API key authentication

**Service Logic:** `/Users/darylfung/programming/language_learner/backend/services/story_service.py`
- Functions: `save_story()`, `get_all_stories()`, `get_story_by_id()`, `delete_story()`
- Handles audio file save/delete with base64 decoding
- Validates vocabulary JSON

**Database Model:** `/Users/darylfung/programming/language_learner/backend/database.py` (Story table)
- Fields: id, user_id, title, story_content, language, vocabulary, audio_file_path, created_at, updated_at

**Request Schema:** `/Users/darylfung/programming/language_learner/backend/schemas.py`
- StoryRequest: title, story_content, language, vocabulary (JSON string), audio (optional base64)
- StoryResponse: full story with all metadata

**File Storage:** `/Users/darylfung/programming/language_learner/backend/file_storage.py`
- save_media_file(): Saves base64 audio to `/uploads` directory
- delete_media_file(): Deletes audio files

---

## 3. STORY CREATION & SAVING FLOW (Complete Workflow)

### Generation Flow:
1. **User Input** (StoryWeaver.tsx lines 329-386)
   - User selects language (Spanish, French, German, etc.)
   - Enters vocabulary words (comma-separated)

2. **Gemini API Call** (StoryWeaver.tsx lines 344-378)
   - Model: `gemini-3.1-flash-lite-preview`
   - Prompt creates JSON with: title, story (HTML with `<span>` tags), vocabulary array
   - Response parsing: Removes markdown formatting (```json blocks)

3. **Story Structure Generated**
   ```json
   {
     "title": "Story Title in Target Language",
     "story": "Story text with <span class='highlight' title='English'>word</span>",
     "vocabulary": [
       {
         "word": "original_word",
         "meaning_in_target": "translated_meaning",
         "equivalent_in_english": "english_word"
       }
     ]
   }
   ```

4. **User Can Generate Audio** (StoryWeaver.tsx lines 388-442)
   - Model: `gemini-2.5-flash-preview-tts`
   - Generates audio with voice "Leda"
   - Returns base64 PCM audio or standard audio format
   - Audio playback with seek controls

5. **User Saves Story** (StoryWeaver.tsx lines 111-178)
   - Converts audio blob to base64 (if present)
   - POST to `/stories` endpoint with:
     - title, story_content, language, vocabulary (JSON string), audio (base64)
   - Backend saves to database + saves audio file to disk
   - Response includes story ID and creation timestamp
   - UI reloads saved stories list

### Saving Backend Process:
1. `/stories` POST endpoint (routes/stories.py lines 18-39)
2. Calls `save_story()` service (services/story_service.py lines 13-49)
3. Validates vocabulary JSON
4. If audio present: decodes base64 → calls `save_media_file()` → returns relative path
5. Creates Story model instance with all data
6. Commits to SQLite database
7. Returns story ID and metadata

### Loading Flow:
- Frontend loads saved stories on mount (useEffect in StoryWeaver.tsx line 90)
- GET `/stories` returns list of all stories
- Click on saved story → GET `/stories/{id}` → loads full data including story_content and vocabulary
- Audio file path retrieved and set as audio URL

### Deletion Flow:
- DELETE `/stories/{id}` endpoint
- Service deletes from database + deletes associated audio file from disk
- Frontend reloads stories list

---

## 4. GEMINI AI INTEGRATION

### Two Different Gemini Implementations:

#### A. **Story Generation (Frontend - Google GenAI SDK)**
**File:** StoryWeaver.tsx lines 329-386

```typescript
const ai = new GoogleGenAI({ apiKey });
const response = await ai.models.generateContent({
  model: 'gemini-3.1-flash-lite-preview',
  contents: prompt,
});
```

- **API Key Source:** `VITE_GEMINI_API_KEY` environment variable
- **Model:** gemini-3.1-flash-lite-preview
- **Purpose:** Generate story with vocabulary words
- **Response Format:** JSON with title, story, vocabulary

#### B. **Audio Generation (Frontend - Google GenAI SDK)**
**File:** StoryWeaver.tsx lines 388-442

```typescript
const response = await ai.models.generateContent({
  model: 'gemini-2.5-flash-preview-tts',
  contents: prompt,
  config: {
    responseModalities: ["AUDIO"],
    speechConfig: {
      voiceConfig: {
        prebuiltVoiceConfig: { voiceName: 'Leda' }
      }
    }
  }
});
```

- **Model:** gemini-2.5-flash-preview-tts (TTS enabled)
- **Voice:** Leda
- **Response:** Audio in base64 (PCM or other format)
- **Playback:** Converted to WAV or data URL for HTML audio element

#### C. **Image Generation (Backend - Gemini WebAPI)**
**File:** routes/image.py

```python
from gemini_webapi import GeminiClient
gemini_client = GeminiClient(GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS)
response = await gemini_client.generate_content(creative_prompt)
```

- **Auth Method:** Browser cookies (Secure_1PSID, Secure_1PSIDTS)
- **Purpose:** Generate memorable images for vocabulary words
- **Response:** Images with URL and/or base64 encoding
- **Environment Variables:** GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS

---

## 5. WORD MEANINGS TABLE GENERATION & STORAGE

### How Vocabulary Table is Generated:

**Source:** Gemini API prompt in StoryWeaver.tsx lines 345-360

The prompt requests:
```
"vocabulary": [
  {
    "word": "The original word submitted by the user",
    "meaning_in_target": "The translated word in {language}",
    "equivalent_in_english": "The equivalent word in English"
  }
]
```

### Gemini's Generation Process:
1. Takes user input words (comma-separated)
2. Creates a story incorporating those words
3. For each word, generates:
   - **meaning_in_target:** Translation/definition in target language
   - **equivalent_in_english:** English equivalent or mnemonic phrase
   - **word:** Original user input word

### Storage:

**Database Field:** Story.vocabulary (Text column)
- Stored as JSON string: `"[{...}, {...}]"`
- Database: `/Users/darylfung/programming/language_learner/backend/stories.db` (SQLite)

**Retrieval Process:**
1. GET `/stories/{id}` endpoint (routes/stories.py line 74-89)
2. Service retrieves Story from database
3. Parses JSON string: `json.loads(story.vocabulary)` (line 81)
4. Returns as JSON array to frontend

**Frontend Display:** StoryWeaver.tsx lines 656-687
- HTML table with columns: "Original Word", "Meaning in {Language}", "Equivalent Word in English"
- Interactive: Click word in table → jumps to that word in story audio

### Data Structure:

```typescript
interface VocabWord {
  word: string;                    // e.g., "gato"
  meaning_in_target: string;       // e.g., "gato" (if Spanish)
  equivalent_in_english: string;   // e.g., "cat, a furry animal"
}
```

---

## 6. DATA MODELS & SCHEMAS

### Story Model (database.py lines 14-26)
```python
class Story(Base):
    __tablename__ = "stories"
    id: String (Primary Key, UUID)
    user_id: String (default: "default_user")
    title: String (required)
    story_content: Text (required)
    language: String (required)
    vocabulary: Text (required, JSON string)
    audio_file_path: String (optional, path to audio file)
    created_at: DateTime (auto-set)
    updated_at: DateTime (auto-updated)
```

### Story Request Schema (schemas.py lines 11-17)
```python
class StoryRequest(BaseModel):
    title: str
    story_content: str
    language: str
    vocabulary: str              # JSON string
    audio: Optional[str] = None  # Base64 audio
```

### Story Response Schema (schemas.py lines 19-28)
```python
class StoryResponse(BaseModel):
    id: str
    title: str
    story_content: str
    language: str
    vocabulary: dict            # Parsed from JSON
    audio: Optional[str] = None
    created_at: str
    updated_at: str
```

### Other Related Models:

**Lyric (database.py lines 28-39)**
- For YouTube videos: id, user_id, title, video_id, language, transcript (JSON), timestamps

**Resource (database.py lines 41-54)**
- For uploaded media: id, user_id, title, file_name, file_type, language, transcript (JSON), media_file_path

**Visual (database.py lines 56-68)**
- For generated images: id, user_id, word, language, images (JSON), prompt, explanation, timestamps

---

## 7. API ENDPOINTS

### Story Endpoints (routes/stories.py)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/stories` | Save a story | API Key |
| GET | `/stories` | List all stories | API Key |
| GET | `/stories/{story_id}` | Get story details | API Key |
| DELETE | `/stories/{story_id}` | Delete a story | API Key |

### Other Main Endpoints

**Transcription:**
- `POST /transcribe` - Transcribe audio/video using Whisper

**YouTube:**
- `GET /youtube-transcript` - Extract YouTube transcript

**Image Generation:**
- `POST /generate-image` - Generate images for vocabulary words (uses Gemini WebAPI)

**Lyrics (YouTube):**
- `POST /lyrics` - Save YouTube lyrics
- `GET /lyrics` - List lyrics
- `GET /lyrics/{lyric_id}` - Get lyric details
- `DELETE /lyrics/{lyric_id}` - Delete lyric

**Visuals (Generated Images):**
- `POST /visuals` - Save generated visual
- `GET /visuals` - List visuals
- `GET /visuals/{visual_id}` - Get visual details
- `DELETE /visuals/{visual_id}` - Delete visual

**Resources (Uploaded Media):**
- `POST /resources` - Upload and transcribe resource
- `GET /resources` - List resources
- `GET /resources/{resource_id}` - Get resource details
- `DELETE /resources/{resource_id}` - Delete resource

### Authentication
All endpoints require header: `X-API-Key: {WHISPER_API_KEY}`
Validated in security.py against config.WHISPER_API_KEY

---

## 8. QUIZ FUNCTIONALITY

**Status:** NOT IMPLEMENTED

No quiz-related code found in the codebase. The application currently focuses on:
1. Story generation and vocabulary learning
2. Audio transcription and playback
3. Visual memory aids (image generation)
4. Resource learning (uploaded media)
5. Melody/lyrics learning
6. Writing exercises

---

## 9. ENVIRONMENT VARIABLES REQUIRED

### Frontend (.env)
```
VITE_GEMINI_API_KEY=your_google_genai_api_key
VITE_BACKEND_API_KEY=your_whisper_api_key
```

### Backend (.env)
```
WHISPER_API_KEY=your_whisper_api_key
GEMINI_COOKIE_1PSID=your_1psid_cookie
GEMINI_COOKIE_1PSIDTS=your_1psidts_cookie (optional)
```

---

## 10. KEY IMPLEMENTATION DETAILS

### Story HTML Structure
Stories are returned with highlighted words:
```html
<span class='highlight' title='English Translation'>word</span>
```

These are:
- Clicked to jump to that position in audio (StoryWeaver.tsx line 643)
- Parsed with regex to extract into an array of word objects
- Indexed to calculate audio playback time

### Audio Processing (StoryWeaver.tsx lines 25-65)
- Converts base64 PCM audio to WAV format
- WAV Header construction with proper RIFF format
- Creates blob URL for HTML audio element
- Supports standard audio formats (MP3, OGG, etc.)

### File Storage
- Audio files saved to `/uploads/` directory with UUID prefix
- Path stored in database (e.g., "uploads/abc12345_audio.mp3")
- Static files mounted in FastAPI at /uploads endpoint
- Files deleted when story is deleted

### Vocabulary Mnemonic System
The "equivalent_in_english" field serves as a mnemonic device:
- Not just a simple translation
- Often includes context, description, or memory hook
- Generated by Gemini to be memorable for language learners

---

## 11. FRONTEND PAGES OVERVIEW

| Page | File | Purpose |
|------|------|---------|
| Dashboard | Dashboard.tsx | Overview/home page |
| Story Weaver | StoryWeaver.tsx | **Main feature** - Generate stories with vocabulary |
| Melody | Melody.tsx | Learn through music/lyrics |
| Podcasts | Podcasts.tsx | Podcast learning (placeholder) |
| Visual Memory | VisualMemory.tsx | Image generation for words |
| Writing | Writing.tsx | Writing exercises (placeholder) |
| Resource Learner | ResourceLearner.tsx | Upload and learn from media |

---

## 12. KEY FUNCTIONS SUMMARY

### Frontend (StoryWeaver.tsx)

| Function | Lines | Purpose |
|----------|-------|---------|
| handleGenerate | 329-386 | Call Gemini to generate story |
| generateAudio | 388-442 | Call Gemini TTS to generate audio |
| saveStory | 111-178 | Save story to backend |
| loadSavedStories | 94-109 | Fetch list of saved stories |
| loadStoryFromSaved | 180-209 | Load full story data by ID |
| deleteStory | 211-229 | Delete story from backend |
| createWavUrl | 25-65 | Convert PCM base64 to WAV blob URL |

### Backend (story_service.py)

| Function | Purpose |
|----------|---------|
| save_story() | Save story to DB with audio handling |
| get_all_stories() | Fetch all stories ordered by date |
| get_story_by_id() | Fetch single story with full content |
| delete_story() | Delete story and associated audio file |

---

