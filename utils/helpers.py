"""
Helper Utilities
Common utility functions used across the application
"""

import os
from typing import Dict, Set, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


# File extension sets
IMAGE_EXTENSIONS: Set[str] = {'jpg', 'jpeg', 'png'}
DOCUMENT_EXTENSIONS: Set[str] = {'txt', 'pdf', 'docx'}
VOICE_EXTENSIONS: Set[str] = {'mp3', 'wav', 'ogg', 'm4a', 'webm'}
ALL_ALLOWED_EXTENSIONS: Set[str] = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS | VOICE_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename

    Args:
        filename (str): Name of the file

    Returns:
        str: File extension in lowercase (without dot)
    """
    logger.debug(f"Getting file extension for: {filename}")

    if '.' not in filename:
        logger.warning(f"No extension found in filename: {filename}")
        return ''

    ext = filename.rsplit('.', 1)[1].lower()
    logger.debug(f"Extracted extension: {ext}")
    return ext


def allowed_file(filename: str, allowed_extensions: Optional[Set[str]] = None) -> bool:
    """
    Check if file extension is allowed

    Args:
        filename (str): Name of the file
        allowed_extensions (Set[str], optional): Set of allowed extensions

    Returns:
        bool: True if file extension is allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ALL_ALLOWED_EXTENSIONS

    logger.debug(f"Checking if file is allowed: {filename}")

    ext = get_file_extension(filename)

    if not ext:
        logger.warning(f"File has no extension: {filename}")
        return False

    is_allowed = ext in allowed_extensions
    logger.debug(f"File '{filename}' allowed: {is_allowed}")
    return is_allowed


def is_image_file(filename: str) -> bool:
    """Check if file is an image"""
    ext = get_file_extension(filename)
    result = ext in IMAGE_EXTENSIONS
    logger.debug(f"Is '{filename}' an image? {result}")
    return result


def is_document_file(filename: str) -> bool:
    """Check if file is a document"""
    ext = get_file_extension(filename)
    result = ext in DOCUMENT_EXTENSIONS
    logger.debug(f"Is '{filename}' a document? {result}")
    return result


def is_voice_file(filename: str) -> bool:
    """Check if file is a voice/audio file"""
    ext = get_file_extension(filename)
    result = ext in VOICE_EXTENSIONS
    logger.debug(f"Is '{filename}' a voice file? {result}")
    return result


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        kb = size_bytes / 1024
        return f"{kb:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        mb = size_bytes / (1024 * 1024)
        return f"{mb:.1f} MB"
    else:
        gb = size_bytes / (1024 * 1024 * 1024)
        return f"{gb:.1f} GB"


def check_file_size(file_path: str, filename: str, max_sizes: Optional[Dict[str, int]] = None) -> Dict:
    """
    Check if file size is within limits for its type

    Args:
        file_path (str): Path to file
        filename (str): Original filename
        max_sizes (Dict[str, int], optional): Dictionary of max sizes by file type

    Returns:
        dict: {'valid': bool, 'error': str or None, 'size_bytes': int,
               'size_formatted': str, 'file_type': str}
    """
    logger.debug(f"Checking file size for: {file_path}")

    # Default max sizes
    if max_sizes is None:
        max_sizes = {
            'image': 10 * 1024 * 1024,
            'document': 10 * 1024 * 1024,
            'voice': 15 * 1024 * 1024
        }

    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {'valid': False, 'error': 'File not found', 'size_bytes': 0,
                    'size_formatted': '0 B', 'file_type': 'unknown'}

        size_bytes = os.path.getsize(file_path)
        size_formatted = format_file_size(size_bytes)
        logger.debug(f"File size: {size_bytes} bytes ({size_formatted})")

        # Determine file type
        if is_image_file(filename):
            file_type = 'image'
            max_size = max_sizes.get('image', 10 * 1024 * 1024)
        elif is_document_file(filename):
            file_type = 'document'
            max_size = max_sizes.get('document', 10 * 1024 * 1024)
        elif is_voice_file(filename):
            file_type = 'voice'
            max_size = max_sizes.get('voice', 15 * 1024 * 1024)
        else:
            logger.error(f"Unsupported file type: {filename}")
            return {'valid': False, 'error': 'Unsupported file type', 'size_bytes': size_bytes,
                    'size_formatted': size_formatted, 'file_type': 'unknown'}

        logger.debug(f"File type: {file_type}, Max allowed: {format_file_size(max_size)}")

        if size_bytes > max_size:
            error_msg = f"{file_type.capitalize()} file too large ({size_formatted}). Max: {format_file_size(max_size)}"
            logger.warning(error_msg)
            return {'valid': False, 'error': error_msg, 'size_bytes': size_bytes,
                    'size_formatted': size_formatted, 'file_type': file_type}

        logger.debug(f"File size check passed for {file_type}")
        return {'valid': True, 'error': None, 'size_bytes': size_bytes,
                'size_formatted': size_formatted, 'file_type': file_type}

    except Exception as e:
        logger.exception(f"Error checking file size: {str(e)}")
        return {'valid': False, 'error': f"Error: {str(e)}", 'size_bytes': 0,
                'size_formatted': '0 B', 'file_type': 'unknown'}
