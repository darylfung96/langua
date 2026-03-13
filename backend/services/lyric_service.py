import json
import logging
from sqlalchemy.orm import Session

from database import Lyric
from schemas import LyricRequest
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class LyricService(BaseService[Lyric]):
    model = Lyric

    def save(self, lyric_data: LyricRequest, db: Session, user_id: str) -> Lyric:
        """Save a lyric/transcript to the database."""
        try:
            json.loads(lyric_data.transcript)  # validate JSON

            lyric = Lyric(
                user_id=user_id,
                title=lyric_data.title,
                video_id=lyric_data.video_id,
                language=lyric_data.language,
                transcript=lyric_data.transcript,
            )
            db.add(lyric)
            db.commit()
            db.refresh(lyric)
            return lyric
        except json.JSONDecodeError as e:
            db.rollback()
            logger.error(f"Invalid transcript JSON: {e}")
            raise ValueError("Invalid transcript JSON")
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving lyric: {e}")
            raise


_service = LyricService()


# ---------------------------------------------------------------------------
# Module-level convenience functions kept for backward compatibility
# ---------------------------------------------------------------------------

def save_lyric(lyric_data: LyricRequest, db: Session, user_id: str) -> Lyric:
    return _service.save(lyric_data, db, user_id)


def get_all_lyrics(db: Session, user_id: str, limit: int | None = None, offset: int = 0) -> list:
    return _service.get_all(db, user_id, limit=limit, offset=offset)


def get_lyric_by_id(lyric_id: str, db: Session, user_id: str) -> Lyric:
    return _service.get_by_id(lyric_id, db, user_id)


def delete_lyric(lyric_id: str, db: Session, user_id: str) -> bool:
    return _service.delete(lyric_id, db, user_id)

