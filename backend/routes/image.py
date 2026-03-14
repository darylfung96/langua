import asyncio
import os
import re
import uuid
import base64
import logging
import tempfile
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse

from config import TEMP_DIR, AI_REQUEST_TIMEOUT
from constants import LANGUAGE_NAMES, MAX_WORD_LENGTH, MAX_LANGUAGE_LENGTH, LANGUAGE_PATTERN
from database import User
from security import get_current_user
from gemini_client import get_gemini_client
from limiter import limiter
from slowapi.util import get_remote_address
from utils import generate_creative_prompt

logger = logging.getLogger(__name__)
router = APIRouter(tags=["image-generation"])

_language_re = re.compile(LANGUAGE_PATTERN)
_word_re = re.compile(r'^[^<>"\'&]+$')


@router.post("/generate-image")
@limiter.limit("10/minute", key_func=get_remote_address)
async def generate_image(
    request: Request,
    word: str = Query(..., min_length=1, max_length=MAX_WORD_LENGTH, description="Word to visualize"),
    language: str = Query("en", min_length=2, max_length=MAX_LANGUAGE_LENGTH, description="BCP 47 language code"),
    current_user: User = Depends(get_current_user)
):
    """Generate a memorable image for a word in a specific language."""
    word = word.strip()
    if not word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")
    if not _word_re.match(word):
        raise HTTPException(status_code=400, detail="Word contains invalid characters")
    if not _language_re.match(language):
        raise HTTPException(status_code=400, detail="Invalid language code format")

    try:
        creative_prompt = generate_creative_prompt(word, language)

        # Get or initialize the Gemini client (lazy initialization)
        client = await get_gemini_client()

        response = await asyncio.wait_for(
            client.generate_content(creative_prompt), timeout=AI_REQUEST_TIMEOUT
        )

        images = []
        text_response = None

        if hasattr(response, 'text') and response.text:
            text_response = response.text

        if hasattr(response, 'images') and response.images:
            # Use a temporary directory that auto-cleans for all image files
            with tempfile.TemporaryDirectory(dir=TEMP_DIR) as tmpdir:
                for idx, image in enumerate(response.images):
                    image_data = {
                        "id": idx,
                        "type": image.__class__.__name__
                    }

                    try:
                        if hasattr(image, 'url'):
                            image_data["url"] = image.url

                        if hasattr(image, 'save'):
                            temp_filename = f"gemini_image_{uuid.uuid4()}.png"
                            temp_path = os.path.join(tmpdir, temp_filename)
                            await image.save(path=tmpdir, filename=temp_filename, verbose=False)

                            with open(temp_path, "rb") as img_file:
                                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                                image_data["base64"] = image_base64
                    except Exception as e:
                        logger.error(f"Error processing image {idx}: {e}")
                        image_data["error"] = "Failed to process image"

                    images.append(image_data)

        return JSONResponse(content={
            "word": word,
            "language": language,
            "prompt": creative_prompt,
            "images": images,
            "text_response": text_response,
            "success": len(images) > 0
        })

    except asyncio.TimeoutError:
        logger.error("Gemini image generation timed out")
        raise HTTPException(status_code=504, detail="AI request timed out. Please try again.")
    except HTTPException:
        raise
    except RuntimeError as e:
        # Gemini client not configured
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error during image generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate image.")
