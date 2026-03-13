from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)

from database import get_db
from schemas import VisualRequest
from security import get_api_key
from services.visual_service import (
    save_visual as save_visual_db,
    get_all_visuals as get_all_visuals_db,
    get_visual_by_id as get_visual_by_id_db,
    delete_visual as delete_visual_db,
)

router = APIRouter(tags=["visuals"])


@router.post("")
async def save_visual(
    visual_data: VisualRequest,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Save a generated visual to the database."""
    try:
        visual = save_visual_db(visual_data, db)
        return JSONResponse(content={
            "id": visual.id,
            "word": visual.word,
            "language": visual.language,
            "created_at": visual.created_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving visual: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save visual: {str(e)}")


@router.get("")
async def get_all_visuals(
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch all saved visuals for the user."""
    try:
        visuals = get_all_visuals_db(db)
        return JSONResponse(content={
            "visuals": [
                {
                    "id": visual.id,
                    "word": visual.word,
                    "language": visual.language,
                    "created_at": visual.created_at.isoformat(),
                    "updated_at": visual.updated_at.isoformat()
                }
                for visual in visuals
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch visuals: {str(e)}")


@router.get("/{visual_id}")
async def get_visual(
    visual_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch a specific visual by ID."""
    try:
        visual = get_visual_by_id_db(visual_id, db)
        return JSONResponse(content={
            "id": visual.id,
            "word": visual.word,
            "language": visual.language,
            "images": json.loads(visual.images),
            "prompt": visual.prompt,
            "explanation": visual.explanation,
            "created_at": visual.created_at.isoformat(),
            "updated_at": visual.updated_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch visual: {str(e)}")


@router.delete("/{visual_id}")
async def delete_visual(
    visual_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Delete a visual by ID."""
    try:
        delete_visual_db(visual_id, db)
        return JSONResponse(content={"success": True, "message": "Visual deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting visual: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete visual: {str(e)}")
