"""File storage utilities for media uploads."""
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Allowed MIME types and their canonical file extensions
ALLOWED_MEDIA_TYPES: dict[str, str] = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/wave": ".wav",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/ogg": ".ogv",
}

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


def validate_media_file(file_data: bytes, mime_type: str) -> None:
    """Raise ValueError if the file exceeds the size limit or has a disallowed type.

    Args:
        file_data: Binary file content.
        mime_type: MIME type reported by the client (e.g. "audio/mpeg").

    Raises:
        ValueError: When validation fails.
    """
    if len(file_data) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"File size {len(file_data) / (1024 * 1024):.1f} MB exceeds the "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
        )
    # Normalise the MIME type (strip parameters like "; codecs=…")
    base_mime = mime_type.split(";")[0].strip().lower() if mime_type else ""
    if base_mime not in ALLOWED_MEDIA_TYPES:
        allowed = ", ".join(sorted(ALLOWED_MEDIA_TYPES))
        raise ValueError(
            f"File type '{base_mime}' is not allowed. Allowed types: {allowed}"
        )


def save_media_file(file_data: bytes, file_name: str) -> str:
    """
    Save media file to disk and return the relative file path.

    Args:
        file_data: Binary file content.
        file_name: Original file name.

    Returns:
        Relative path to saved file (e.g., "uploads/abc123_filename.mp3")
    """
    file_ext = Path(file_name).suffix
    unique_name = f"{uuid.uuid4().hex[:8]}_{Path(file_name).stem}{file_ext}"
    file_path = UPLOADS_DIR / unique_name

    with open(file_path, "wb") as f:
        f.write(file_data)

    return f"uploads/{unique_name}"


def delete_media_file(file_path: str) -> bool:
    """
    Delete media file from disk.

    Args:
        file_path: Relative path to file.

    Returns:
        True if successful, False if file not found.
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

