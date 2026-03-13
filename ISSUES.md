# Codebase Issues & Refactoring Notes

> Auto-generated from codebase analysis. Issues are grouped by severity and area.

---

## 🔴 Critical

### 1. No Real Authentication
- All 4 database models hardcode `user_id = Column(String, default="default_user")`
  - `database.py` lines 18, 32, 45, 60
- Single API key shared by all users — no user isolation
- Anyone with the API key can read or delete all data

### 2. Secrets Committed to Repository
- `backend/.env` contains real credentials:
  - `WHISPER_API_KEY`
  - `GEMINI_COOKIE_1PSID`
  - `GEMINI_COOKIE_1PSIDTS`
- **Action required: revoke these keys immediately if they are in git history**
- Add `.env` to `.gitignore` for both `backend/` and `frontend/`

### 3. Backend API Key Exposed in Frontend
- `frontend/.env` sets `VITE_BACKEND_API_KEY` which Vite bundles into compiled JS
- Visible to anyone via browser DevTools → Network tab
- The backend API key should never be in frontend code

---

## 🟠 High Priority

### 4. Massive Code Duplication in Backend Services
All 4 service files repeat identical CRUD logic (~350 duplicated lines):
- `services/story_service.py` lines 13–50
- `services/lyric_service.py` lines 11–34
- `services/resource_service.py` lines 12–41
- `services/visual_service.py` lines 11–35

Each implements the same `save_xxx`, `get_all_xxx`, `get_xxx_by_id`, `delete_xxx` pattern.
**Fix:** Extract a generic `BaseService[T]` class.

### 5. Hardcoded Backend URL in Frontend
`http://localhost:8000` is hardcoded in 5 places — cannot switch to a production backend without find-and-replace:
- `StoryWeaver.tsx` line 69
- `Melody.tsx` line 33
- `ResourceLearner.tsx` line 45
- `VisualMemory.tsx` lines 60, 163

**Fix:** Use `import.meta.env.VITE_BACKEND_URL` consistently. A `VITE_BACKEND_URL` env var already partially exists.

### 6. `print()` and `traceback.print_exc()` in Route Handlers
Debugging code left in production paths (10+ instances):
- `routes/stories.py` lines 36–39, 105–108
- `routes/lyrics.py` lines 37–40, 104–107
- `routes/resources.py` lines 60–63, 142–143, 159–162
- `routes/visual.py` lines 37–40, 105–108

A `logger` is already imported in these files — it is just not being used.
**Fix:** Replace all `print(...)` / `traceback.print_exc()` calls with `logger.error(..., exc_info=True)`.

### 7. No Tests
- Zero test files exist in either `frontend/` or `backend/`
- No test framework configured (no pytest, vitest, or jest setup)
- 0% code coverage

### 8. Manual JSON Serialization in Every Route
All routes manually call `json.loads(...)` on stored string columns and re-serialize in responses:
- `routes/stories.py` line 81: `json.loads(story.vocabulary)`
- `routes/resources.py` line 107: `json.loads(resource.transcript)`
- `routes/visual.py` line 80: `json.loads(visual.images)`

**Fix:** Use Pydantic response models with proper serialization instead of manual field mapping.

---

## 🟡 Medium Priority

### 9. No Pagination on Database Queries
All list endpoints return every row with no limit:
```python
# services/story_service.py line 55
db.query(Story).order_by(Story.created_at.desc()).all()
```
Same pattern in `lyric_service.py`, `resource_service.py`, `visual_service.py`.
**Fix:** Add `limit` / `offset` parameters and enforce a reasonable default page size.

### 10. No File Validation Before Upload
`ResourceLearner.tsx` sends files to the backend with no client-side size or type check (line 82).
The backend `file_storage.py` also has no size guard beyond the global `WHISPER_MAX_UPLOAD_SIZE` setting.
**Fix:** Validate file size and MIME type on both client and server before processing.

### 11. Frontend Pages Are Too Large / No Custom Hooks
All business logic lives inside page components with no extraction:
- `StoryWeaver.tsx` — 695 lines
- `ResourceLearner.tsx` — 526 lines
- `VisualMemory.tsx` — 463 lines
- `Melody.tsx` — 403 lines

Every page duplicates the same fetch/save/load/delete + loading/error state pattern (~600 lines of repeated logic).
**Fix:** Extract reusable custom hooks, e.g.:
- `useApi(endpoint)` — fetch, save, delete with shared loading/error state
- `useMediaPlayer(ref)` — playback controls shared across pages

### 12. Bare `except Exception` Handlers
23 route handler try/except blocks catch `Exception` broadly, including `SystemExit` and `KeyboardInterrupt`.
**Fix:** Catch specific exception types (`ValueError`, `SQLAlchemyError`, `json.JSONDecodeError`) before falling through to a generic handler.

### 13. CORS Hardcoded to Localhost
`config.py` line 23:
```python
CORS_ORIGINS = ["http://localhost:5173"]
```
Cannot deploy without modifying source code.
**Fix:** Read from an environment variable, e.g. `CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")`.

### 14. No Error Boundaries in React
No `ErrorBoundary` component wraps any routes or pages. An unhandled render error crashes the entire app.
**Fix:** Wrap routes in an `ErrorBoundary` in `App.tsx`.

### 15. No 404 Route
`App.tsx` has no catch-all route. Navigating to an unknown path shows a blank page.
**Fix:** Add `<Route path="*" element={<NotFound />} />`.

---

## 🟢 Low Priority / Polish

### 16. `console.log` / `console.error` in Production Code
25+ console statements remain from debugging:
- `StoryWeaver.tsx` lines 123, 127, 136, 143, 146
- `Melody.tsx` line 60
- `VisualMemory.tsx` line 74

**Fix:** Remove or gate behind a `DEBUG` flag. ESLint `no-console` rule can enforce this.

### 17. Magic Numbers and Hardcoded Values
- `StoryWeaver.tsx` line 25: audio sample rate `24000` hardcoded
- `StoryWeaver.tsx` line 169 / `Melody.tsx` line 110: success toast timeout `2000` ms hardcoded
- `routes/image.py` line 78: `/tmp/` hardcoded as temp directory
- `config.py` line 19: Whisper model `"medium"` hardcoded

### 18. `useRef<any>` Instead of Specific Types
`Melody.tsx` line 30:
```typescript
const playerRef = useRef<any>(null);
```
**Fix:** Use the specific type from the `react-player` package.

### 19. Stub Pages with No Implementation
`Writing.tsx` and `Podcasts.tsx` are each 17 lines and render nothing useful.
Dashboard cards for these features are commented out in `Dashboard.tsx` (lines 21–27, 35–41).
**Fix:** Either remove them or add a "Coming Soon" placeholder and restore the dashboard cards.

### 20. No `backend/.env.template`
Frontend has `.env.template`; backend does not.
New contributors have no way to know which environment variables are required.
**Fix:** Add `backend/.env.template` listing all required variables with placeholder values.

### 21. Gemini Cookies Used for Auth
`routes/image.py` line 21 uses session cookies to authenticate with Gemini:
```python
gemini_client = GeminiClient(GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS, proxy=None)
```
This violates Gemini's Terms of Service and breaks when cookies expire.
**Fix:** Migrate to the official Gemini API with a proper API key.

### 22. No Rate Limiting
No rate limiter middleware is applied to any endpoint.
**Fix:** Add `slowapi` or FastAPI middleware to limit requests per IP/key.

---

## ✅ What's Already Good

- Clean **Routes → Services → Database** separation in the backend
- **TypeScript** throughout the frontend; **Pydantic** schemas in the backend
- **UUID primary keys** — no collision risk
- **SQLAlchemy ORM** — no raw SQL queries
- **ESLint** configured with React + TypeScript rules
- **CSS scoped per component** with CSS variables for theming
- API key authentication present (even if implementation is weak)
- Input validation exists in some endpoints (e.g. `routes/image.py` line 40)
