# Backend Structure

The backend has been refactored following best practices for maintainability and scalability.

## Directory Structure

```
backend/
├── main.py                 # Application entry point
├── config.py              # Configuration settings (environment variables)
├── database.py            # Database setup, models, and session management
├── schemas.py             # Pydantic request/response models
├── security.py            # API key authentication
├── utils.py               # Utility functions (extract_video_id, prompts, etc.)
├── services/
│   ├── __init__.py
│   └── story_service.py   # Business logic for story operations (CRUD)
└── routes/
    ├── __init__.py
    ├── stories.py         # /stories endpoints (save, get, delete)
    ├── transcribe.py      # /transcribe endpoint (audio transcription)
    ├── youtube.py         # /youtube-transcript endpoint
    └── image.py           # /generate-image endpoint
```

## Architecture

### Layers

1. **Main (main.py)**
   - FastAPI app initialization
   - Middleware setup (CORS)
   - Router registration
   - Server startup

2. **Routes**
   - Endpoint handlers
   - Request validation
   - Error handling and HTTP responses
   - Dependency injection

3. **Services**
   - Business logic
   - Database operations
   - Data transformations

4. **Database**
   - SQLAlchemy models
   - Database connection
   - Session management

5. **Config**
   - Environment variables
   - Constants
   - Settings

6. **Schemas**
   - Pydantic models for request/response validation

7. **Security**
   - Authentication logic
   - API key validation

## Benefits

✅ **Separation of Concerns** - Each module has a single responsibility
✅ **Reusability** - Services can be used across multiple routes
✅ **Testability** - Easy to unit test individual components
✅ **Scalability** - Easy to add new routes and services
✅ **Maintainability** - Clear structure makes debugging and updates easier
✅ **Code Organization** - Routes logically grouped by feature

## Adding New Features

### To add a new endpoint:

1. Create a new file in `routes/` (e.g., `routes/my_feature.py`)
2. Define your router and endpoints
3. If needed, add business logic to `services/`
4. Import and register the router in `main.py`

Example:
```python
# routes/my_feature.py
from fastapi import APIRouter
from security import get_api_key

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.get("")
async def get_data(api_key: str = Depends(get_api_key)):
    return {"data": "example"}
```

Then in `main.py`:
```python
from routes.my_feature import router as my_feature_router
app.include_router(my_feature_router)
```

## Running the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

API documentation available at `http://localhost:8000/docs`
