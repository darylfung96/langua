"""File storage utilities for media uploads."""
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


def save_media_file(file_data: bytes, file_name: str) -> str:
    """
    Save media file to disk and return the relative file path.
    
    Args:
        file_data: Binary file content
        file_name: Original file name
        
    Returns:
        Relative path to saved file (e.g., "uploads/abc123_filename.mp3")
    """
    # Generate unique filename to avoid conflicts
    file_ext = Path(file_name).suffix
    unique_name = f"{uuid.uuid4().hex[:8]}_{Path(file_name).stem}{file_ext}"
    file_path = UPLOADS_DIR / unique_name
    
    with open(file_path, 'wb') as f:
        f.write(file_data)
    
    # Return relative path
    return f"uploads/{unique_name}"


def delete_media_file(file_path: str) -> bool:
    """
    Delete media file from disk.

    Args:
        file_path: Relative path to file

    Returns:
        True if successful, False if file not found
    """
    full_path = (Path(__file__).parent / file_path).resolve()
    if not str(full_path).startswith(str(UPLOADS_DIR.resolve())):
        logger.warning(f"Blocked path traversal attempt: {file_path}")
        return False
    try:
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def get_media_file_path(file_path: str) -> Path:
    """Get full path to media file, restricted to uploads directory."""
    full_path = (Path(__file__).parent / file_path).resolve()
    if not str(full_path).startswith(str(UPLOADS_DIR.resolve())):
        raise ValueError(f"Invalid file path: {file_path}")
    return full_path
