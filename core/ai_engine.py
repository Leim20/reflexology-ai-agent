"""
AI Engine
Unified interface for OpenAI API calls with comprehensive logging
"""

from typing import List, Dict, Any, Optional
import time
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)


class AIEngine:
    """
    AI Engine for chat completions and voice transcription

    Handles:
    - Chat completions (text and multimodal)
    - Voice transcription (Whisper)
    - Error handling and retries
    - Comprehensive debug logging
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.7,
                 max_tokens: int = 1500):
        """
        Initialize AI Engine

        Args:
            api_key (str): OpenAI API key
            model (str): Model name (default: gpt-4o-mini)
            temperature (float): Temperature for generation (default: 0.7)
            max_tokens (int): Maximum tokens in response (default: 1500)
        """
        logger.info("="*80)
        logger.info("INITIALIZING AI ENGINE")
        logger.info("="*80)

        logger.debug(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
        logger.debug(f"Model: {model}")
        logger.debug(f"Temperature: {temperature}")
        logger.debug(f"Max Tokens: {max_tokens}")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info("✓ AI Engine initialized successfully")
        logger.info("="*80)

    def generate_response(self, messages: List[Dict[str, Any]],
                         temperature: Optional[float] = None,
                         max_tokens: Optional[int] = None,
                         tools: Optional[List[Dict[str, Any]]] = None,
                         tool_choice: Optional[str] = None,
                         model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate chat completion response with optional function calling

        Args:
            messages (List[Dict]): Conversation messages
            temperature (float, optional): Override default temperature
            max_tokens (int, optional): Override default max_tokens
            tools (List[Dict], optional): Function calling tools definitions
            tool_choice (str, optional): "auto", "none", or {"type": "function", "function": {"name": "..."}}
            model (str, optional): Override default model (e.g., "gpt-4o-mini" for cheaper tasks)

        Returns:
            dict: {
                'content': str,
                'success': bool,
                'error': str or None,
                'usage': dict,
                'completion_id': str,
                'tool_calls': List[Dict] or None (if AI wants to call functions)
            }
        """
        logger.info("="*60)
        logger.info("GENERATING AI RESPONSE")
        logger.info("="*60)

        # Allow model override for cost optimization (e.g., gpt-4o-mini for extraction)
        use_model = model or self.model

        logger.debug(f"Messages count: {len(messages)}")
        logger.debug(f"Model: {use_model}")
        logger.debug(f"Temperature: {temperature or self.temperature}")
        logger.debug(f"Max tokens: {max_tokens or self.max_tokens}")

        # Log message details
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            if isinstance(content, str):
                preview = content[:100] + "..." if len(content) > 100 else content
                logger.debug(f"Message {i} [{role}]: {preview}")
            elif isinstance(content, list):
                logger.debug(f"Message {i} [{role}]: Multimodal ({len(content)} parts)")
                for j, part in enumerate(content):
                    part_type = part.get('type', 'unknown')
                    logger.debug(f"  Part {j}: {part_type}")

        start_time = time.time()

        try:
            logger.info("🤖 Calling OpenAI API...")
            if tools:
                logger.debug(f"  With {len(tools)} tool(s) available for function calling")

            # Build API call parameters
            api_params = {
                'model': use_model,
                'messages': messages,
                'temperature': temperature or self.temperature,
                'max_tokens': max_tokens or self.max_tokens
            }

            # Add function calling parameters if provided
            if tools:
                api_params['tools'] = tools
                if tool_choice:
                    api_params['tool_choice'] = tool_choice

            response = self.client.chat.completions.create(**api_params)

            elapsed_time = time.time() - start_time
            message = response.choices[0].message

            # Extract content and tool calls
            content = message.content
            tool_calls = None

            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        'id': tool_call.id,
                        'type': tool_call.type,
                        'function': {
                            'name': tool_call.function.name,
                            'arguments': tool_call.function.arguments
                        }
                    })
                logger.info(f"🔧 AI wants to call {len(tool_calls)} function(s)")
                for tc in tool_calls:
                    logger.debug(f"   Function: {tc['function']['name']}")
                    logger.debug(f"   Arguments: {tc['function']['arguments'][:100]}...")

            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }

            logger.info(f"✓ Response received in {elapsed_time:.2f}s")
            logger.info(f"  Completion ID: {response.id}")
            logger.info(f"  Tokens used: {usage['total_tokens']} (prompt: {usage['prompt_tokens']}, completion: {usage['completion_tokens']})")
            if content:
                logger.info(f"  Response length: {len(content)} characters")
                logger.debug(f"  Response preview: {content[:200]}...")
            elif tool_calls:
                logger.info(f"  Response type: Function call(s)")

            logger.info("="*60)

            return {
                'content': content,
                'success': True,
                'error': None,
                'usage': usage,
                'completion_id': response.id,
                'model': response.model,
                'elapsed_time': elapsed_time,
                'tool_calls': tool_calls
            }

        except Exception as e:
            elapsed_time = time.time() - start_time

            logger.error("="*60)
            logger.error("❌ AI RESPONSE GENERATION FAILED")
            logger.error("="*60)
            logger.error(f"Error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Time elapsed: {elapsed_time:.2f}s")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'content': None,
                'success': False,
                'error': str(e),
                'usage': None,
                'completion_id': None,
                'elapsed_time': elapsed_time
            }

    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper API

        Args:
            audio_file_path (str): Path to audio file
            language (str, optional): Language code (e.g., 'en', 'ms', 'zh')

        Returns:
            dict: {
                'transcription': str,
                'success': bool,
                'error': str or None,
                'language': str
            }
        """
        logger.info("="*60)
        logger.info("TRANSCRIBING AUDIO")
        logger.info("="*60)

        logger.debug(f"Audio file: {audio_file_path}")
        logger.debug(f"Language: {language or 'auto-detect'}")

        start_time = time.time()

        try:
            with open(audio_file_path, 'rb') as audio_file:
                logger.info("🎤 Calling Whisper API...")

                if language:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language
                    )
                else:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )

            elapsed_time = time.time() - start_time
            transcription = transcript.text.strip()

            logger.info(f"✓ Transcription completed in {elapsed_time:.2f}s")
            logger.info(f"  Transcription length: {len(transcription)} characters")
            logger.debug(f"  Transcription preview: {transcription[:200]}...")
            logger.info("="*60)

            return {
                'transcription': transcription,
                'success': True,
                'error': None,
                'language': language or 'auto',
                'elapsed_time': elapsed_time
            }

        except Exception as e:
            elapsed_time = time.time() - start_time

            logger.error("="*60)
            logger.error("❌ AUDIO TRANSCRIPTION FAILED")
            logger.error("="*60)
            logger.error(f"Error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Time elapsed: {elapsed_time:.2f}s")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'transcription': None,
                'success': False,
                'error': str(e),
                'language': None,
                'elapsed_time': elapsed_time
            }
