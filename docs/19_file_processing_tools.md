# File Processing Tools

## Overview

The File Processing Tools are **backend utilities** that handle media files sent by customers via WhatsApp. They process voice messages, images, documents, and videos to extract content that the AI can understand.

**Location:** `handlers/tools/`
**Files:** `voice.py`, `image.py`, `document.py`, `video.py`
**Dependencies:** OpenAI Whisper, PIL, PyPDF2, python-docx, OpenCV, moviepy

---

## What is the Purpose?

The File Processing Tools exist to:

1. **Transcribe Voice Messages** — Convert audio to text using Whisper API.

2. **Process Images** — Encode images for GPT-4 Vision analysis.

3. **Extract Document Text** — Pull text from PDF, DOCX, TXT files.

4. **Handle Videos** — Extract keyframes and transcribe audio.

5. **Enable Multimedia Conversations** — Let customers communicate beyond text.

---

## The 4 Processing Tools

| Tool | File | Formats | Purpose |
|------|------|---------|---------|
| Voice Handler | `voice.py` | MP3, WAV, OGG, M4A, WEBM | Whisper transcription |
| Image Handler | `image.py` | JPG, PNG | Base64 encoding for Vision |
| Document Handler | `document.py` | PDF, DOCX, TXT | Text extraction |
| Video Handler | `video.py` | MP4, MOV, AVI, MKV, WEBM | Keyframes + audio |

---

## Tool 1: Voice Handler

### Purpose

Transcribe voice messages using **OpenAI Whisper API** with multilingual support for Malaysian context (Malay, Chinese, English).

### Location

`handlers/tools/voice.py` (~251 lines)

### Key Functions

```python
# Main processing function
def process_voice(file_path: str, file_extension: str, ai_engine) -> Dict:
    """
    Process voice file and return transcribed text

    Args:
        file_path: Path to audio file
        file_extension: mp3, wav, ogg, m4a, webm
        ai_engine: AIEngine instance

    Returns:
        {
            'transcription': str,
            'audio_info': dict,
            'success': bool
        }
    """

# Transcription function
def transcribe_audio(file_path: str, ai_engine, language=None, prompt=None) -> str:
    """Transcribe audio using Whisper API"""

# Validation
def validate_audio(file_path: str) -> bool:
    """Validate audio file exists and is not empty"""

# Info extraction
def get_audio_info(file_path: str, file_extension: str) -> dict:
    """Get file size, estimated duration, processing time"""
```

### Multilingual Whisper Prompt

```python
WHISPER_PROMPT = """Serenity Reflexology Example City customer conversation.
Malay: tak boleh, boleh, ok lah, nak book, ada slot tak, berapa harga, urut, terima kasih
Chinese: 预约, 按摩, 可以, 不可以, 好的, 多少钱, 谢谢, 几点, 今天, 明天
English: booking, massage, appointment, slot, therapist, body massage, foot massage"""
```

This prompt helps Whisper correctly identify:
- Malaysian slang and abbreviations
- Chinese service-related vocabulary
- Common booking phrases

### Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Customer sends voice message via WhatsApp                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  WHAPI webhook receives audio file URL                      │
│  Download audio to temp file                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  process_voice(file_path, extension, ai_engine)            │
│                                                              │
│  1. validate_audio() - Check file exists, not empty         │
│  2. get_audio_info() - Get duration estimate                │
│  3. transcribe_audio() - Call Whisper API                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Whisper API processes audio                                │
│  Returns: "我想预约明天下午三点的按摩"                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI processes transcription as normal text message          │
│  Responds appropriately to booking request                  │
└─────────────────────────────────────────────────────────────┘
```

### Duration Estimation

```python
def estimate_audio_duration(file_path: str, file_extension: str) -> float:
    """Estimate duration based on file size"""
    size_mb = os.path.getsize(file_path) / (1024 * 1024)

    # Compressed formats: ~1 MB per minute
    if ext in ['mp3', 'm4a', 'ogg', 'webm']:
        duration_min = size_mb * 1.0

    # Uncompressed WAV: ~10 MB per minute
    elif ext == 'wav':
        duration_min = size_mb * 0.1

    return duration_min
```

---

## Tool 2: Image Handler

### Purpose

Process images for **GPT-4 Vision** analysis by encoding to base64 and validating image integrity.

### Location

`handlers/tools/image.py` (~170 lines)

### Key Functions

```python
# Main processing function
def process_image(file_path: str, file_extension: str) -> tuple:
    """
    Process image and return base64 encoded data

    Args:
        file_path: Path to image file
        file_extension: jpg, jpeg, png

    Returns:
        (base64_data: str, mime_type: str)
    """

# Base64 encoding
def encode_to_base64(file_path: str) -> str:
    """Encode image file to base64 string"""

# Validation
def validate_image(file_path: str) -> bool:
    """Validate image using PIL"""

# Info extraction
def get_image_info(file_path: str) -> dict:
    """Get format, dimensions, mode"""

# MIME type
def get_mime_type(file_extension: str) -> str:
    """Get MIME type for image"""
```

### Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Customer sends image via WhatsApp                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  process_image(file_path, extension)                        │
│                                                              │
│  1. validate_image() - Check with PIL                       │
│  2. get_image_info() - Get dimensions                       │
│  3. encode_to_base64() - Convert for API                    │
│  4. get_mime_type() - Determine MIME type                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Returns: (base64_data, "image/jpeg")                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI Engine sends to GPT-4 Vision:                           │
│  {                                                          │
│    "type": "image_url",                                     │
│    "image_url": {                                           │
│      "url": "data:image/jpeg;base64,{base64_data}"         │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Image Validation

```python
def validate_image(file_path: str) -> bool:
    """Validate image using PIL's verify()"""
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verify image integrity
        return True
    except Exception as e:
        raise Exception(f"Invalid image file: {str(e)}")
```

---

## Tool 3: Document Handler

### Purpose

Extract text content from **PDF, DOCX, and TXT** files that customers send.

### Location

`handlers/tools/document.py` (~183 lines)

### Key Functions

```python
# Main processing function
def process_document(file_path: str, file_extension: str) -> str:
    """
    Process document and extract text

    Args:
        file_path: Path to document file
        file_extension: pdf, docx, txt

    Returns:
        Extracted text content
    """

# PDF extraction
def extract_from_pdf(file_path: str) -> str:
    """Extract text using PyPDF2"""

# DOCX extraction
def extract_from_docx(file_path: str) -> str:
    """Extract text using python-docx"""

# TXT extraction
def extract_from_txt(file_path: str) -> str:
    """Read text with encoding fallback"""
```

### PDF Extraction

```python
def extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        page_count = len(pdf_reader.pages)

        text = ""
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += page_text + "\n"

        return text.strip()
```

### DOCX Extraction

```python
def extract_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()
```

### TXT Extraction with Encoding Fallback

```python
def extract_from_txt(file_path: str) -> str:
    """Extract text with encoding fallback"""
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except UnicodeDecodeError:
        # Fallback to latin-1
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read().strip()
```

---

## Tool 4: Video Handler

### Purpose

Process videos by **extracting keyframes** for visual analysis and **transcribing audio** for content understanding.

### Location

`handlers/tools/video.py` (~344 lines)

### Key Functions

```python
# Main processing function
def process_video(file_path, file_extension, ai_engine, num_keyframes=3) -> Dict:
    """
    Process video file

    Args:
        file_path: Path to video file
        file_extension: mp4, mov, avi, mkv, webm
        ai_engine: AIEngine instance
        num_keyframes: Number of frames to extract

    Returns:
        {
            'keyframes': list of base64 strings,
            'video_info': dict,
            'audio_transcription': str or None,
            'mime_type': str,
            'success': bool
        }
    """

# Keyframe extraction
def extract_keyframes(file_path, num_frames=3, max_dimension=1024) -> List[str]:
    """Extract evenly-distributed frames using OpenCV"""

# Audio extraction and transcription
def extract_and_transcribe_audio(file_path, ai_engine) -> Optional[str]:
    """Extract audio with moviepy, transcribe with Whisper"""

# Validation
def validate_video(file_path: str) -> bool:
    """Validate video with OpenCV"""

# Info extraction
def get_video_info(file_path: str) -> dict:
    """Get duration, fps, resolution, frame count"""
```

### Keyframe Extraction

```python
def extract_keyframes(file_path: str, num_frames: int = 3) -> List[str]:
    """Extract evenly-distributed keyframes"""
    cap = cv2.VideoCapture(file_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate frame indices (evenly distributed)
    step = frame_count // (num_frames + 1)
    frame_indices = [step * (i + 1) for i in range(num_frames)]

    keyframes_base64 = []

    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()

        if ret:
            # Resize if needed
            if frame.shape[1] > 1024:
                scale = 1024 / frame.shape[1]
                frame = cv2.resize(frame, None, fx=scale, fy=scale)

            # Encode to base64
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            keyframes_base64.append(frame_base64)

    cap.release()
    return keyframes_base64
```

### Audio Extraction and Transcription

```python
def extract_and_transcribe_audio(file_path: str, ai_engine) -> Optional[str]:
    """Extract audio from video and transcribe"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_audio_path = os.path.join(temp_dir, "extracted_audio.wav")

        # Extract audio with moviepy
        video_clip = VideoFileClip(file_path)
        audio_clip = video_clip.audio

        if audio_clip is None:
            return None  # Video has no audio

        audio_clip.write_audiofile(temp_audio_path, verbose=False)
        audio_clip.close()
        video_clip.close()

        # Transcribe with Whisper
        result = ai_engine.transcribe_audio(temp_audio_path)

        if result['success']:
            return result['transcription']

        return None
```

---

## Integration in app.py

### Voice Message Handling

```python
from handlers.tools import process_voice

# In webhook handler
if message_type == 'voice' or message_type == 'audio':
    # Download audio file
    audio_path = download_media(media_url)

    # Process voice
    result = process_voice(audio_path, file_extension, ai_engine)

    if result['success']:
        # Use transcription as message
        message_text = result['transcription']

        # Continue processing as text
        response = generate_ai_response(message_text)
```

### Image Handling

```python
from handlers.tools import process_image

# In webhook handler
if message_type == 'image':
    # Download image
    image_path = download_media(media_url)

    # Process image
    base64_data, mime_type = process_image(image_path, file_extension)

    # Send to GPT-4 Vision
    response = ai_engine.generate_response_with_image(
        messages,
        base64_data,
        mime_type
    )
```

### Document Handling

```python
from handlers.tools import process_document

# In webhook handler
if message_type == 'document':
    # Download document
    doc_path = download_media(media_url)

    # Extract text
    doc_text = process_document(doc_path, file_extension)

    # Include in AI context
    message_with_doc = f"Customer sent document:\n{doc_text}\n\nRespond appropriately."
```

---

## Supported Formats

### Voice/Audio

| Format | Extension | Notes |
|--------|-----------|-------|
| MP3 | .mp3 | Most common |
| WAV | .wav | Uncompressed |
| OGG | .ogg | WhatsApp voice |
| M4A | .m4a | Apple format |
| WEBM | .webm | Web format |

### Images

| Format | Extension | Notes |
|--------|-----------|-------|
| JPEG | .jpg, .jpeg | Most common |
| PNG | .png | Lossless |

### Documents

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | .pdf | PyPDF2 |
| DOCX | .docx | python-docx |
| TXT | .txt | Plain text |

### Videos

| Format | Extension | Notes |
|--------|-----------|-------|
| MP4 | .mp4 | Most common |
| MOV | .mov | Apple format |
| AVI | .avi | Legacy |
| MKV | .mkv | Open format |
| WEBM | .webm | Web format |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Transcription fails | Whisper API error | Check API key |
| Image invalid | Corrupted file | Validate with PIL |
| PDF empty | Scanned PDF | OCR not supported |
| Video no audio | Silent video | Handle None return |

### Debug Logging

```
============================================================
PROCESSING VOICE: OGG
============================================================
File: /tmp/voice_123.ogg
Extension: ogg
  Size: 0.15 MB
  Estimated duration: 0.15 minutes
  Est. processing time: 5-10 seconds
Transcribing audio...
✓ Transcription successful
  Transcription length: 45 characters
============================================================
```

---

## Summary

The 4 File Processing Tools enable **multimedia conversations**:

- **Voice** — Whisper transcription with Malaysian context
- **Image** — Base64 encoding for GPT-4 Vision
- **Document** — PDF/DOCX/TXT text extraction
- **Video** — Keyframe extraction + audio transcription

This allows customers to send any media type and receive intelligent AI responses.
