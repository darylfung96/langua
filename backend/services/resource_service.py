import json
import logging
from sqlalchemy.orm import Session

from database import Resource
from schemas import ResourceRequest
from file_storage import save_media_file, delete_media_file
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class ResourceService(BaseService[Resource]):
    model = Resource

    def save(
        self,
        resource_data: ResourceRequest,
        db: Session,
        user_id: str,
        media_file_data: bytes = None,
    ) -> Resource:
        """Save a transcribed resource atomically.

        The media file is written only after the DB row is validated (flushed),
        so a DB error won't leave an orphaned file on disk.
        """
        try:
            json.loads(resource_data.transcript)  # validate JSON

            resource = Resource(
                user_id=user_id,
                title=resource_data.title,
                file_name=resource_data.file_name,
                file_type=resource_data.file_type,
                language=resource_data.language,
                transcript=resource_data.transcript,
                media_file_path=None,
            )
            db.add(resource)
            db.flush()  # Validate DB constraints before touching the filesystem

            media_file_path = None
            if media_file_data:
                try:
                    media_file_path = save_media_file(media_file_data, resource_data.file_name)
                    resource.media_file_path = media_file_path
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error saving media file: {e}", exc_info=True)
                    raise ValueError(f"Failed to save media file: {str(e)[:100]}")

            db.commit()
            db.refresh(resource)
            return resource
        except json.JSONDecodeError as e:
            db.rollback()
            logger.error(f"Invalid transcript JSON: {e}")
            raise ValueError("Invalid transcript JSON")
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            if 'media_file_path' in locals() and media_file_path:
                delete_media_file(media_file_path)
            logger.error(f"Error saving resource: {e}", exc_info=True)
            raise

    def _pre_delete(self, record: Resource) -> None:
        if record.media_file_path:
            delete_media_file(record.media_file_path)


_service = ResourceService()


# ---------------------------------------------------------------------------
# Module-level convenience functions kept for backward compatibility
# ---------------------------------------------------------------------------

def save_resource(resource_data: ResourceRequest, db: Session, user_id: str, media_file_data: bytes = None) -> Resource:
    return _service.save(resource_data, db, user_id, media_file_data)


def get_all_resources(db: Session, user_id: str, limit: int | None = None, offset: int = 0) -> list:
    return _service.get_all(db, user_id, limit=limit, offset=offset)


def get_resource_by_id(resource_id: str, db: Session, user_id: str) -> Resource:
    return _service.get_by_id(resource_id, db, user_id)


def delete_resource(resource_id: str, db: Session, user_id: str) -> bool:
    return _service.delete(resource_id, db, user_id)

