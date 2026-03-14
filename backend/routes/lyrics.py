from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

from database import get_db, User
from schemas import LyricRequest, LyricDetailResponse, SavedLyricListItem
from security import get_current_user
from utils import format_timestamp
from services.lyric_service import (
    save_lyric as save_lyric_db,
    get_all_lyrics as get_all_lyrics_db,
    count_lyrics as count_lyrics_db,
    get_lyric_by_id as get_lyric_by_id_db,
    delete_lyric as delete_lyric_db,
)
from limiter import limiter
from slowapi.util import get_remote_address

router = APIRouter(tags=["lyrics"])


@router.post("/lyrics")
@limiter.limit("30/minute", key_func=get_remote_address)
async def save_lyric(
    request: Request,
    lyric_data: LyricRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a lyric/transcript to the database."""
    try:
        lyric = save_lyric_db(lyric_data, db, current_user.id)
        return JSONResponse(content={
            "id": lyric.id,
            "title": lyric.title,
            "language": lyric.language,
            "created_at": format_timestamp(lyric.created_at)
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving lyric for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save lyric.")


@router.get("/lyrics")
async def get_all_lyrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
):
    """Fetch saved lyrics with optional pagination."""
    try:
        lyrics = get_all_lyrics_db(db, current_user.id, limit=limit, offset=offset)
        total = count_lyrics_db(db, current_user.id)
        return JSONResponse(content={
            "lyrics": [
                SavedLyricListItem(
                    id=lyric.id,
                    title=lyric.title,
                    language=lyric.language,
                    created_at=format_timestamp(lyric.created_at),
                    updated_at=format_timestamp(lyric.updated_at),
                ).model_dump()
                for lyric in lyrics
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        logger.error(f"Error fetching lyrics for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch lyrics.")


@router.get("/lyrics/{lyric_id}")
async def get_lyric(
    lyric_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch a specific lyric by ID."""
    try:
        lyric = get_lyric_by_id_db(lyric_id, db, current_user.id)
        return JSONResponse(content=LyricDetailResponse.model_validate(lyric).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching lyric {lyric_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch lyric.")


@router.delete("/lyrics/{lyric_id}")
@limiter.limit("20/minute", key_func=get_remote_address)
async def delete_lyric(
    request: Request,
    lyric_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a lyric by ID."""
    try:
        delete_lyric_db(lyric_id, db, current_user.id)
        return JSONResponse(content={"success": True, "message": "Lyric deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting lyric {lyric_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete lyric.")

