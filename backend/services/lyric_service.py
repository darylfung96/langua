import json
import logging
from sqlalchemy.orm import Session

from database import Lyric
from schemas import LyricRequest

logger = logging.getLogger(__name__)


def save_lyric(lyric_data: LyricRequest, db: Session) -> Lyric:
    """Save a lyric/transcript to the database."""
    try:
        # Validate transcript is valid JSON
        transcript_data = json.loads(lyric_data.transcript)
        
        lyric = Lyric(
            title=lyric_data.title,
            video_id=lyric_data.video_id,
            language=lyric_data.language,
            transcript=lyric_data.transcript
        )
        db.add(lyric)
        db.commit()
        db.refresh(lyric)
        return lyric
    except json.JSONDecodeError as e:
        db.rollback()
        logger.error(f"Invalid transcript JSON: {e}")
        raise ValueError("Invalid transcript JSON")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving lyric: {e}")
        raise


def get_all_lyrics(db: Session) -> list:
    """Fetch all saved lyrics."""
    try:
        lyrics = db.query(Lyric).order_by(Lyric.created_at.desc()).all()
        return lyrics
    except Exception as e:
        logger.error(f"Error fetching lyrics: {e}")
        raise


def get_lyric_by_id(lyric_id: str, db: Session) -> Lyric:
    """Fetch a specific lyric by ID."""
    try:
        lyric = db.query(Lyric).filter(Lyric.id == lyric_id).first()
        if not lyric:
            raise ValueError(f"Lyric with ID {lyric_id} not found")
        return lyric
    except Exception as e:
        logger.error(f"Error fetching lyric: {e}")
        raise


def delete_lyric(lyric_id: str, db: Session) -> bool:
    """Delete a lyric by ID."""
    try:
        lyric = db.query(Lyric).filter(Lyric.id == lyric_id).first()
        if not lyric:
            raise ValueError(f"Lyric with ID {lyric_id} not found")
        
        db.delete(lyric)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting lyric: {e}")
        raise
