"""
File Processing Tools
Document, image, voice processing, and escalation handlers
"""

from .document import process_document, extract_from_pdf, extract_from_docx, extract_from_txt
from .image import process_image, encode_to_base64, validate_image, get_image_info, get_mime_type
from .voice import process_voice, transcribe_audio, get_audio_info
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
    'EscalationTool',
    'create_escalation_tool',
    'escalate'
]
