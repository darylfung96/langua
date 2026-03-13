import json
import logging
import base64
from sqlalchemy.orm import Session

from database import Story
from schemas import StoryRequest
from file_storage import save_media_file, delete_media_file

logger = logging.getLogger(__name__)


def save_story(story_data: StoryRequest, db: Session) -> Story:
    """Save a story to the database."""
    try:
        # Validate vocabulary is valid JSON
        vocab_data = json.loads(story_data.vocabulary)
        
        # Save audio file if provided
        audio_file_path = None
        if story_data.audio:
            try:
                # Decode base64 audio data
                audio_bytes = base64.b64decode(story_data.audio)
                # Save to filesystem and get the relative path
                audio_file_path = save_media_file(audio_bytes, 'audio.mp3')
            except Exception as e:
                logger.error(f"Error saving audio file: {e}")
                # Continue saving story even if audio save fails
        
        story = Story(
            title=story_data.title,
            story_content=story_data.story_content,
            language=story_data.language,
            vocabulary=story_data.vocabulary,
            quiz=story_data.quiz,
            audio_file_path=audio_file_path
        )
        db.add(story)
        db.commit()
        db.refresh(story)
        return story
    except json.JSONDecodeError as e:
        db.rollback()
        logger.error(f"Invalid vocabulary JSON: {e}")
        raise ValueError("Invalid vocabulary JSON")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving story: {e}")
        raise


def get_all_stories(db: Session) -> list:
    """Fetch all saved stories."""
    try:
        stories = db.query(Story).order_by(Story.created_at.desc()).all()
        return stories
    except Exception as e:
        logger.error(f"Error fetching stories: {e}")
        raise


def get_story_by_id(story_id: str, db: Session) -> Story:
    """Fetch a specific story by ID."""
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")
        return story
    except Exception as e:
        logger.error(f"Error fetching story: {e}")
        raise


def delete_story(story_id: str, db: Session) -> bool:
    """Delete a story by ID."""
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")
        
        # Delete associated audio file if it exists
        if story.audio_file_path:
            delete_media_file(story.audio_file_path)
        
        db.delete(story)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting story: {e}")
        raise
