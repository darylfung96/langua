"""Google Cloud Text-to-Speech client.

Provides a single async function ``generate_tts_audio`` that returns
base64-encoded MP3 audio for a given text and BCP-47 language code.

Features:
- WaveNet voice selection per language
- LRU + TTL in-memory cache (asyncio-safe)
- Circuit breaker on quota/auth failures
- Automatic retry with exponential backoff for transient errors
- API key sent via header, never in URL
"""
import asyncio
import logging
import random
import time
from collections import OrderedDict
from dataclasses import dataclass

import httpx
from fastapi import HTTPException

from config import GOOGLE_CLOUD_TTS_API_KEY, TTS_REQUEST_TIMEOUT, TTS_SPEAKING_RATE

logger = logging.getLogger(__name__)

# ── Voice mapping ────────────────────────────────────────────────────────────
# Maps the app's BCP-47 language codes to (Google languageCode, WaveNet voice name).
TTS_VOICE_MAP: dict[str, tuple[str, str]] = {
    "en":    ("en-US", "en-US-Wavenet-D"),
    "en-US": ("en-US", "en-US-Wavenet-D"),
    "es":    ("es-ES", "es-ES-Wavenet-B"),
    "fr":    ("fr-FR", "fr-FR-Wavenet-B"),
    "de":    ("de-DE", "de-DE-Wavenet-B"),
    "it":    ("it-IT", "it-IT-Wavenet-C"),
    "ja":    ("ja-JP", "ja-JP-Wavenet-B"),
    "ko":    ("ko-KR", "ko-KR-Wavenet-B"),
    "zh-CN": ("cmn-CN", "cmn-CN-Wavenet-B"),
    "zh-TW": ("cmn-TW", "cmn-TW-Wavenet-B"),
    "ru":    ("ru-RU", "ru-RU-Wavenet-B"),
    "pt":    ("pt-BR", "pt-BR-Wavenet-B"),
    "pt-BR": ("pt-BR", "pt-BR-Wavenet-B"),
    "ar":    ("ar-XA", "ar-XA-Wavenet-B"),
}

SUPPORTED_TTS_LANGUAGES: frozenset[str] = frozenset(TTS_VOICE_MAP)

# ── Cache ────────────────────────────────────────────────────────────────────
_CACHE_MAX = 200
_CACHE_TTL = 86_400  # 24 hours — TTS audio for static phrases is stable


@dataclass(slots=True)
class _CacheEntry:
    audio: str
    expires_at: float  # monotonic timestamp


_cache: OrderedDict[str, _CacheEntry] = OrderedDict()
_cache_lock = asyncio.Lock()

# ── Circuit breaker ──────────────────────────────────────────────────────────
_QUOTA_COOLDOWN = 300  # seconds before retrying after a 403
_quota_exceeded_until: float = 0.0  # monotonic timestamp

# ── Retry ────────────────────────────────────────────────────────────────────
_MAX_RETRIES = 2
_RETRYABLE_STATUS: frozenset[int] = frozenset({429, 500, 502, 503, 504})
_TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


# ── Public API ───────────────────────────────────────────────────────────────

async def generate_tts_audio(text: str, language: str) -> str:
    """Return base64-encoded MP3 audio for *text* spoken in *language*.

    Raises ``HTTPException`` on all failure modes so callers can propagate
    directly to the client without additional error handling.
    """
    if not GOOGLE_CLOUD_TTS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech is not configured. Set GOOGLE_CLOUD_TTS_API_KEY.",
        )

    if time.monotonic() < _quota_exceeded_until:
        raise HTTPException(
            status_code=503,
            detail="TTS quota exceeded. Service temporarily unavailable.",
        )

    voice_info = TTS_VOICE_MAP.get(language)
    if not voice_info:
        # Allow prefix match so e.g. "pt-PT" falls back to "pt"
        voice_info = TTS_VOICE_MAP.get(language.split("-")[0])
    if not voice_info:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language for TTS: {language}",
        )

    language_code, voice_name = voice_info
    cache_key = f"{language_code}:{text.strip().lower()}"

    # Cache read
    async with _cache_lock:
        entry = _cache.get(cache_key)
        if entry is not None:
            if time.monotonic() < entry.expires_at:
                _cache.move_to_end(cache_key)
                return entry.audio
            del _cache[cache_key]  # expired

    audio_content = await _call_api(text, language_code, voice_name)

    # Cache write
    async with _cache_lock:
        if len(_cache) >= _CACHE_MAX:
            _cache.popitem(last=False)  # evict LRU
        _cache[cache_key] = _CacheEntry(
            audio=audio_content,
            expires_at=time.monotonic() + _CACHE_TTL,
        )

    return audio_content


# ── Internal helpers ─────────────────────────────────────────────────────────

async def _call_api(text: str, language_code: str, voice_name: str) -> str:
    """Call the Google Cloud TTS REST API with retries and exponential backoff."""
    global _quota_exceeded_until

    payload = {
        "input": {"text": text},
        "voice": {"languageCode": language_code, "name": voice_name},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": TTS_SPEAKING_RATE},
    }
    headers = {
        "X-Goog-Api-Key": GOOGLE_CLOUD_TTS_API_KEY,
        "Content-Type": "application/json",
    }

    last_exc: Exception | None = None

    async with httpx.AsyncClient(timeout=TTS_REQUEST_TIMEOUT) as client:
        for attempt in range(_MAX_RETRIES + 1):
            if attempt:
                await asyncio.sleep(2 ** (attempt - 1) + random.uniform(0, 1))

            try:
                response = await client.post(_TTS_API_URL, json=payload, headers=headers)
            except httpx.TimeoutException as exc:
                logger.warning(
                    "Google TTS timeout (attempt %d/%d, language=%s)",
                    attempt + 1, _MAX_RETRIES + 1, language_code,
                )
                last_exc = exc
                continue
            except httpx.RequestError as exc:
                logger.warning(
                    "Google TTS request error (attempt %d/%d, language=%s): %s",
                    attempt + 1, _MAX_RETRIES + 1, language_code, type(exc).__name__,
                )
                last_exc = exc
                continue

            if response.status_code == 403:
                _quota_exceeded_until = time.monotonic() + _QUOTA_COOLDOWN
                logger.error(
                    "Google TTS quota/auth error (status=403) – circuit breaker "
                    "active for %ds", _QUOTA_COOLDOWN,
                )
                raise HTTPException(
                    status_code=503,
                    detail="TTS quota exceeded or invalid API key.",
                )

            if response.status_code == 400:
                logger.warning(
                    "Google TTS bad request: status=400, language=%s", language_code,
                )
                raise HTTPException(status_code=400, detail="Invalid TTS request.")

            if response.status_code in _RETRYABLE_STATUS:
                logger.warning(
                    "Google TTS retryable error: status=%d (attempt %d/%d, language=%s)",
                    response.status_code, attempt + 1, _MAX_RETRIES + 1, language_code,
                )
                last_exc = httpx.HTTPStatusError(
                    message=str(response.status_code),
                    request=response.request,
                    response=response,
                )
                continue

            if not response.is_success:
                logger.error(
                    "Google TTS non-retryable error: status=%d, language=%s",
                    response.status_code, language_code,
                )
                raise HTTPException(status_code=502, detail="TTS service error.")

            try:
                data = response.json()
            except Exception:
                logger.error(
                    "Google TTS returned non-JSON response: status=%d", response.status_code,
                )
                raise HTTPException(
                    status_code=502, detail="TTS service returned invalid response.",
                )

            audio_content = data.get("audioContent")
            if not isinstance(audio_content, str) or not audio_content.strip():
                logger.error("Google TTS returned empty or invalid audioContent")
                raise HTTPException(status_code=502, detail="TTS service returned empty audio.")

            return audio_content

    # All retries exhausted
    if isinstance(last_exc, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail="TTS request timed out.")
    raise HTTPException(status_code=502, detail="TTS service unavailable after retries.")
