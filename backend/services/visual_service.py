import json
import logging
from sqlalchemy.orm import Session

from database import Visual
from schemas import VisualRequest

logger = logging.getLogger(__name__)


def save_visual(visual_data: VisualRequest, db: Session = None) -> Visual:
    """Save a generated visual to the database."""
    try:
        # Validate images is valid JSON
        images_data = json.loads(visual_data.images)
        
        visual = Visual(
            word=visual_data.word,
            language=visual_data.language,
            images=visual_data.images,
            prompt=visual_data.prompt,
            explanation=visual_data.explanation
        )
        db.add(visual)
        db.commit()
        db.refresh(visual)
        return visual
    except json.JSONDecodeError as e:
        db.rollback()
        logger.error(f"Invalid images JSON: {e}")
        raise ValueError("Invalid images JSON")
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving visual: {e}")
        raise


def get_all_visuals(db: Session) -> list:
    """Fetch all saved visuals."""
    try:
        visuals = db.query(Visual).order_by(Visual.created_at.desc()).all()
        return visuals
    except Exception as e:
        logger.error(f"Error fetching visuals: {e}")
        raise


def get_visual_by_id(visual_id: str, db: Session) -> Visual:
    """Fetch a specific visual by ID."""
    try:
        visual = db.query(Visual).filter(Visual.id == visual_id).first()
        if not visual:
            raise ValueError(f"Visual with ID {visual_id} not found")
        return visual
    except Exception as e:
        logger.error(f"Error fetching visual: {e}")
        raise


def delete_visual(visual_id: str, db: Session) -> bool:
    """Delete a visual by ID."""
    try:
        visual = db.query(Visual).filter(Visual.id == visual_id).first()
        if not visual:
            raise ValueError(f"Visual with ID {visual_id} not found")
        
        db.delete(visual)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting visual: {e}")
        raise
