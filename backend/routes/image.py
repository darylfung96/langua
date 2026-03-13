import asyncio
import os
import uuid
import base64
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from config import TEMP_DIR
from security import get_current_user
from gemini_client import gemini_client
from limiter import limiter
from utils import generate_creative_prompt

logger = logging.getLogger(__name__)
router = APIRouter(tags=["image-generation"])

_AI_TIMEOUT = 60.0  # seconds


@router.post("/generate-image")
@limiter.limit("10/minute")
async def generate_image(
    request: Request,
    word: str,
    language: str = "en",
    api_key: str = Depends(get_current_user)
):
    """Generate a memorable image for a word in a specific language."""
    if not gemini_client:
        raise HTTPException(
            status_code=503,
            detail="Gemini service is not available. Please configure GEMINI_COOKIE_1PSID and optionally GEMINI_COOKIE_1PSIDTS environment variables."
        )

    if not word or not word.strip():
        raise HTTPException(status_code=400, detail="Word cannot be empty")

    try:
        creative_prompt = generate_creative_prompt(word.strip(), language)

        await gemini_client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
        response = await asyncio.wait_for(
            gemini_client.generate_content(creative_prompt), timeout=_AI_TIMEOUT
        )

        images = []
        text_response = None

        if hasattr(response, 'text') and response.text:
            text_response = response.text

        if hasattr(response, 'images') and response.images:
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
                        await image.save(path=TEMP_DIR, filename=temp_filename, verbose=False)

                        full_path = os.path.join(TEMP_DIR, temp_filename)
                        with open(full_path, "rb") as img_file:
                            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                            image_data["base64"] = image_base64

                        os.remove(full_path)
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
    except Exception as e:
        logger.error(f"Error during image generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate image.")
