from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)

from database import get_db
from schemas import LyricRequest
from security import get_api_key
from services.lyric_service import (
    save_lyric as save_lyric_db,
    get_all_lyrics as get_all_lyrics_db,
    get_lyric_by_id as get_lyric_by_id_db,
    delete_lyric as delete_lyric_db,
)

router = APIRouter(tags=["lyrics"])


@router.post("/lyrics")
async def save_lyric(
    lyric_data: LyricRequest,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Save a lyric/transcript to the database."""
    try:
        lyric = save_lyric_db(lyric_data, db)
        return JSONResponse(content={
            "id": lyric.id,
            "title": lyric.title,
            "language": lyric.language,
            "created_at": lyric.created_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving lyric: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save lyric: {str(e)}")


@router.get("/lyrics")
async def get_all_lyrics(
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch all saved lyrics for the user."""
    try:
        lyrics = get_all_lyrics_db(db)
        return JSONResponse(content={
            "lyrics": [
                {
                    "id": lyric.id,
                    "title": lyric.title,
                    "language": lyric.language,
                    "created_at": lyric.created_at.isoformat(),
                    "updated_at": lyric.updated_at.isoformat()
                }
                for lyric in lyrics
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lyrics: {str(e)}")


@router.get("/lyrics/{lyric_id}")
async def get_lyric(
    lyric_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch a specific lyric by ID."""
    try:
        lyric = get_lyric_by_id_db(lyric_id, db)
        return JSONResponse(content={
            "id": lyric.id,
            "title": lyric.title,
            "video_id": lyric.video_id,
            "language": lyric.language,
            "transcript": json.loads(lyric.transcript),
            "created_at": lyric.created_at.isoformat(),
            "updated_at": lyric.updated_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lyric: {str(e)}")


@router.delete("/lyrics/{lyric_id}")
async def delete_lyric(
    lyric_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Delete a lyric by ID."""
    try:
        delete_lyric_db(lyric_id, db)
        return JSONResponse(content={"success": True, "message": "Lyric deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting lyric: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete lyric: {str(e)}")
