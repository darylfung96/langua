import json
import logging
from sqlalchemy.orm import Session

from database import Resource
from schemas import ResourceRequest
from file_storage import save_media_file, delete_media_file

logger = logging.getLogger(__name__)


def save_resource(resource_data: ResourceRequest, media_file_data: bytes = None, db: Session = None) -> Resource:
    """Save a transcribed resource to the database."""
    try:
        # Validate transcript is valid JSON
        transcript_data = json.loads(resource_data.transcript)
        
        media_file_path = None
        if media_file_data:
            media_file_path = save_media_file(media_file_data, resource_data.file_name)
        
        resource = Resource(
            title=resource_data.title,
            file_name=resource_data.file_name,
            file_type=resource_data.file_type,
            language=resource_data.language,
            transcript=resource_data.transcript,
            media_file_path=media_file_path
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)
        return resource
    except json.JSONDecodeError as e:
        db.rollback()
        logger.error(f"Invalid transcript JSON: {e}")
        raise ValueError("Invalid transcript JSON")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving resource: {e}")
        raise


def get_all_resources(db: Session) -> list:
    """Fetch all saved resources."""
    try:
        resources = db.query(Resource).order_by(Resource.created_at.desc()).all()
        return resources
    except Exception as e:
        logger.error(f"Error fetching resources: {e}")
        raise


def get_resource_by_id(resource_id: str, db: Session) -> Resource:
    """Fetch a specific resource by ID."""
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise ValueError(f"Resource with ID {resource_id} not found")
        return resource
    except Exception as e:
        logger.error(f"Error fetching resource: {e}")
        raise


def delete_resource(resource_id: str, db: Session) -> bool:
    """Delete a resource by ID."""
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise ValueError(f"Resource with ID {resource_id} not found")
        
        # Delete associated media file if it exists
        if resource.media_file_path:
            delete_media_file(resource.media_file_path)
        
        db.delete(resource)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting resource: {e}")
        raise
