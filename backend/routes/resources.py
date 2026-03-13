from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)

from database import get_db
from schemas import ResourceRequest
from security import get_api_key
from services.resource_service import (
    save_resource as save_resource_db,
    get_all_resources as get_all_resources_db,
    get_resource_by_id as get_resource_by_id_db,
    delete_resource as delete_resource_db,
)
from file_storage import get_media_file_path

router = APIRouter(tags=["resources"])


@router.post("")
async def save_resource(
    request: Request,
    api_key: str = Depends(get_api_key),
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
        
        resource_data = ResourceRequest(
            title=title,
            file_name=file_name,
            file_type=file_type,
            language=language,
            transcript=transcript
        )
        
        resource = save_resource_db(resource_data, media_data, db)
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
        logger.error(f"Error saving resource: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save resource: {str(e)}")


@router.get("")
async def get_all_resources(
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch all saved resources for the user."""
    try:
        resources = get_all_resources_db(db)
        return JSONResponse(content={
            "resources": [
                {
                    "id": resource.id,
                    "title": resource.title,
                    "file_name": resource.file_name,
                    "language": resource.language,
                    "has_media": resource.media_file_path is not None,
                    "created_at": resource.created_at.isoformat(),
                    "updated_at": resource.updated_at.isoformat()
                }
                for resource in resources
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch resources: {str(e)}")


@router.get("/{resource_id}")
async def get_resource(
    resource_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Fetch a specific resource by ID."""
    try:
        resource = get_resource_by_id_db(resource_id, db)
        return JSONResponse(content={
            "id": resource.id,
            "title": resource.title,
            "file_name": resource.file_name,
            "file_type": resource.file_type,
            "language": resource.language,
            "transcript": json.loads(resource.transcript),
            "media_file_path": resource.media_file_path,
            "created_at": resource.created_at.isoformat(),
            "updated_at": resource.updated_at.isoformat()
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch resource: {str(e)}")


@router.get("/media/{resource_id}")
async def get_media(
    resource_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Download media file for a resource."""
    try:
        resource = get_resource_by_id_db(resource_id, db)
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
        logger.error(f"Error fetching media: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch media: {str(e)}")


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Delete a resource by ID."""
    try:
        delete_resource_db(resource_id, db)
        return JSONResponse(content={"success": True, "message": "Resource deleted"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting resource: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete resource: {str(e)}")
