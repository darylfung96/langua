# Codebase Issues & Refactoring Notes

> Auto-generated from codebase analysis. Issues are grouped by severity and area.

---

## 🔴 Critical

### 1. No Real Authentication
- All 4 database models hardcode `user_id = Column(String, default="default_user")`
  - `database.py` lines 18, 32, 45, 60
- Single API key shared by all users — no user isolation
- Anyone with the API key can read or delete all data

---

## 🟠 High Priority

### 7. No Tests
- Zero test files exist in either `frontend/` or `backend/`
- No test framework configured (no pytest, vitest, or jest setup)
- 0% code coverage

---

## 🟡 Medium Priority

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

---

## 🟢 Low Priority / Polish

### 21. Gemini Cookies Used for Auth
`routes/image.py` line 21 uses session cookies to authenticate with Gemini:
```python
gemini_client = GeminiClient(GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS, proxy=None)
```
This violates Gemini's Terms of Service and breaks when cookies expire.
**Fix:** Migrate to the official Gemini API with a proper API key.

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
- `BaseService[T]` eliminates CRUD duplication across all 4 domain services
- Pydantic response models with `field_validator` handle JSON deserialization automatically
- Pagination (`limit` / `offset`) on all list endpoints
- File MIME type and size validation on both client and server
- `CORS_ORIGINS` read from environment variable
- React `ErrorBoundary` wraps all routes; 404 catch-all route present
- No debug `console.log` calls in production code
- Named constants for magic numbers (`AUDIO_SAMPLE_RATE`, `TOAST_TIMEOUT_MS`, `TEMP_DIR`)
- `useRef<ReactPlayer>` typed correctly in `Melody.tsx`
- Podcast Pro and Journaling dashboard cards restored with "Coming Soon" state
- `backend/.env.template` documents all required environment variables
- `slowapi` rate limiting (60 req/min per IP) applied globally
