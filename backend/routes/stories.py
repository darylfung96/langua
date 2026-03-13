from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from typing import Optional

from database import get_db, User
from schemas import StoryRequest, StoryDetailResponse, SavedStoryListItem
from security import get_current_user
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a generated story to the database."""
    try:
        story = save_story_db(story_data, db, current_user.id)
        return JSONResponse(content={
            "id": story.id,
            "title": story.title,
            "language": story.language,
            "created_at": story.created_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving story: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save story.")


@router.get("")
async def get_all_stories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
):
    """Fetch saved stories with optional pagination."""
    try:
        stories = get_all_stories_db(db, current_user.id, limit=limit, offset=offset)
        return JSONResponse(content={
            "stories": [
                SavedStoryListItem(
                    id=story.id,
                    title=story.title,
                    language=story.language,
                    created_at=story.created_at.isoformat(),
                    updated_at=story.updated_at.isoformat(),
                ).model_dump()
                for story in stories
            ],
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch stories.")


@router.get("/{story_id}")
async def get_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch a specific story by ID."""
    try:
        story = get_story_by_id_db(story_id, db, current_user.id)
        return JSONResponse(content=StoryDetailResponse.model_validate(story).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch story.")


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a story by ID."""
    try:
        delete_story_db(story_id, db, current_user.id)
        return JSONResponse(content={"success": True, "message": "Story deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting story: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete story.")

