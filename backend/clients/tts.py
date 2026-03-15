"""
clients/tts — Text-to-speech implementations.

Two implementations are available:
  1. generate_tts()        — Gemini GenAI TTS (gemini-2.5-flash-preview-tts)
                             Returns raw audio bytes + MIME type.
                             Requires GEMINI_API_KEY.
  2. generate_tts_audio()  — Google Cloud TTS REST API (WaveNet voices)
                             Returns base64-encoded MP3 string.
                             Requires GOOGLE_CLOUD_TTS_API_KEY.

Both are exported from this module.  The original gemini_tts.py and
tts_client.py modules still exist as shims that re-export from here.
"""

# ─── Standard library ───────────────────────────────────────────────────────
import asyncio
import logging
import random
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Tuple

# ─── Third-party ─────────────────────────────────────────────────────────────
import httpx
from fastapi import HTTPException

# ─── Internal ────────────────────────────────────────────────────────────────
from config import (
    GEMINI_API_KEY,
    GOOGLE_CLOUD_TTS_API_KEY,
    AI_REQUEST_TIMEOUT,
    TTS_REQUEST_TIMEOUT,
    TTS_SPEAKING_RATE,
)
from constants import LANGUAGE_NAMES

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# Implementation 1 — Gemini GenAI TTS
# ════════════════════════════════════════════════════════════════════════════

def _get_language_name(language_code: str) -> str:
    """Return human-readable display name for a BCP-47 language code."""
    return LANGUAGE_NAMES.get(language_code, language_code)


async def generate_tts(language: str, title: str, story: str) -> Tuple[bytes, str]:
    """Generate TTS audio using the Gemini GenAI TTS model.

    Args:
        language: BCP-47 language code (e.g. 'en', 'fr', 'es')
        title:    Story title (plain text)
        story:    Story content (plain text, without HTML)

    Returns:
        Tuple of (audio_bytes, mime_type)

    Raises:
        RuntimeError: GEMINI_API_KEY not configured or SDK not installed
        ValueError:   No audio returned by the API
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Gemini API key is required for audio generation. "
            "Set GEMINI_API_KEY environment variable with a key from "
            "https://aistudio.google.com/app/apikey"
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        logger.error("Failed to import google-genai. Run: pip install google-genai")
        raise RuntimeError("Google GenAI SDK is not installed.") from exc

    client = genai.Client(api_key=GEMINI_API_KEY)
    language_name = _get_language_name(language)
    prompt = (
        f"Please read the following story aloud in {language_name}:\n\n"
        f"{title}\n\n{story}"
    )

    generate_content_config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
            )
        ),
    )

    try:
        loop = asyncio.get_running_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.5-flash-preview-tts",
                    contents=prompt,
                    config=generate_content_config,
                ),
            ),
            timeout=AI_REQUEST_TIMEOUT,
        )

        if not response.candidates:
            raise ValueError("No candidates in Gemini TTS response")
        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            raise ValueError("No content parts in Gemini TTS response")

        for part in candidate.content.parts:
            if (
                part.inline_data
                and part.inline_data.mime_type
                and part.inline_data.mime_type.startswith("audio/")
            ):
                audio_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type
                logger.info(
                    "Gemini TTS generated audio: mime_type=%s, size=%d bytes",
                    mime_type,
                    len(audio_bytes),
                )
                return audio_bytes, mime_type

        raise ValueError("No audio data found in Gemini TTS response")

    except asyncio.TimeoutError:
        logger.error("Gemini TTS request timed out after %ds", AI_REQUEST_TIMEOUT)
        raise
    except Exception:
        logger.error("Error generating TTS with Gemini", exc_info=True)
        raise


# ════════════════════════════════════════════════════════════════════════════
# Implementation 2 — Google Cloud TTS REST API
# ════════════════════════════════════════════════════════════════════════════

# Voice map: app BCP-47 code → (Google languageCode, WaveNet voice name)
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

_CACHE_MAX = 200
_CACHE_TTL = 86_400  # 24 h – TTS for static phrases is stable
_QUOTA_COOLDOWN = 300  # s before retrying after a 403
_MAX_RETRIES = 2
_RETRYABLE_STATUS: frozenset[int] = frozenset({429, 500, 502, 503, 504})
_TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


@dataclass(slots=True)
class _CacheEntry:
    audio: str
    expires_at: float  # monotonic timestamp


_cache: OrderedDict[str, _CacheEntry] = OrderedDict()
_cache_lock = asyncio.Lock()
_quota_exceeded_until: float = 0.0


async def generate_tts_audio(text: str, language: str) -> str:
    """Return base64-encoded MP3 audio for *text* spoken in *language*.

    Uses Google Cloud TTS REST API with WaveNet voices, an in-process LRU/TTL
    cache, circuit breaker on quota exhaustion, and exponential-backoff retries.

    Raises:
        HTTPException: on all failure modes (propagated to FastAPI responses).
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

    voice_info = TTS_VOICE_MAP.get(language) or TTS_VOICE_MAP.get(language.split("-")[0])
    if not voice_info:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language for TTS: {language}",
        )

    language_code, voice_name = voice_info
    cache_key = f"{language_code}:{text.strip().lower()}"

    async with _cache_lock:
        entry = _cache.get(cache_key)
        if entry is not None:
            if time.monotonic() < entry.expires_at:
                _cache.move_to_end(cache_key)
                return entry.audio
            del _cache[cache_key]

    audio_content = await _call_cloud_tts(text, language_code, voice_name)

    async with _cache_lock:
        if len(_cache) >= _CACHE_MAX:
            _cache.popitem(last=False)
        _cache[cache_key] = _CacheEntry(
            audio=audio_content,
            expires_at=time.monotonic() + _CACHE_TTL,
        )

    return audio_content


async def _call_cloud_tts(text: str, language_code: str, voice_name: str) -> str:
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

    async with httpx.AsyncClient(timeout=TTS_REQUEST_TIMEOUT) as http:
        for attempt in range(_MAX_RETRIES + 1):
            if attempt:
                await asyncio.sleep(2 ** (attempt - 1) + random.uniform(0, 1))

            try:
                response = await http.post(_TTS_API_URL, json=payload, headers=headers)
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
                raise HTTPException(status_code=503, detail="TTS quota exceeded or invalid API key.")

            if response.status_code == 400:
                logger.warning("Google TTS bad request: status=400, language=%s", language_code)
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
                logger.error("Google TTS error: status=%d, language=%s", response.status_code, language_code)
                raise HTTPException(status_code=502, detail="TTS service error.")

            try:
                data = response.json()
            except Exception:
                logger.error("Google TTS returned non-JSON: status=%d", response.status_code)
                raise HTTPException(status_code=502, detail="TTS service returned invalid response.")

            audio_content = data.get("audioContent")
            if not isinstance(audio_content, str) or not audio_content.strip():
                logger.error("Google TTS returned empty audioContent")
                raise HTTPException(status_code=502, detail="TTS service returned empty audio.")

            return audio_content

    if isinstance(last_exc, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail="TTS request timed out.")
    raise HTTPException(status_code=502, detail="TTS service unavailable after retries.")
