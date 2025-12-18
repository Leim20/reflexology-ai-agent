"""
Chatwoot Handler - Option B Implementation
Manages Chatwoot API interactions for the chat agent
"""

import os
import requests
import json
import hashlib
from typing import Dict, Any, Optional
from utils import get_logger

logger = get_logger(__name__)


class ChatwootHandler:
    def __init__(self):
        self.api_token = os.getenv("CHATWOOT_API_ACCESS_TOKEN")
        self.base_url = os.getenv("CHATWOOT_BASE_URL")
        self.account_id = os.getenv("CHATWOOT_ACCOUNT_ID")
        self.inbox_id = os.getenv("CHATWOOT_INBOX_ID")
        
        if not all([self.api_token, self.base_url, self.account_id, self.inbox_id]):
            logger.error("Chatwoot configuration incomplete!")
            raise ValueError("Chatwoot configuration incomplete")
        
        self.headers = {
            "api_access_token": self.api_token,
            "Content-Type": "application/json"
        }
        
        logger.info(f"Chatwoot handler initialized - {self.base_url}")
    
    def create_or_get_contact(self, phone_number: str, name: str = None):
        response = None
        try:
            search_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts/search"
            create_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts"

            phone_clean = phone_number.strip().lstrip("+")
            variants = [phone_clean, f"+{phone_clean}"]

            # Try search with both raw and + prefixed
            for q in variants:
                response = requests.get(search_url, headers=self.headers, params={"q": q}, timeout=10)
                if response.status_code == 200:
                    contacts = response.json().get("payload", [])
                    if contacts:
                        logger.info(f"Found existing contact: {contacts[0].get('id')} for {q}")
                        return contacts[0]

            payload = {
                "inbox_id": int(self.inbox_id),
                "phone_number": variants[1],  # always send with +
            }
            if name:
                payload["name"] = name

            response = requests.post(create_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            contact = response.json().get("payload", {}).get("contact", response.json())
            logger.info(f"Created new contact: {contact.get('id')}")
            return contact
        except Exception as e:
            body = ""
            try:
                body = response.text  # type: ignore[name-defined]
            except Exception:
                body = ""
            logger.error(f"Error creating/finding contact: {e} | body={body}")
            return None
    
    def create_or_get_conversation(self, contact_id: int, source_id: str = None):
        try:
            list_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations"
            params = {"inbox_id": self.inbox_id, "status": "open"}
            response = requests.get(list_url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                conversations = response.json().get("data", {}).get("payload", [])
                for conv in conversations:
                    if conv.get("meta", {}).get("sender", {}).get("id") == contact_id:
                        logger.info(f"Found existing conversation: {conv.get('id')}")
                        return conv
            
            create_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations"
            payload = {
                "source_id": source_id or f"whatsapp_{contact_id}",
                "inbox_id": int(self.inbox_id),
                "contact_id": contact_id
            }
            response = requests.post(create_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            conversation = response.json()
            logger.info(f"Created new conversation: {conversation.get('id')}")
            return conversation
        except Exception as e:
            logger.error(f"Error creating/finding conversation: {e}")
            return None
    
    def add_message_to_conversation(self, conversation_id: int, message: str, message_type: str = "incoming", private: bool = False):
        try:
            url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
            payload = {
                "content": message,
                "message_type": message_type,
                "private": private
            }
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.debug(f"Added {message_type} message to conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False
    
    def send_message(self, conversation_id: int, message: str):
        return self.add_message_to_conversation(conversation_id, message, message_type="outgoing", private=False)
    
    def is_chatwoot_webhook(self, webhook_data: dict):
        has_event = "event" in webhook_data
        has_account = "account" in webhook_data
        has_conversation = "conversation" in webhook_data
        is_chatwoot = has_event and has_account and has_conversation
        if is_chatwoot:
            logger.debug(f"Detected Chatwoot webhook: {webhook_data.get('event')}")
        else:
            logger.debug("Detected WHAPI webhook")
        return is_chatwoot
    
    def parse_chatwoot_webhook(self, webhook_data: dict):
        try:
            event = webhook_data.get("event")
            if event != "message_created":
                logger.info(f"Skipping event: {event}")
                return None
            
            # Handle both nested message AND root-level structure
            message = webhook_data.get("message", {})
            conversation = webhook_data.get("conversation", {})
            
            # Get message_type from nested or root level
            message_type = message.get("message_type") if message else None
            if message_type is None:
                message_type = webhook_data.get("message_type")
            
            # Get content from nested or root level
            message_content_temp = message.get("content", "") if message else ""
            if not message_content_temp:
                message_content_temp = webhook_data.get("content", "")
            
            # Get sender info
            sender = message.get("sender", {}) if message else {}
            if not sender:
                sender = webhook_data.get("sender", {})
            sender_type = sender.get("type", "unknown")
            
            logger.info(f"DEBUG: message_type={message_type}, sender_type={sender_type}, content={str(message_content_temp)[:30]}...")
            
            # Accept if outgoing OR from agent (type=user)
            is_outgoing = message_type in [1, "outgoing"]
            is_from_agent = sender_type in ["user", "User"]
            
            if not is_outgoing and not is_from_agent:
                logger.info(f"Skipping (message_type={message_type}, sender_type={sender_type})")
                return None
            
            # Check private
            is_private = message.get("private", False) if message else webhook_data.get("private", False)
            if is_private:
                logger.info("Skipping private note")
                return None
            
            sender_name = sender.get("name", "unknown")
            
            # Get message content
            conversation_id = conversation.get("id")
            contact = conversation.get("meta", {}).get("sender", {})
            phone_number = contact.get("phone_number", "").replace("+", "")
            contact_name = contact.get("name", "Customer")
            message_content = str(message_content_temp).strip()
            
            if not message_content:
                logger.info("Skipping empty message")
                return None
            
            logger.info(f"   Sender Type: {sender_type}")
            logger.info(f"   Sender Name: {sender_name}")
            logger.info(f"   Message Type: {message_type}")
            logger.info(f"   Content: {message_content[:100] if len(message_content) > 0 else '(empty)'}...")
            # Extract message_id from multiple possible locations
            message_id = message.get("id")
            if not message_id:
                # Try root level (some Chatwoot webhooks have id at root)
                message_id = webhook_data.get("id")
            if not message_id:
                # Fallback: create a hash based on content + conversation_id for dedup
                content_hash = hashlib.md5(f"{conversation_id}:{message_content[:100]}".encode()).hexdigest()[:16]
                message_id = f"hash_{content_hash}"
                logger.debug(f"Using content hash for dedup: {message_id}")
            
            logger.info(f"Human agent message: Conv {conversation_id}, To {contact_name}")
            
            return {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "phone_number": phone_number,
                "contact_name": contact_name,
                "message": message_content,
                "is_human_agent": True,
                "raw_message": message,
                "raw_conversation": conversation
            }
        except Exception as e:
            logger.error(f"Error parsing Chatwoot webhook: {e}")
            return None
