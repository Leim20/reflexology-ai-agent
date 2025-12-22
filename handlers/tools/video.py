"""
Video Handler
Handles video file processing with keyframe extraction and audio transcription
(MP4, MOV, AVI, MKV, WebM) with comprehensive logging
"""

import os
import cv2
import base64
import tempfile
from typing import Dict, Any, List, Optional
from moviepy import VideoFileClip
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_video(file_path: str) -> bool:
    """
    Validate that the video file exists and is a valid video file

    Args:
        file_path (str): Path to video file

    Returns:
        bool: True if valid video file

    Raises:
        Exception: If validation fails
    """
    logger.debug(f"Validating video file: {file_path}")

    try:
        if not os.path.exists(file_path):
            raise Exception("Video file not found")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise Exception("Video file is empty")

        # Try to open with OpenCV to verify it's a valid video
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise Exception("Could not open video file with OpenCV")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            raise Exception("Video file has no frames")

        cap.release()

        logger.debug(f"✓ Video validation passed (size: {file_size} bytes, frames: {frame_count})")
        return True

    except Exception as e:
        logger.error(f"❌ Video validation failed: {file_path}")
        logger.error(f"Error: {str(e)}")
        raise Exception(f"Invalid video file: {str(e)}")


def get_video_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about the video file

    Args:
        file_path (str): Path to video file

    Returns:
        dict: Video information (duration, fps, resolution, frame_count)

    Raises:
        Exception: If getting info fails
    """
    logger.debug(f"Getting video info: {file_path}")

    try:
        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            raise Exception("Could not open video file")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Calculate duration in seconds
        duration_sec = frame_count / fps if fps > 0 else 0
        duration_min = duration_sec / 60

        cap.release()

        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)

        info = {
            'size_mb': round(size_mb, 2),
            'duration_sec': round(duration_sec, 2),
            'duration_min': round(duration_min, 2),
            'fps': round(fps, 2),
            'resolution': f"{width}x{height}",
            'width': width,
            'height': height,
            'frame_count': frame_count
        }

        logger.debug(f"Video info: {info}")
        return info

    except Exception as e:
        logger.error(f"❌ Failed to get video info: {file_path}")
        logger.error(f"Error: {str(e)}")
        raise Exception(f"Error getting video info: {str(e)}")


def extract_keyframes(file_path: str, num_frames: int = 3, max_dimension: int = 1024) -> List[str]:
    """
    Extract keyframes from video and encode as base64

    Args:
        file_path (str): Path to video file
        num_frames (int): Number of keyframes to extract (default: 3)
        max_dimension (int): Maximum width/height for resized frames (default: 1024)

    Returns:
        list: List of base64 encoded keyframe images

    Raises:
        Exception: If extraction fails
    """
    logger.debug(f"Extracting {num_frames} keyframes from: {file_path}")

    try:
        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            raise Exception("Could not open video file")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if frame_count <= 0:
            raise Exception("Video has no frames")

        # Calculate frame indices to extract (evenly distributed)
        frame_indices = []
        if num_frames >= frame_count:
            frame_indices = list(range(frame_count))
        else:
            step = frame_count // (num_frames + 1)
            frame_indices = [step * (i + 1) for i in range(num_frames)]

        keyframes_base64 = []

        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret:
                logger.warning(f"Could not read frame {frame_idx}")
                continue

            # Resize frame if necessary
            height, width = frame.shape[:2]
            if width > max_dimension or height > max_dimension:
                scale = min(max_dimension / width, max_dimension / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))

            # Encode frame to base64
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                keyframes_base64.append(frame_base64)

        cap.release()

        logger.debug(f"✓ Extracted {len(keyframes_base64)} keyframes")
        return keyframes_base64

    except Exception as e:
        logger.error(f"❌ Failed to extract keyframes: {file_path}")
        logger.error(f"Error: {str(e)}")
        raise Exception(f"Error extracting keyframes: {str(e)}")


def extract_and_transcribe_audio(file_path: str, ai_engine) -> Optional[str]:
    """
    Extract audio from video and transcribe using AI engine

    Args:
        file_path (str): Path to video file
        ai_engine: AIEngine instance

    Returns:
        str: Transcribed text or None if no audio or transcription fails

    Raises:
        Exception: If extraction fails critically
    """
    logger.debug(f"Extracting audio from video: {file_path}")

    try:
        # Extract audio using moviepy
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_audio_path = os.path.join(temp_dir, "extracted_audio.wav")

            try:
                video_clip = VideoFileClip(file_path)
                audio_clip = video_clip.audio

                if audio_clip is None:
                    logger.warning("Video has no audio track")
                    video_clip.close()
                    return None

                audio_clip.write_audiofile(temp_audio_path, verbose=False, logger=None)
                audio_clip.close()
                video_clip.close()

            except Exception as e:
                logger.warning(f"Failed to extract audio with moviepy: {str(e)}")
                return None

            # Transcribe the extracted audio
            try:
                result = ai_engine.transcribe_audio(temp_audio_path, language=None)

                if result['success']:
                    logger.debug(f"✓ Audio transcription successful")
                    return result['transcription']
                else:
                    logger.warning(f"Audio transcription failed: {result.get('error', 'Unknown error')}")
                    return None

            except Exception as e:
                logger.warning(f"Transcription failed: {str(e)}")
                return None

    except Exception as e:
        logger.error(f"❌ Failed to extract audio from video: {file_path}")
        logger.error(f"Error: {str(e)}")
        return None


def get_mime_type(file_extension: str) -> str:
    """
    Get MIME type for video based on extension

    Args:
        file_extension (str): File extension (mp4, mov, avi, mkv, webm)

    Returns:
        str: MIME type
    """
    ext = file_extension.lower()
    mime_types = {
        'mp4': 'video/mp4',
        'mov': 'video/quicktime',
        'avi': 'video/x-msvideo',
        'mkv': 'video/x-matroska',
        'webm': 'video/webm'
    }

    mime_type = mime_types.get(ext, 'video/mp4')
    logger.debug(f"MIME type for {ext}: {mime_type}")
    return mime_type


def process_video(file_path: str, file_extension: str, ai_engine, num_keyframes: int = 3) -> Dict[str, Any]:
    """
    Process video file and extract keyframes, metadata, and transcribe audio

    Args:
        file_path (str): Path to video file
        file_extension (str): File extension (mp4, mov, avi, mkv, webm)
        ai_engine: AIEngine instance
        num_keyframes (int): Number of keyframes to extract (default: 3)

    Returns:
        dict: {
            'keyframes': list of base64 strings,
            'video_info': dict,
            'audio_transcription': str or None,
            'mime_type': str,
            'success': bool
        }

    Raises:
        Exception: If processing fails
    """
    ext = file_extension.lower()

    logger.info("="*60)
    logger.info(f"PROCESSING VIDEO: {ext.upper()}")
    logger.info("="*60)

    logger.debug(f"File: {file_path}")
    logger.debug(f"Extension: {ext}")

    # Validate file extension
    supported_formats = ['mp4', 'mov', 'avi', 'mkv', 'webm']
    if ext not in supported_formats:
        logger.error(f"❌ Unsupported video format: {ext}")
        raise Exception(f"Unsupported video format: {ext}. Supported: {', '.join(supported_formats)}")

    # Validate video file
    validate_video(file_path)

    # Get video information
    video_info = get_video_info(file_path)
    logger.info(f"  Size: {video_info['size_mb']} MB")
    logger.info(f"  Duration: {video_info['duration_min']} minutes")
    logger.info(f"  Resolution: {video_info['resolution']}")
    logger.info(f"  FPS: {video_info['fps']}")
    logger.info(f"  Total frames: {video_info['frame_count']}")

    # Extract keyframes
    logger.info(f"Extracting {num_keyframes} keyframes...")
    keyframes = extract_keyframes(file_path, num_frames=num_keyframes)
    logger.info(f"  ✓ Extracted {len(keyframes)} keyframes")

    # Extract and transcribe audio
    logger.info("Extracting and transcribing audio...")
    audio_transcription = extract_and_transcribe_audio(file_path, ai_engine)
    if audio_transcription:
        logger.info(f"  ✓ Audio transcription successful ({len(audio_transcription)} characters)")
    else:
        logger.info(f"  ℹ No audio or transcription unavailable")

    # Get MIME type
    mime_type = get_mime_type(file_extension)

    logger.info(f"✓ Video processing successful")
    logger.info(f"  MIME type: {mime_type}")

    return {
        'keyframes': keyframes,
        'video_info': video_info,
        'audio_transcription': audio_transcription,
        'mime_type': mime_type,
        'success': True
    }
