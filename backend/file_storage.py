"""File storage utilities for media uploads with security validation."""
import logging
import os
import uuid
import re
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Allowed MIME types with extensions and magic byte signatures
ALLOWED_MEDIA_TYPES: dict[str, dict] = {
    "audio/mpeg": {
        "extensions": [".mp3"],
        "magic": [b"ID3", b"\xff\xfb"]  # MP3 ID3 tag or frame header
    },
    "audio/mp3": {
        "extensions": [".mp3"],
        "magic": [b"ID3", b"\xff\xfb"]
    },
    "audio/wav": {
        "extensions": [".wav"],
        "magic": [b"RIFF"]  # RIFF WAVE format
    },
    "audio/x-wav": {
        "extensions": [".wav"],
        "magic": [b"RIFF"]
    },
    "audio/wave": {
        "extensions": [".wav"],
        "magic": [b"RIFF"]
    },
    "audio/ogg": {
        "extensions": [".ogg"],
        "magic": [b"OggS"]  # Ogg container
    },
    "audio/flac": {
        "extensions": [".flac"],
        "magic": [b"fLaC"]  # FLAC magic bytes
    },
    "video/mp4": {
        "extensions": [".mp4", ".m4a"],
        "magic": [b"\x00\x00\x00\x18\x66\x74\x79\x70\x6d\x70\x34\x31"]  # ftyp box
    },
    "video/webm": {
        "extensions": [".webm"],
        "magic": [b"\x1a\x45\xdf\xa3"]  # EBML header
    },
    "video/ogg": {
        "extensions": [".ogv"],
        "magic": [b"OggS"]
    },
}

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
_MAGIC_BYTE_CHECK_SIZE = 16  # Check first 16 bytes for magic signatures


def _detect_mime_from_magic(file_data: bytes, claimed_mime: str) -> str:
    """
    Detect MIME type by inspecting file magic bytes.
    Returns the detected MIME or raises ValueError if not matching allowed types.
    """
    header = file_data[:_MAGIC_BYTE_CHECK_SIZE]

    # Check against known magic signatures
    for mime, info in ALLOWED_MEDIA_TYPES.items():
        for magic in info["magic"]:
            if header.startswith(magic):
                # If we found a match, verify it's in the claimed MIME or any allowed MIME
                if mime == claimed_mime:
                    return mime
                # If the claimed MIME is a different allowed type, still accept if file is valid
                # (e.g., client says audio/mpeg but file is audio/mp3 - both map to same type)
                for alt_mime in ALLOWED_MEDIA_TYPES:
                    if claimed_mime == alt_mime and mime in ALLOWED_MEDIA_TYPES:
                        return mime

    raise ValueError(f"File content does not match the declared type {claimed_mime}")


def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """
    Verify that target_path resolves to a location within base_dir.
    Uses realpath() to resolve all symlinks and prevents directory traversal.
    """
    try:
        resolved_base = os.path.realpath(str(base_dir))
        resolved_target = os.path.realpath(str(target_path))
        return resolved_target.startswith(resolved_base + os.sep) or resolved_target == resolved_base
    except (OSError, ValueError):
        return False


def validate_media_file(file_data: bytes, mime_type: str) -> None:
    """Raise ValueError if the file exceeds the size limit or fails validation.

    Performs both MIME header validation AND file content validation (magic bytes)
    to prevent malicious uploads with forged Content-Type headers.

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
        allowed = ", ".join(sorted(ALLOWED_MEDIA_TYPES.keys()))
        raise ValueError(
            f"File type '{base_mime}' is not allowed. Allowed types: {allowed}"
        )

    # CRITICAL: Validate actual file content using magic bytes, not just client-provided header
    try:
        _detect_mime_from_magic(file_data, base_mime)
    except ValueError as e:
        raise ValueError(f"File content validation failed: {e}")


def save_media_file(file_data: bytes, file_name: str) -> str:
    """
    Save media file to disk with atomic write and return the relative file path.
    Validates that the final file is within the uploads directory.

    Args:
        file_data: Binary file content.
        file_name: Original file name (used only for extension).

    Returns:
        Relative path to saved file (e.g., "uploads/abc123_filename.mp3")
    """
    # Validate extension is allowed for extra safety
    file_ext = Path(file_name).suffix.lower()
    if not file_ext:
        raise ValueError("File must have an extension")

    # Generate random filename, sanitizing the original stem
    random_name = uuid.uuid4().hex[:16]
    safe_stem = "".join(c for c in Path(file_name).stem if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_stem = safe_stem[:50] if safe_stem else "file"
    unique_name = f"{random_name}_{safe_stem}{file_ext}"
    file_path = UPLOADS_DIR / unique_name

    # Double-check: ensure file_path is within UPLOADS_DIR even after resolution
    if not _is_safe_path(UPLOADS_DIR, file_path):
        raise ValueError(f"File path would escape uploads directory: {unique_name}")

    # Write file atomically: first to temp, then rename
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    try:
        with open(temp_path, "wb") as f:
            f.write(file_data)
        # Atomic move
        temp_path.replace(file_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise

    return f"uploads/{unique_name}"


def delete_media_file(file_path: str) -> bool:
    """
    Delete media file from disk with symlink safety check.

    Args:
        file_path: Relative path to file.

    Returns:
        True if successful, False if file not found.
    """
    full_path = (Path(__file__).parent / file_path).resolve()

    # Check resolved path is within uploads dir (prevents symlink attacks)
    if not _is_safe_path(UPLOADS_DIR, full_path):
        logger.warning(f"Blocked path traversal/symlink attack: {file_path}")
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
    """Get full path to media file, restricted to uploads directory with symlink safety."""
    full_path = (Path(__file__).parent / file_path).resolve()

    # Verify the resolved path is actually within UPLOADS_DIR
    if not _is_safe_path(UPLOADS_DIR, full_path):
        raise ValueError(f"Invalid file path (outside uploads dir): {file_path}")

    return full_path

