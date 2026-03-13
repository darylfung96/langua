import json
import logging
from sqlalchemy.orm import Session

from database import Visual
from schemas import VisualRequest
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class VisualService(BaseService[Visual]):
    model = Visual

    def save(self, visual_data: VisualRequest, db: Session, user_id: str) -> Visual:
        """Save a generated visual to the database."""
        try:
            json.loads(visual_data.images)  # validate JSON

            visual = Visual(
                user_id=user_id,
                word=visual_data.word,
                language=visual_data.language,
                images=visual_data.images,
                prompt=visual_data.prompt,
                explanation=visual_data.explanation,
            )
            db.add(visual)
            db.commit()
            db.refresh(visual)
            return visual
        except json.JSONDecodeError as e:
            db.rollback()
            logger.error(f"Invalid images JSON: {e}")
            raise ValueError("Invalid images JSON")
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving visual: {e}")
            raise


_service = VisualService()


# ---------------------------------------------------------------------------
# Module-level convenience functions kept for backward compatibility
# ---------------------------------------------------------------------------

def save_visual(visual_data: VisualRequest, db: Session, user_id: str) -> Visual:
    return _service.save(visual_data, db, user_id)


def get_all_visuals(db: Session, user_id: str, limit: int | None = None, offset: int = 0) -> list:
    return _service.get_all(db, user_id, limit=limit, offset=offset)


def get_visual_by_id(visual_id: str, db: Session, user_id: str) -> Visual:
    return _service.get_by_id(visual_id, db, user_id)


def delete_visual(visual_id: str, db: Session, user_id: str) -> bool:
    return _service.delete(visual_id, db, user_id)

