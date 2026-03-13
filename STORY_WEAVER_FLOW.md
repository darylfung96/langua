# Story Weaver Feature - Complete Data Flow Diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React/TypeScript)                  │
│                   /Users/darylfung/.../StoryWeaver.tsx               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
                  ▼               ▼               ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │  Gemini API  │  │ Gemini TTS   │  │ Backend API  │
        │  (Story Gen) │  │ (Audio Gen)  │  │ (Save/Load)  │
        └──────────────┘  └──────────────┘  └──────────────┘
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
                  ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI/Python)                         │
│                    /Users/darylfung/.../backend/                     │
│                                                                       │
│  Routes (routes/stories.py)                                          │
│  ├─ POST /stories → save_story()                                    │
│  ├─ GET /stories → get_all_stories()                                │
│  ├─ GET /stories/{id} → get_story_by_id()                           │
│  └─ DELETE /stories/{id} → delete_story()                           │
│                                                                       │
│  Services (services/story_service.py)                                │
│  └─ Business logic for all story operations                          │
│                                                                       │
│  Database (database.py)                                              │
│  └─ SQLAlchemy ORM: Story model                                      │
│                                                                       │
│  File Storage (file_storage.py)                                      │
│  └─ Audio file persistence: /uploads/                                │
│                                                                       │
│  SQLite DB: stories.db                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## User Interaction Flow

### 1. STORY GENERATION

```
User Interface (StoryWeaver.tsx)
    │
    ├─ Input Language: "French"
    ├─ Input Words: "gato, leche, rapido"
    │
    └─► CLICK "Weave Story"
            │
            ▼
    Prepare Prompt:
    "Write an engaging story in French that incorporates 
     the following vocabulary words: gato, leche, rapido.
     Return as JSON with: title, story, vocabulary"
            │
            ▼
    Call Gemini API
    Model: gemini-3.1-flash-lite-preview
            │
            ├─► Generate story text
            ├─► Wrap keywords in HTML: <span class='highlight' title='English'>word</span>
            └─► Generate vocabulary array:
                [
                  {
                    "word": "gato",
                    "meaning_in_target": "gato",
                    "equivalent_in_english": "cat, furry animal"
                  },
                  ...
                ]
            │
            ▼
    Parse JSON Response
    (Remove markdown formatting if present)
            │
            ▼
    Display:
    ├─ Story title
    ├─ Story text (with highlighted words)
    └─ Vocabulary table
            │
            └─ User can now:
               ├─ Generate audio
               ├─ Save story
               └─ Load different story
```

### 2. AUDIO GENERATION

```
User Interface
    │
    └─► CLICK "Listen" Button
            │
            ▼
    Strip HTML tags from story
    Prepare prompt: "Please read the following story 
                     aloud in French: {story_text}"
            │
            ▼
    Call Gemini API (TTS enabled)
    Model: gemini-2.5-flash-preview-tts
    Voice: Leda
    responseModalities: ["AUDIO"]
            │
            ▼
    Receive audio (base64 PCM or standard format)
            │
            ├─ If PCM: Convert to WAV format
            │   (createWavUrl function)
            │   - Add RIFF/WAVE headers
            │   - Create blob URL
            │
            └─ If standard format:
                Create data URL: data:audio/...;base64,...
            │
            ▼
    Display:
    ├─ Play/Pause button (active state)
    ├─ Seek bar with time display
    └─ Audio waveform animation
            │
            └─ User interactions:
               ├─ Play/Pause
               ├─ Seek to position
               └─ Click word to jump to that word in audio
```

### 3. STORY SAVING

```
User Interface
    │
    └─► CLICK "Save" Button
            │
            ▼
    Prepare Save Request:
    {
      "title": "Story Title (user-input-words)",
      "story_content": "{full_story_html}",
      "language": "French",
      "vocabulary": "{JSON_string}",
      "audio": "{base64_audio_or_null}"
    }
            │
            ▼
    POST to http://localhost:8000/stories
    Header: X-API-Key: {VITE_BACKEND_API_KEY}
            │
            ▼
    ┌────────────────────────────────────────┐
    │         BACKEND PROCESSING              │
    │                                        │
    │  routes/stories.py: save_story()       │
    │    │                                   │
    │    ├─ Validate API key                │
    │    └─ Call service layer              │
    │                                        │
    │  services/story_service.py: save_story()
    │    │                                   │
    │    ├─ Validate vocabulary JSON         │
    │    │                                   │
    │    ├─ If audio present:                │
    │    │   ├─ Decode base64                │
    │    │   ├─ Call save_media_file()       │
    │    │   │   └─ Save to /uploads/        │
    │    │   │       (with UUID prefix)      │
    │    │   └─ Get relative path            │
    │    │                                   │
    │    ├─ Create Story model instance      │
    │    │   ├─ id: UUID (auto-generated)    │
    │    │   ├─ title                        │
    │    │   ├─ story_content                │
    │    │   ├─ language                     │
    │    │   ├─ vocabulary: "{JSON_string}"  │
    │    │   ├─ audio_file_path: "uploads/..." (or null)
    │    │   ├─ user_id: "default_user"    │
    │    │   ├─ created_at: now              │
    │    │   └─ updated_at: now              │
    │    │                                   │
    │    ├─ db.add(story)                    │
    │    ├─ db.commit()                      │
    │    └─ Return story object              │
    │                                        │
    │  routes/stories.py: Format response    │
    │    └─ Return: {id, title, language,    │
    │              created_at}               │
    └────────────────────────────────────────┘
            │
            ▼
    Receive Response: {id: "abc123", title: "...", ...}
            │
            ▼
    Frontend:
    ├─ Show success message: "Story saved successfully!"
    ├─ Reload saved stories list (GET /stories)
    └─ Clear message after 2 seconds
```

### 4. LOADING SAVED STORY

```
User Interface
    │
    └─ On page load OR click saved story
            │
            ▼
    Load Saved Stories:
    GET http://localhost:8000/stories
    Header: X-API-Key: {VITE_BACKEND_API_KEY}
            │
            ▼
    Backend returns list:
    {
      "stories": [
        {
          "id": "uuid1",
          "title": "...",
          "language": "French",
          "created_at": "2024-03-12T...",
          "updated_at": "2024-03-12T..."
        },
        ...
      ]
    }
            │
            ▼
    Display in sidebar:
    ├─ "📚 Saved Stories"
    ├─ List of story buttons
    └─ Each with delete button (trash icon)
            │
            └─ User clicks story in list
                    │
                    ▼
            GET http://localhost:8000/stories/{story_id}
            Header: X-API-Key: {VITE_BACKEND_API_KEY}
                    │
                    ▼
            Backend returns full story:
            {
              "id": "uuid1",
              "title": "...",
              "story_content": "...",
              "language": "French",
              "vocabulary": [...],    ← Parsed from JSON
              "audio_file_path": "uploads/abc_audio.mp3",
              "created_at": "...",
              "updated_at": "..."
            }
                    │
                    ▼
            Frontend loads:
            ├─ Story title and content
            ├─ Vocabulary table
            └─ Audio from: http://localhost:8000/{audio_file_path}
                    │
                    ▼
            Display everything (same UI as new story)
```

### 5. STORY DELETION

```
User Interface
    │
    └─ Click trash icon on saved story
            │
            ▼
    Show confirmation dialog:
    "Are you sure you want to delete this story?"
            │
            ├─ Cancel → Do nothing
            │
            └─ Confirm
                    │
                    ▼
            DELETE http://localhost:8000/stories/{story_id}
            Header: X-API-Key: {VITE_BACKEND_API_KEY}
                    │
                    ▼
            ┌────────────────────────────────────────┐
            │       BACKEND DELETE PROCESS           │
            │                                        │
            │  routes/stories.py: delete_story()     │
            │    │                                   │
            │    └─ Call service layer              │
            │                                        │
            │  services/story_service.py:delete_story()
            │    │                                   │
            │    ├─ Query: db.query(Story).filter... │
            │    │         .first()                  │
            │    │                                   │
            │    ├─ If audio_file_path exists:      │
            │    │   └─ delete_media_file()          │
            │    │       └─ Delete from /uploads/    │
            │    │                                   │
            │    ├─ db.delete(story)                 │
            │    ├─ db.commit()                      │
            │    └─ Return True                      │
            │                                        │
            │  routes/stories.py: Format response    │
            │    └─ Return: {success: true}          │
            └────────────────────────────────────────┘
                    │
                    ▼
            Receive: {success: true, message: "Story deleted"}
                    │
                    ▼
            Frontend:
            ├─ Reload saved stories list
            └─ Update UI
```

---

## Database Schema

```
SQLite: stories.db
│
└─ TABLE: stories
   ├─ id (TEXT, PRIMARY KEY)           [UUID]
   ├─ user_id (TEXT)                   ["default_user"]
   ├─ title (TEXT, NOT NULL)           ["My Story Title"]
   ├─ story_content (TEXT, NOT NULL)   ["Full story with HTML..."]
   ├─ language (TEXT, NOT NULL)        ["French"]
   ├─ vocabulary (TEXT, NOT NULL)      [JSON: "[{...}, {...}]"]
   ├─ audio_file_path (TEXT, NULL)     ["uploads/abc12345_audio.mp3"]
   ├─ created_at (DATETIME)            [auto: now]
   └─ updated_at (DATETIME)            [auto: now, on update]
```

---

## Key Data Structures

### Vocabulary Word (from Gemini)
```typescript
interface VocabWord {
  word: string;                  // "gato" (original user input)
  meaning_in_target: string;     // "gato" (or French if translated)
  equivalent_in_english: string; // "cat, a furry animal" (mnemonic)
}
```

### Story Response (Gemini → Frontend)
```typescript
interface StoryResponse {
  title: string;           // "The Adventure of..." in target language
  story: string;           // HTML with <span class='highlight' title='English'>word</span>
  vocabulary: VocabWord[]; // Array of 3-5 vocab words
}
```

### Highlighted Word in Story HTML
```html
<span class='highlight' title='cat'>gato</span>
```
- `title`: English translation (shows on hover)
- Text content: Target language word
- Click: Jumps to that word's audio position

### Saved Story List Item (Backend response)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Adventure (gato, leche, rápido)",
  "language": "French",
  "created_at": "2024-03-12T18:30:00.000Z",
  "updated_at": "2024-03-12T18:30:00.000Z"
}
```

### Full Story (Backend GET by ID)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Adventure",
  "story_content": "<p>Once upon a time... <span class='highlight' title='cat'>gato</span>...</p>",
  "language": "French",
  "vocabulary": [
    {
      "word": "gato",
      "meaning_in_target": "gato",
      "equivalent_in_english": "cat, a furry animal"
    },
    ...
  ],
  "audio_file_path": "uploads/a1b2c3d4_audio.mp3",
  "created_at": "2024-03-12T18:30:00.000Z",
  "updated_at": "2024-03-12T18:30:00.000Z"
}
```

---

## API Endpoints Summary

### Story Management
```
POST   /stories                    → Save new story
GET    /stories                    → List all stories
GET    /stories/{story_id}         → Get story details
DELETE /stories/{story_id}         → Delete story
```

### Supporting Features
```
POST   /transcribe                 → Transcribe audio
GET    /youtube-transcript         → Get YouTube transcript
POST   /generate-image             → Generate images for words
GET    /visuals                    → List generated visuals
POST   /visuals                    → Save visual
DELETE /visuals/{visual_id}        → Delete visual
```

---

## Key Functions & Their Locations

### Frontend (StoryWeaver.tsx)

| Line Range | Function | Purpose |
|-----------|----------|---------|
| 25-65 | `createWavUrl()` | Convert base64 PCM to WAV blob URL |
| 94-109 | `loadSavedStories()` | Fetch saved stories from backend |
| 111-178 | `saveStory()` | Save generated story to backend |
| 180-209 | `loadStoryFromSaved()` | Load full story by ID |
| 211-229 | `deleteStory()` | Delete story from backend |
| 280-310 | `storyWords` (useMemo) | Parse story HTML into word array |
| 312-327 | `jumpToWord()` / `jumpToVocab()` | Seek audio to word position |
| 329-386 | `handleGenerate()` | Generate story via Gemini API |
| 388-442 | `generateAudio()` | Generate audio via Gemini TTS |
| 444-455 | `toggleAudio()` | Play/pause or generate audio |

### Backend (services/story_service.py)

| Function | Purpose |
|----------|---------|
| `save_story()` | Validate, save story and audio to DB |
| `get_all_stories()` | Fetch stories ordered by date |
| `get_story_by_id()` | Get single story with full content |
| `delete_story()` | Delete story and audio file |

### Backend (routes/stories.py)

| Endpoint | Function | Purpose |
|----------|----------|---------|
| POST /stories | `save_story()` | API handler for saving |
| GET /stories | `get_all_stories()` | API handler for listing |
| GET /stories/{id} | `get_story()` | API handler for detail |
| DELETE /stories/{id} | `delete_story()` | API handler for delete |

---

## File Paths Reference

```
Frontend:
  /Users/darylfung/programming/language_learner/frontend/
    src/
      pages/
        StoryWeaver.tsx          ← Main component (695 lines)
        StoryWeaver.css          ← Styling
      App.tsx                    ← Router
      main.tsx                   ← Entry point
    package.json

Backend:
  /Users/darylfung/programming/language_learner/backend/
    routes/
      stories.py                 ← API endpoints
    services/
      story_service.py           ← Business logic
    database.py                  ← ORM models & Story table
    schemas.py                   ← Request/Response models
    file_storage.py              ← File I/O
    security.py                  ← API key validation
    main.py                      ← FastAPI app
    config.py                    ← Configuration
    requirements.txt             ← Dependencies
    stories.db                   ← SQLite database
    uploads/                     ← Audio files directory

Database:
  stories.db
    stories table
    lyrics table
    resources table
    visuals table
```

