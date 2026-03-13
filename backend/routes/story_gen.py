"""
Gemini AI story and audio generation endpoints.
Handles story generation and TTS audio — keeps the API key server-side.
"""
import json
import logging
import re

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from gemini_webapi import GeminiClient

from security import get_api_key
from config import GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["story-generation"])

# Initialize Gemini client
gemini_client = None

if GEMINI_COOKIE_1PSID:
    try:
        gemini_client = GeminiClient(GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS, proxy=None)
        logger.info("Gemini client created for story generation (will be initialized on first use)")
    except Exception as e:
        logger.warning(f"Failed to create Gemini client: {e}")


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


def _get_gemini_client():
    if not gemini_client:
        raise HTTPException(
            status_code=503,
            detail="Gemini service is not available. Please configure GEMINI_COOKIE_1PSID and optionally GEMINI_COOKIE_1PSIDTS environment variables."
        )
    return gemini_client


class StoryGenRequest(BaseModel):
    language: str
    words: str


class AudioGenRequest(BaseModel):
    language: str
    title: str
    story: str


class QuizGenRequest(BaseModel):
    language: str
    story: str
    vocabulary: list


@router.post("/generate-quiz")
async def generate_quiz(
    request: QuizGenRequest,
    api_key: str = Depends(get_api_key)
):
    """Generate a vocabulary quiz based on a story using Gemini AI."""
    client = _get_gemini_client()

    clean_story = re.sub(r"<[^>]+>", "", request.story)
    vocab_list = ", ".join(
        f"{v.get('word', '')} = {v.get('equivalent_in_english', '')}"
        for v in request.vocabulary
    )

    prompt = (
        f"You are a fun and engaging language quiz creator. Based on this {request.language} "
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
        f'      "question": "The question in the {request.language} language",\n'
        '      "options": ["gato", "perro", "pájaro", "pez"],\n'
        '      "correct_answer": "gato",\n'
        '      "explanation": "Gato = cat! Think of a cat saying GA-TO when it meows.",\n'
        '      "word": "gato"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    try:
        await client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
        response = await client.generate_content(prompt)

        if not response.text:
            raise HTTPException(status_code=500, detail="No quiz generated.")

        quiz_data = json.loads(_sanitize_json_text(response.text))
        return JSONResponse(content=quiz_data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini quiz response as JSON: {e}")
        raise HTTPException(status_code=500, detail="AI returned an invalid response format.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.post("/generate-story")
async def generate_story(
    request: StoryGenRequest,
    api_key: str = Depends(get_api_key)
):
    """Generate a vocabulary story using Gemini AI."""
    client = _get_gemini_client()

    prompt = (
        f"Write an engaging story in {request.language} that incorporates the following "
        f"vocabulary words: {request.words}.\n where each targeted vocabulary word will "
        "be wrapped in <span class='highlight' title='English Translation'>word</span> \n"
        "Return the result as a raw JSON object with this exact structure:\n"
        "{\n"
        f'  "title": "Story Title in {request.language}",\n'
        f'  "story": "The story in {request.language}, with the requested vocabulary words",\n'
        '  "vocabulary": [\n'
        '    {\n'
        '      "word": "The original word submitted by the user",\n'
        f'      "meaning_in_target": "The meaning of the word in {request.language}",\n'
        '      "equivalent_in_english": "The equivalent word in English"\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "Ensure your response is ONLY valid JSON, without any markdown formatting like ```json."
    )

    try:
        await client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
        response = await client.generate_content(prompt)

        if not response.text:
            raise HTTPException(status_code=500, detail="No response from AI.")

        story_data = json.loads(_sanitize_json_text(response.text))
        return JSONResponse(content=story_data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini story response as JSON: {e}")
        raise HTTPException(status_code=500, detail="AI returned an invalid response format.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating story: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate story: {str(e)}")


@router.post("/generate-audio")
async def generate_audio(
    request: AudioGenRequest,
    api_key: str = Depends(get_api_key)
):
    """Generate TTS audio for a story using Gemini AI."""
    client = _get_gemini_client()

    clean_story = re.sub(r"<[^>]+>", "", request.story)
    prompt = (
        f"Please read the following story aloud in {request.language}:\n\n"
        f"{request.title}\n\n{clean_story}"
    )

    try:
        await client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
        response = await client.generate_content(prompt)

        audio_part = None
        candidates = response.candidates or []
        for candidate in candidates:
            # gemini_webapi Candidate may expose parts directly or via .content
            parts = (
                getattr(candidate, "parts", None)
                or getattr(getattr(candidate, "content", None), "parts", None)
                or []
            )
            for part in parts:
                if (
                    part.inline_data
                    and part.inline_data.mime_type
                    and part.inline_data.mime_type.startswith("audio/")
                ):
                    audio_part = part
                    break
            if audio_part:
                break

        if not audio_part or not audio_part.inline_data:
            raise HTTPException(status_code=500, detail="No audio returned from AI.")

        return JSONResponse(content={
            "audio_data": audio_part.inline_data.data,
            "mime_type": audio_part.inline_data.mime_type,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")
