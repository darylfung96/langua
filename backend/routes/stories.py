from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

from database import get_db
from schemas import StoryRequest
from security import get_api_key
from services.story_service import (
    save_story as save_story_db,
    get_all_stories as get_all_stories_db,
    get_story_by_id as get_story_by_id_db,
    delete_story as delete_story_db,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stories"])


@router.post("")
async def save_story(
    story_data: StoryRequest,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Save a generated story to the database."""
    try:
        story = save_story_db(story_data, db)
        return JSONResponse(content={
            "id": story.id,
            "title": story.title,
            "language": story.language,
            "created_at": story.created_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving story: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save story: {str(e)}")


@router.get("")
async def get_all_stories(
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch all saved stories for the user."""
    try:
        stories = get_all_stories_db(db)
        return JSONResponse(content={
            "stories": [
                {
                    "id": story.id,
                    "title": story.title,
                    "language": story.language,
                    "created_at": story.created_at.isoformat(),
                    "updated_at": story.updated_at.isoformat()
                }
                for story in stories
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stories: {str(e)}")


@router.get("/{story_id}")
async def get_story(
    story_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch a specific story by ID."""
    try:
        story = get_story_by_id_db(story_id, db)
        import json
        return JSONResponse(content={
            "id": story.id,
            "title": story.title,
            "story_content": story.story_content,
            "language": story.language,
            "vocabulary": json.loads(story.vocabulary),
            "quiz": json.loads(story.quiz) if story.quiz else None,
            "audio_file_path": story.audio_file_path,
            "created_at": story.created_at.isoformat(),
            "updated_at": story.updated_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch story: {str(e)}")


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Delete a story by ID."""
    try:
        delete_story_db(story_id, db)
        return JSONResponse(content={"success": True, "message": "Story deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting story: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete story: {str(e)}")
