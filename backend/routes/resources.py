from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
import logging
from typing import Optional

logger = logging.getLogger(__name__)

from database import get_db, User
from schemas import ResourceRequest, ResourceDetailResponse, SavedResourceListItem
from security import get_current_user
from services.resource_service import (
    save_resource as save_resource_db,
    get_all_resources as get_all_resources_db,
    get_resource_by_id as get_resource_by_id_db,
    delete_resource as delete_resource_db,
)
from file_storage import get_media_file_path, validate_media_file

router = APIRouter(tags=["resources"])


@router.post("")
async def save_resource(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a transcribed resource with optional media file."""
    try:
        form_data = await request.form()
        
        title = form_data.get('title')
        file_name = form_data.get('file_name')
        file_type = form_data.get('file_type')
        language = form_data.get('language')
        transcript = form_data.get('transcript')
        media_file = form_data.get('media_file')
        
        media_data = None
        if media_file:
            media_data = await media_file.read()
            validate_media_file(media_data, file_type or "")
        
        resource_data = ResourceRequest(
            title=title,
            file_name=file_name,
            file_type=file_type,
            language=language,
            transcript=transcript
        )
        
        resource = save_resource_db(resource_data, db, current_user.id, media_data)
        return JSONResponse(content={
            "id": resource.id,
            "title": resource.title,
            "language": resource.language,
            "media_file_path": resource.media_file_path,
            "created_at": resource.created_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving resource: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save resource.")


@router.get("")
async def get_all_resources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
):
    """Fetch saved resources with optional pagination."""
    try:
        resources = get_all_resources_db(db, current_user.id, limit=limit, offset=offset)
        return JSONResponse(content={
            "resources": [
                SavedResourceListItem(
                    id=resource.id,
                    title=resource.title,
                    file_name=resource.file_name,
                    language=resource.language,
                    has_media=resource.media_file_path is not None,
                    created_at=resource.created_at.isoformat(),
                    updated_at=resource.updated_at.isoformat(),
                ).model_dump()
                for resource in resources
            ],
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch resources.")


@router.get("/{resource_id}")
async def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch a specific resource by ID."""
    try:
        resource = get_resource_by_id_db(resource_id, db, current_user.id)
        return JSONResponse(content=ResourceDetailResponse.model_validate(resource).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch resource.")


@router.get("/media/{resource_id}")
async def get_media(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download media file for a resource."""
    try:
        resource = get_resource_by_id_db(resource_id, db, current_user.id)
        if not resource.media_file_path:
            raise HTTPException(status_code=404, detail="No media file for this resource")
        
        file_path = get_media_file_path(resource.media_file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        return FileResponse(
            path=file_path,
            media_type=resource.file_type,
            filename=resource.file_name
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching media: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch media.")


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resource by ID."""
    try:
        delete_resource_db(resource_id, db, current_user.id)
        return JSONResponse(content={"success": True, "message": "Resource deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting resource: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete resource.")

