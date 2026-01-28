"""
Voice Handler
Handles audio file processing and transcription (MP3, WAV, OGG, M4A, WEBM)
with comprehensive logging
"""

import os
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# Whisper prompt for Malaysian multilingual context (Malay/Chinese/English)
# This helps Whisper correctly identify language and vocabulary for short voice clips
WHISPER_PROMPT = """Serenity Reflexology Example City customer conversation.
Malay: tak boleh, boleh, ok lah, nak book, ada slot tak, berapa harga, urut, terima kasih, baik, nanti, esok, hari ini, mahu, tidak, ya, saya, awak, bila, mana, kenapa, macam mana, boleh tak, tak nak, nak
Chinese: 预约, 按摩, 可以, 不可以, 好的, 多少钱, 谢谢, 几点, 今天, 明天, 要, 不要, 我要, 有没有, 位子, 脚底, 身体, 师傅
English: booking, massage, appointment, slot, therapist, body massage, foot massage, cancel, reschedule, tomorrow, today, how much, thank you, ok, yes, no"""


def validate_audio(file_path: str) -> bool:
    """
    Validate that the audio file exists and is accessible

    Args:
        file_path (str): Path to audio file

    Returns:
        bool: True if valid audio file

    Raises:
        Exception: If validation fails
    """
    logger.debug(f"Validating audio file: {file_path}")

    try:
        if not os.path.exists(file_path):
            raise Exception("Audio file not found")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise Exception("Audio file is empty")

        logger.debug(f"✓ Audio validation passed (size: {file_size} bytes)")
        return True

    except Exception as e:
        logger.error(f"❌ Audio validation failed: {file_path}")
        logger.error(f"Error: {str(e)}")
        raise Exception(f"Invalid audio file: {str(e)}")


def estimate_audio_duration(file_path: str, file_extension: str) -> float:
    """
    Estimate audio duration based on file size and format

    Args:
        file_path (str): Path to audio file
        file_extension (str): File extension (mp3, wav, ogg, m4a, webm)

    Returns:
        float: Estimated duration in minutes
    """
    logger.debug(f"Estimating audio duration: {file_path}")

    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        ext = file_extension.lower()

        logger.debug(f"File size: {size_mb:.2f} MB")
        logger.debug(f"Format: {ext}")

        # Rough estimates for common formats
        # Compressed formats (mp3, m4a, ogg, webm) ~1 MB per minute at 128kbps
        if ext in ['mp3', 'm4a', 'ogg', 'webm']:
            duration_min = size_mb * 1.0
        # Uncompressed WAV ~10 MB per minute
        elif ext == 'wav':
            duration_min = size_mb * 0.1
        else:
            # Conservative estimate for unknown formats
            duration_min = size_mb * 0.5

        duration_min = round(duration_min, 1)
        logger.debug(f"Estimated duration: {duration_min} minutes")

        return duration_min

    except Exception as e:
        logger.warning(f"Failed to estimate duration: {str(e)}")
        return 0.0


def estimate_processing_time(duration_minutes: float) -> str:
    """
    Estimate transcription processing time based on audio duration

    Args:
        duration_minutes (float): Audio duration in minutes

    Returns:
        str: Human-readable processing time estimate
    """
    # Whisper typically processes at 3-5x real-time speed
    # For conservative estimate, use 3x (e.g., 1 min audio = ~20 sec processing)
    processing_seconds = duration_minutes * 20

    if processing_seconds < 10:
        return "5-10 seconds"
    elif processing_seconds < 20:
        return "10-20 seconds"
    elif processing_seconds < 30:
        return "20-30 seconds"
    elif processing_seconds < 45:
        return "30-45 seconds"
    elif processing_seconds < 60:
        return "45-60 seconds"
    else:
        minutes = int(processing_seconds / 60)
        return f"{minutes}-{minutes + 1} minutes"


def get_audio_info(file_path: str, file_extension: str) -> Dict[str, Any]:
    """
    Get detailed information about the audio file

    Args:
        file_path (str): Path to audio file
        file_extension (str): File extension

    Returns:
        dict: Audio information (size_mb, format, estimated_duration)

    Raises:
        Exception: If getting info fails
    """
    logger.debug(f"Getting audio info: {file_path}")

    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        duration = estimate_audio_duration(file_path, file_extension)

        info = {
            'size_mb': round(size_mb, 2),
            'format': file_extension.upper(),
            'estimated_duration_min': duration,
            'processing_time_estimate': estimate_processing_time(duration)
        }

        logger.debug(f"Audio info: {info}")
        return info

    except Exception as e:
        logger.error(f"❌ Failed to get audio info: {file_path}")
        logger.error(f"Error: {str(e)}")
        raise Exception(f"Error getting audio info: {str(e)}")


def transcribe_audio(file_path: str, ai_engine, language: Optional[str] = None, prompt: Optional[str] = None) -> str:
    """
    Transcribe audio file using OpenAI Whisper API

    Args:
        file_path (str): Path to audio file
        ai_engine: AIEngine instance
        language (str, optional): Language code (e.g., 'en', 'ms', 'zh'). None for auto-detection.
        prompt (str, optional): Prompt to guide transcription with expected vocabulary/context.

    Returns:
        str: Transcribed text

    Raises:
        Exception: If transcription fails
    """
    logger.info(f"Transcribing audio: {file_path}")
    logger.debug(f"Language: {language or 'auto-detect'}")
    logger.debug(f"Using prompt: {'Yes' if prompt else 'No'}")

    try:
        result = ai_engine.transcribe_audio(file_path, language, prompt)

        if result['success']:
            logger.info(f"✓ Transcription successful")
            return result['transcription']
        else:
            raise Exception(result['error'])

    except Exception as e:
        logger.error(f"❌ Transcription failed: {file_path}")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        raise Exception(f"Error transcribing audio: {str(e)}")


def process_voice(file_path: str, file_extension: str, ai_engine) -> Dict[str, Any]:
    """
    Process voice file and return transcribed text with metadata

    Args:
        file_path (str): Path to audio file
        file_extension (str): File extension (mp3, wav, ogg, m4a, webm)
        ai_engine: AIEngine instance

    Returns:
        dict: {
            'transcription': str,
            'audio_info': dict,
            'success': bool
        }

    Raises:
        Exception: If processing fails
    """
    ext = file_extension.lower()

    logger.info("="*60)
    logger.info(f"PROCESSING VOICE: {ext.upper()}")
    logger.info("="*60)

    logger.debug(f"File: {file_path}")
    logger.debug(f"Extension: {ext}")

    # Validate file extension
    supported_formats = ['mp3', 'wav', 'ogg', 'm4a', 'webm']
    if ext not in supported_formats:
        logger.error(f"❌ Unsupported audio format: {ext}")
        raise Exception(f"Unsupported audio format: {ext}. Supported: {', '.join(supported_formats)}")

    # Validate audio file
    validate_audio(file_path)

    # Get audio information
    audio_info = get_audio_info(file_path, file_extension)
    logger.info(f"  Size: {audio_info['size_mb']} MB")
    logger.info(f"  Estimated duration: {audio_info['estimated_duration_min']} minutes")
    logger.info(f"  Est. processing time: {audio_info['processing_time_estimate']}")

    # Transcribe audio with multilingual Malaysian prompt
    transcription = transcribe_audio(file_path, ai_engine, prompt=WHISPER_PROMPT)

    logger.info(f"✓ Voice processing successful")
    logger.info(f"  Transcription length: {len(transcription)} characters")
    logger.debug(f"  Transcription preview: {transcription[:200]}...")

    return {
        'transcription': transcription,
        'audio_info': audio_info,
        'success': True
    }
