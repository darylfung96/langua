"""
Gemini AI story and audio generation endpoints.
Handles story generation and TTS audio — keeps the API key server-side.
"""
import asyncio
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from config import AI_REQUEST_TIMEOUT
from security import get_current_user
from database import User
from gemini_client import get_gemini_client
from gemini_tts import generate_tts
from limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["story-generation"])

# Language code to display name mapping
LANGUAGE_NAMES = {
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'ru': 'Russian',
    'pt': 'Portuguese',
    'en': 'English',
    'ar': 'Arabic',
}


def _sanitize_json_text(text: str) -> str:
    """Strip markdown fences and fix invalid JSON escape sequences from AI responses."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    text = text.rstrip("`").strip()
    # Remove backslashes before characters that are not valid JSON escape characters.
    # Gemini sometimes emits Markdown-style escapes (e.g. \_ \' \< \> \!) inside JSON
    # string values. Removing them produces the intended characters.
    text = re.sub(r'\\(?!["\\/bfnrtu])', '', text)
    return text


# Language validation pattern (BCP 47 basic)
_language_regex = re.compile(r'^[a-zA-Z]{2,3}(?:-[a-zA-Z]{2})?$')


def _validate_language(v: str) -> str:
    """Validate language code format."""
    if not v:
        raise ValueError("Language is required")
    if not _language_regex.match(v):
        raise ValueError(f"Invalid language format: {v}. Use format like 'en', 'en-US', 'zh-CN'")
    return v


class StoryGenRequest(BaseModel):
    language: str = Field(min_length=1, max_length=100)
    words: str = Field(min_length=1, max_length=2_000)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("words")
    @classmethod
    def validate_words(cls, v: str) -> str:
        # Basic sanitization - prevent script injection in words list
        if re.search(r'[<>"\'&]', v):
            raise ValueError("Words contain invalid characters")
        return v


class AudioGenRequest(BaseModel):
    language: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    story: str = Field(min_length=1, max_length=50_000)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("story")
    @classmethod
    def sanitize_story(cls, v: str) -> str:
        """Sanitize HTML tags from story."""
        return re.sub(r'<[^>]+>', '', v)


class QuizGenRequest(BaseModel):
    language: str = Field(min_length=1, max_length=100)
    story: str = Field(min_length=1, max_length=50_000)
    vocabulary: list

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)


@router.post("/generate-quiz")
@limiter.limit("10/minute")
async def generate_quiz(
    request: Request,
    body: QuizGenRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a vocabulary quiz based on a story using Gemini AI."""
    try:
        client = await get_gemini_client()

        # Get display name for the language
        language_display = LANGUAGE_NAMES.get(body.language, body.language)

        clean_story = re.sub(r"<[^>]+>", "", body.story)
        vocab_list = ", ".join(
            f"{v.get('word', '')} = {v.get('equivalent_in_english', '')}"
            for v in body.vocabulary
        )

        prompt = (
            f"You are a fun and engaging language quiz creator. Based on this {language_display} "
            "vocabulary words, create an interactive quiz to help the learner remember the words.\n\n"
            f"Vocabulary words: {vocab_list}\n\n"
            "Create 3 questions per vocabulary word with VARIED types to keep it exciting:\n"
            '- "multiple_choice": 4 options, only one correct\n'
            '- "fill_blank": sentence with _____ where the answer goes\n'
            '- "true_false": options must be exactly ["True", "False"]\n\n'
            "Rules:\n"
            "- Make wrong options (distractors) plausible but clearly wrong\n"
            "- Explanations should be fun, memorable mnemonics or story references\n"
            "- Mix question types so it stays engaging\n"
            "- For fill_blank, the correct_answer is the exact word that fills the blank\n\n"
            "Return ONLY valid JSON with this exact structure (no markdown):\n"
            '{\n'
            '  "questions": [\n'
            '    {\n'
            '      "id": 1,\n'
            '      "type": "multiple_choice",\n'
            f'      "question": "The question in the {language_display} language",\n'
            '      "options": ["gato", "perro", "pájaro", "pez"],\n'
            '      "correct_answer": "gato",\n'
            '      "explanation": "Gato = cat! Think of a cat saying GA-TO when it meows.",\n'
            '      "word": "gato"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        response = await asyncio.wait_for(
            client.generate_content(prompt), timeout=AI_REQUEST_TIMEOUT
        )

        if not response.text:
            raise HTTPException(status_code=500, detail="No quiz generated.")

        quiz_data = json.loads(_sanitize_json_text(response.text))
        return JSONResponse(content=quiz_data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini quiz response as JSON: {e}")
        raise HTTPException(status_code=500, detail="AI returned an invalid response format.")
    except asyncio.TimeoutError:
        logger.error("Gemini quiz generation timed out")
        raise HTTPException(status_code=504, detail="AI request timed out. Please try again.")
    except HTTPException:
        raise
    except RuntimeError as e:
        # Gemini client not configured
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate quiz.")


@router.post("/generate-story")
@limiter.limit("10/minute")
async def generate_story(
    request: Request,
    body: StoryGenRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a vocabulary story using Gemini AI."""
    try:
        client = await get_gemini_client()

        # Get display name for the language
        language_display = LANGUAGE_NAMES.get(body.language, body.language)

        prompt = (
            f"Write an engaging story in {language_display} that incorporates the following "
            f"vocabulary words: {body.words}.\n where each targeted vocabulary word will "
            "be wrapped in <span class='highlight' title='English Translation'>word</span> \n"
            "Return the result as a raw JSON object with this exact structure:\n"
            "{\n"
            f'  "title": "Story Title in {language_display}",\n'
            f'  "story": "The story in {language_display}, with the requested vocabulary words",\n'
            '  "vocabulary": [\n'
            '    {\n'
            '      "word": "The original word submitted by the user",\n'
            f'      "meaning_in_target": "The meaning of the word in {body.language}",\n'
            '      "equivalent_in_english": "The equivalent word in English"\n'
            '    }\n'
            '  ]\n'
            "}\n\n"
            "Ensure your response is ONLY valid JSON, without any markdown formatting like ```json."
        )

        response = await asyncio.wait_for(
            client.generate_content(prompt), timeout=AI_REQUEST_TIMEOUT
        )

        if not response.text:
            raise HTTPException(status_code=500, detail="No response from AI.")

        story_data = json.loads(_sanitize_json_text(response.text))
        return JSONResponse(content=story_data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini story response as JSON: {e}")
        raise HTTPException(status_code=500, detail="AI returned an invalid response format.")
    except asyncio.TimeoutError:
        logger.error("Gemini story generation timed out")
        raise HTTPException(status_code=504, detail="AI request timed out. Please try again.")
    except HTTPException:
        raise
    except RuntimeError as e:
        # Gemini client not configured
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating story: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate story.")


@router.post("/generate-audio")
@limiter.limit("10/minute")
async def generate_audio(
    request: Request,
    body: AudioGenRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate TTS audio for a story using Gemini AI."""
    try:
        # Use the dedicated TTS function (requires GEMINI_API_KEY)
        audio_bytes, mime_type = await generate_tts(
            language=body.language,
            title=body.title,
            story=body.story  # already sanitized by validator
        )

        # Encode audio bytes to base64 for JSON transport
        import base64
        audio_data_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        return JSONResponse(content={
            "audio_data": audio_data_b64,
            "mime_type": mime_type,
        })

    except asyncio.TimeoutError:
        logger.error("Gemini audio generation timed out")
        raise HTTPException(status_code=504, detail="AI request timed out. Please try again.")
    except HTTPException:
        raise
    except RuntimeError as e:
        # Missing API key or configuration error
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate audio.")
