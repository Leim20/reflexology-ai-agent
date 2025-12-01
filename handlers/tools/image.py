"""
Image Handler
Handles image processing (JPG, PNG) with comprehensive logging
"""

import base64
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def encode_to_base64(file_path: str) -> str:
    """
    Encode image to base64 for OpenAI API

    Args:
        file_path (str): Path to image file

    Returns:
        str: Base64 encoded image

    Raises:
        Exception: If encoding fails
    """
    logger.debug(f"Encoding image to base64: {file_path}")

    try:
        with open(file_path, 'rb') as image_file:
            image_data = image_file.read()
            encoded = base64.b64encode(image_data).decode('utf-8')

        logger.debug(f"✓ Image encoded ({len(encoded)} chars)")
        return encoded

    except Exception as e:
        logger.error(f"❌ Failed to encode image: {file_path}")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        raise Exception(f"Error encoding image: {str(e)}")


def validate_image(file_path: str) -> bool:
    """
    Validate that the file is a proper image

    Args:
        file_path (str): Path to image file

    Returns:
        bool: True if valid image

    Raises:
        Exception: If validation fails
    """
    logger.debug(f"Validating image: {file_path}")

    try:
        with Image.open(file_path) as img:
            img.verify()

        logger.debug("✓ Image validation passed")
        return True

    except Exception as e:
        logger.error(f"❌ Image validation failed: {file_path}")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        raise Exception(f"Invalid image file: {str(e)}")


def get_image_info(file_path: str) -> dict:
    """
    Get detailed information about the image

    Args:
        file_path (str): Path to image file

    Returns:
        dict: Image information (format, size, mode, dimensions)

    Raises:
        Exception: If getting info fails
    """
    logger.debug(f"Getting image info: {file_path}")

    try:
        with Image.open(file_path) as img:
            info = {
                'format': img.format,
                'size': img.size,
                'mode': img.mode,
                'width': img.width,
                'height': img.height
            }

        logger.debug(f"Image info: {info['format']}, {info['width']}x{info['height']}, {info['mode']}")
        return info

    except Exception as e:
        logger.error(f"❌ Failed to get image info: {file_path}")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        raise Exception(f"Error getting image info: {str(e)}")


def get_mime_type(file_extension: str) -> str:
    """
    Get MIME type for image based on extension

    Args:
        file_extension (str): File extension (jpg, jpeg, png)

    Returns:
        str: MIME type
    """
    ext = file_extension.lower()
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png'
    }

    mime_type = mime_types.get(ext, 'image/jpeg')
    logger.debug(f"MIME type for {ext}: {mime_type}")
    return mime_type


def process_image(file_path: str, file_extension: str) -> tuple:
    """
    Process image file and return base64 encoded data with MIME type

    Args:
        file_path (str): Path to image file
        file_extension (str): File extension (jpg, jpeg, png)

    Returns:
        tuple: (base64_data: str, mime_type: str)

    Raises:
        Exception: If processing fails
    """
    logger.info("="*60)
    logger.info(f"PROCESSING IMAGE: {file_extension.upper()}")
    logger.info("="*60)

    logger.debug(f"File: {file_path}")
    logger.debug(f"Extension: {file_extension}")

    # Validate image first
    validate_image(file_path)

    # Get image info
    info = get_image_info(file_path)
    logger.info(f"  Format: {info['format']}")
    logger.info(f"  Dimensions: {info['width']}x{info['height']}")
    logger.info(f"  Mode: {info['mode']}")

    # Encode to base64
    base64_data = encode_to_base64(file_path)

    # Get MIME type
    mime_type = get_mime_type(file_extension)

    logger.info(f"✓ Image processing successful")
    logger.info(f"  MIME type: {mime_type}")
    logger.info(f"  Base64 size: {len(base64_data)} characters")

    return base64_data, mime_type
