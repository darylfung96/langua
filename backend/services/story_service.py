import json
import logging
import base64
from sqlalchemy.orm import Session

from database import Story
from schemas import StoryRequest
from file_storage import save_media_file, delete_media_file
from services.base_service import BaseService

logger = logging.getLogger(__name__)


MAX_AUDIO_BASE64_BYTES = 70_000_000  # ~50 MB binary after base64 encoding (base64 ≈ 1.37× input)


class StoryService(BaseService[Story]):
    model = Story

    def save(self, story_data: StoryRequest, db: Session, user_id: str) -> Story:
        """Save a story to the database atomically.

        File is written only after the DB row is validated (flushed), so a DB
        error won't leave an orphaned file on disk.
        """
        try:
            json.loads(story_data.vocabulary)  # validate JSON

            if story_data.audio and len(story_data.audio) > MAX_AUDIO_BASE64_BYTES:
                raise ValueError("Audio file too large (maximum 50 MB)")

            story = Story(
                user_id=user_id,
                title=story_data.title,
                story_content=story_data.story_content,
                language=story_data.language,
                vocabulary=story_data.vocabulary,
                quiz=story_data.quiz,
                audio_file_path=None,
            )
            db.add(story)
            db.flush()  # Validate DB constraints before touching the filesystem

            audio_file_path = None
            if story_data.audio:
                try:
                    audio_bytes = base64.b64decode(story_data.audio)
                    audio_file_path = save_media_file(audio_bytes, "audio.mp3")
                    story.audio_file_path = audio_file_path
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error saving audio file: {e}", exc_info=True)
                    raise ValueError(f"Failed to process audio: {str(e)[:100]}")

            db.commit()
            db.refresh(story)
            return story
        except json.JSONDecodeError as e:
            db.rollback()
            logger.error(f"Invalid vocabulary JSON: {e}")
            raise ValueError("Invalid vocabulary JSON")
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            if 'audio_file_path' in locals() and audio_file_path:
                delete_media_file(audio_file_path)
            logger.error(f"Error saving story: {e}", exc_info=True)
            raise

    def _pre_delete(self, record: Story) -> None:
        if record.audio_file_path:
            delete_media_file(record.audio_file_path)


_service = StoryService()


# ---------------------------------------------------------------------------
# Module-level convenience functions kept for backward compatibility
# ---------------------------------------------------------------------------

def save_story(story_data: StoryRequest, db: Session, user_id: str) -> Story:
    return _service.save(story_data, db, user_id)


def get_all_stories(db: Session, user_id: str, limit: int | None = None, offset: int = 0) -> list:
    return _service.get_all(db, user_id, limit=limit, offset=offset)


def get_story_by_id(story_id: str, db: Session, user_id: str) -> Story:
    return _service.get_by_id(story_id, db, user_id)


def delete_story(story_id: str, db: Session, user_id: str) -> bool:
    return _service.delete(story_id, db, user_id)

