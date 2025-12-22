"""
File Processing Tools
Document, image, voice, video processing, and escalation handlers
"""

from .document import process_document, extract_from_pdf, extract_from_docx, extract_from_txt
from .image import process_image, encode_to_base64, validate_image, get_image_info, get_mime_type
from .voice import process_voice, transcribe_audio, get_audio_info
from .video import process_video, extract_keyframes, get_video_info, validate_video, extract_and_transcribe_audio
from .escalation import EscalationTool, create_escalation_tool, escalate

__all__ = [
    'process_document',
    'extract_from_pdf',
    'extract_from_docx',
    'extract_from_txt',
    'process_image',
    'encode_to_base64',
    'validate_image',
    'get_image_info',
    'get_mime_type',
    'process_voice',
    'transcribe_audio',
    'get_audio_info',
    'process_video',
    'extract_keyframes',
    'get_video_info',
    'validate_video',
    'extract_and_transcribe_audio',
    'EscalationTool',
    'create_escalation_tool',
    'escalate'
]
