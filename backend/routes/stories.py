from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

from database import get_db, User
from schemas import StoryRequest, StoryDetailResponse, SavedStoryListItem
from security import get_current_user
from utils import format_timestamp
from services.story_service import (
    save_story as save_story_db,
    get_all_stories as get_all_stories_db,
    count_stories as count_stories_db,
    get_story_by_id as get_story_by_id_db,
    delete_story as delete_story_db,
)
from limiter import limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stories"])


@router.post("")
@limiter.limit("30/minute", key_func=get_remote_address)
async def save_story(
    request: Request,
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
            "created_at": format_timestamp(story.created_at)
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving story for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save story.")


@router.get("")
async def get_all_stories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
):
    """Fetch saved stories with optional pagination."""
    try:
        stories = get_all_stories_db(db, current_user.id, limit=limit, offset=offset)
        total = count_stories_db(db, current_user.id)
        return JSONResponse(content={
            "stories": [
                SavedStoryListItem(
                    id=story.id,
                    title=story.title,
                    language=story.language,
                    created_at=format_timestamp(story.created_at),
                    updated_at=format_timestamp(story.updated_at),
                ).model_dump()
                for story in stories
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        logger.error(f"Error fetching stories for user {current_user.id}: {e}", exc_info=True)
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
        logger.error(f"Error fetching story {story_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch story.")


@router.delete("/{story_id}")
@limiter.limit("20/minute", key_func=get_remote_address)
async def delete_story(
    request: Request,
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
        logger.error(f"Error deleting story {story_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete story.")

