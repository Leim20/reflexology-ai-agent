"""
Conversation Manager
Manages conversation history for multiple sessions with comprehensive logging
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """
    Manages conversation history for multiple sessions

    Features:
    - Session-based storage (in-memory)
    - Add/retrieve messages
    - Export conversations
    - Clear conversations
    - Automatic context window management
    """

    def __init__(self, max_history_length: int = 50):
        """
        Initialize Conversation Manager

        Args:
            max_history_length (int): Maximum messages to keep per session (default: 50)
        """
        logger.info("="*80)
        logger.info("INITIALIZING CONVERSATION MANAGER")
        logger.info("="*80)

        logger.debug(f"Max history length: {max_history_length}")

        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_length = max_history_length

        logger.info("✓ Conversation Manager initialized")
        logger.info("="*80)

    def create_session(self, session_id: str, system_message: str) -> None:
        """
        Create a new conversation session with system message

        Args:
            session_id (str): Unique session identifier
            system_message (str): System prompt for this conversation
        """
        logger.info(f"Creating new session: {session_id}")
        logger.debug(f"System message length: {len(system_message)} characters")
        logger.debug(f"System message preview: {system_message[:200]}...")

        self.conversations[session_id] = [
            {
                "role": "system",
                "content": system_message,
                "timestamp": datetime.now().isoformat()
            }
        ]

        logger.info(f"✓ Session created: {session_id}")
        logger.debug(f"Active sessions: {len(self.conversations)}")

    def add_message(self, session_id: str, role: str, content: Any) -> None:
        """
        Add a message to conversation history

        Args:
            session_id (str): Session identifier
            role (str): Message role ('user' or 'assistant')
            content (Any): Message content (str or list for multimodal)
        """
        logger.debug(f"Adding message to session: {session_id}")
        logger.debug(f"Role: {role}")

        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found, creating new session")
            self.create_session(session_id, "You are a helpful assistant.")

        # Log content details
        if isinstance(content, str):
            logger.debug(f"Content type: text ({len(content)} chars)")
            logger.debug(f"Content preview: {content[:100]}...")
        elif isinstance(content, list):
            logger.debug(f"Content type: multimodal ({len(content)} parts)")
        else:
            logger.debug(f"Content type: {type(content)}")

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        self.conversations[session_id].append(message)

        # Manage context window
        if len(self.conversations[session_id]) > self.max_history_length:
            removed_count = len(self.conversations[session_id]) - self.max_history_length
            # Keep system message (first) and trim old messages
            system_msg = self.conversations[session_id][0]
            self.conversations[session_id] = [system_msg] + self.conversations[session_id][-(self.max_history_length-1):]

            logger.warning(f"Context window exceeded, removed {removed_count} old messages")

        logger.debug(f"✓ Message added. Total messages in session: {len(self.conversations[session_id])}")

    def get_messages(self, session_id: str, include_system: bool = True) -> List[Dict[str, Any]]:
        """
        Get all messages for a session

        Args:
            session_id (str): Session identifier
            include_system (bool): Include system message (default: True)

        Returns:
            List[Dict]: List of messages
        """
        logger.debug(f"Getting messages for session: {session_id}")

        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found")
            return []

        messages = self.conversations[session_id]

        if not include_system and len(messages) > 0 and messages[0]['role'] == 'system':
            messages = messages[1:]

        logger.debug(f"Returning {len(messages)} messages")
        return messages

    def get_conversation_for_api(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation in format suitable for OpenAI API

        Args:
            session_id (str): Session identifier

        Returns:
            List[Dict]: Messages without timestamps
        """
        logger.debug(f"Getting conversation for API: {session_id}")

        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found")
            return []

        # Remove timestamps for API
        api_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversations[session_id]
        ]

        logger.debug(f"Prepared {len(api_messages)} messages for API")
        return api_messages

    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation for a session

        Args:
            session_id (str): Session identifier

        Returns:
            bool: True if session was cleared
        """
        logger.info(f"Clearing session: {session_id}")

        if session_id in self.conversations:
            message_count = len(self.conversations[session_id])
            del self.conversations[session_id]
            logger.info(f"✓ Session cleared ({message_count} messages removed)")
            logger.debug(f"Remaining sessions: {len(self.conversations)}")
            return True
        else:
            logger.warning(f"Session {session_id} not found")
            return False

    def export_conversation(self, session_id: str, agent_name: str = "Assistant") -> Optional[str]:
        """
        Export conversation as formatted text

        Args:
            session_id (str): Session identifier
            agent_name (str): Name of the agent for export

        Returns:
            str: Formatted conversation text, or None if session not found
        """
        logger.info(f"Exporting conversation: {session_id}")

        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found")
            return None

        messages = self.conversations[session_id]
        logger.debug(f"Exporting {len(messages)} messages")

        export_text = f"""CONVERSATION EXPORT
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Session ID: {session_id}
{'='*60}

"""

        # Skip system message (first message)
        for i, msg in enumerate(messages[1:], 1):
            role = msg['role']
            content = msg['content']
            timestamp = msg.get('timestamp', 'N/A')

            # Handle multimodal messages
            if isinstance(content, list):
                text_content = ""
                has_image = False
                for item in content:
                    if item.get('type') == 'text':
                        text_content = item.get('text', '')
                    elif item.get('type') == 'image_url':
                        has_image = True

                if role == 'user':
                    export_text += f"USER (Message {i} - {timestamp}):\n"
                    export_text += f"{text_content}\n"
                    if has_image:
                        export_text += "[Image uploaded]\n"
                else:
                    export_text += f"{agent_name.upper()} (Response {i} - {timestamp}):\n"
                    export_text += f"{text_content}\n"
            else:
                # Regular text message
                if role == 'user':
                    export_text += f"USER (Message {i} - {timestamp}):\n"
                    export_text += f"{content}\n"
                elif role == 'assistant':
                    export_text += f"{agent_name.upper()} (Response {i} - {timestamp}):\n"
                    export_text += f"{content}\n"

            export_text += "\n" + "-"*60 + "\n\n"

        export_text += f"""
{'='*60}
END OF CONVERSATION
Total Messages: {len(messages) - 1}
"""

        logger.info(f"✓ Conversation exported ({len(export_text)} characters)")
        return export_text

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all conversations

        Returns:
            dict: Statistics
        """
        logger.debug("Getting conversation statistics")

        stats = {
            'total_sessions': len(self.conversations),
            'sessions': []
        }

        for session_id, messages in self.conversations.items():
            session_stats = {
                'session_id': session_id,
                'message_count': len(messages),
                'user_messages': sum(1 for msg in messages if msg['role'] == 'user'),
                'assistant_messages': sum(1 for msg in messages if msg['role'] == 'assistant')
            }
            stats['sessions'].append(session_stats)

        logger.debug(f"Stats: {stats['total_sessions']} sessions, {sum(s['message_count'] for s in stats['sessions'])} total messages")
        return stats

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        exists = session_id in self.conversations
        logger.debug(f"Session {session_id} exists: {exists}")
        return exists
