from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

from db import get_db, User
from schemas import VisualRequest, VisualDetailResponse, SavedVisualListItem
from core.security import get_current_user
from core.utils import format_timestamp
from services.visual_service import (
    save_visual as save_visual_db,
    get_all_visuals as get_all_visuals_db,
    count_visuals as count_visuals_db,
    get_visual_by_id as get_visual_by_id_db,
    delete_visual as delete_visual_db,
)
from core.limiter import limiter
from slowapi.util import get_remote_address

router = APIRouter(tags=["visuals"])


@router.post("")
@limiter.limit("30/minute", key_func=get_remote_address)
async def save_visual(
    request: Request,
    visual_data: VisualRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a generated visual to the database."""
    try:
        visual = save_visual_db(visual_data, db, current_user.id)
        return JSONResponse(content={
            "id": visual.id,
            "word": visual.word,
            "language": visual.language,
            "created_at": format_timestamp(visual.created_at)
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving visual for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save visual.")


@router.get("")
async def get_all_visuals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
):
    """Fetch saved visuals with optional pagination."""
    try:
        visuals = get_all_visuals_db(db, current_user.id, limit=limit, offset=offset)
        total = count_visuals_db(db, current_user.id)
        return JSONResponse(content={
            "visuals": [
                SavedVisualListItem(
                    id=visual.id,
                    word=visual.word,
                    language=visual.language,
                    created_at=format_timestamp(visual.created_at),
                    updated_at=format_timestamp(visual.updated_at),
                ).model_dump()
                for visual in visuals
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        logger.error(f"Error fetching visuals for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch visuals.")


@router.get("/{visual_id}")
async def get_visual(
    visual_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch a specific visual by ID."""
    try:
        visual = get_visual_by_id_db(visual_id, db, current_user.id)
        return JSONResponse(content=VisualDetailResponse.model_validate(visual).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching visual {visual_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch visual.")


@router.delete("/{visual_id}")
@limiter.limit("20/minute", key_func=get_remote_address)
async def delete_visual(
    request: Request,
    visual_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a visual by ID."""
    try:
        delete_visual_db(visual_id, db, current_user.id)
        return JSONResponse(content={"success": True, "message": "Visual deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting visual {visual_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete visual.")

