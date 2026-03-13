import os
import uuid
import base64
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from gemini_webapi import GeminiClient

from config import GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS
from security import get_api_key
from utils import generate_creative_prompt

logger = logging.getLogger(__name__)
router = APIRouter(tags=["image-generation"])

# Initialize Gemini client
gemini_client = None

if GEMINI_COOKIE_1PSID:
    try:
        gemini_client = GeminiClient(GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS, proxy=None)
        logger.info("Gemini client created (will be initialized on first use)")
    except Exception as e:
        logger.warning(f"Failed to create Gemini client: {e}")


@router.post("/generate-image")
async def generate_image(
    word: str,
    language: str = "en",
    api_key: str = Depends(get_api_key)
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
        # Generate the creative prompt
        creative_prompt = generate_creative_prompt(word.strip(), language)
        
        # Initialize the client if not already done
        await gemini_client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
        
        # Generate content with Gemini (with image generation)
        response = await gemini_client.generate_content(creative_prompt)
        
        # Process the response
        images = []
        text_response = None
        
        # Extract text response
        if hasattr(response, 'text') and response.text:
            text_response = response.text
        
        # Extract images if available
        if hasattr(response, 'images') and response.images:
            for idx, image in enumerate(response.images):
                image_data = {
                    "id": idx,
                    "type": image.__class__.__name__
                }
                
                # Try to get image data
                try:
                    # Get image URL if available
                    if hasattr(image, 'url'):
                        image_data["url"] = image.url
                    
                    # Try to save and convert to base64
                    if hasattr(image, 'save'):
                        temp_filename = f"gemini_image_{uuid.uuid4()}.png"
                        await image.save(path="/tmp/", filename=temp_filename, verbose=False)
                        
                        full_path = f"/tmp/{temp_filename}"
                        with open(full_path, "rb") as img_file:
                            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                            image_data["base64"] = image_base64
                        
                        # Cleanup
                        os.remove(full_path)
                except Exception as e:
                    logger.error(f"Error processing image {idx}: {e}")
                    image_data["error"] = str(e)
                
                images.append(image_data)
        
        return JSONResponse(content={
            "word": word,
            "language": language,
            "prompt": creative_prompt,
            "images": images,
            "text_response": text_response,
            "success": len(images) > 0
        })
    
    except Exception as e:
        logger.error(f"Error during image generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image: {str(e)}"
        )
