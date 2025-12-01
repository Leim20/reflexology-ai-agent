"""
Escalation Tool
Handles forwarding customer messages to managers/supervisors via WhatsApp
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class EscalationTool:
    """
    Handles escalation of customer issues to human staff
    Automatically forwards customer messages to appropriate manager via WhatsApp
    """

    def __init__(self, whapi_token: str, whapi_channel_id: str, escalation_config: Dict[str, Any]):
        """
        Initialize escalation tool

        Args:
            whapi_token: Whapi API authentication token
            whapi_channel_id: Whapi channel ID for sending messages
            escalation_config: Configuration for escalation contacts and settings
        """
        self.whapi_token = whapi_token
        self.whapi_channel_id = whapi_channel_id
        self.base_url = 'https://gate.whapi.cloud'
        self.config = escalation_config
        self.enabled = escalation_config.get('enabled', True)
        self.log_escalations = escalation_config.get('log_escalations', True)
        self.log_file = escalation_config.get('log_file', 'logs/escalations.log')

        logger.info("✓ Escalation tool initialized")
        logger.debug(f"Escalation enabled: {self.enabled}")
        logger.debug(f"Logging enabled: {self.log_escalations}")


    def escalate_to_human(
        self,
        customer_name: str,
        customer_phone: str,
        customer_message: str,
        escalation_reason: str,
        platform: str = 'whatsapp',
        escalation_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        Escalate customer issue to appropriate manager

        Args:
            customer_name: Customer's name
            customer_phone: Customer's WhatsApp number
            customer_message: Original message from customer
            escalation_reason: Reason for escalation (e.g., "special discount request")
            platform: Source platform ('whatsapp' or 'web')
            escalation_type: Type of escalation to route to correct manager
                Options: 'complaint', 'special_request', 'membership', 'system_issue', 'general'

        Returns:
            dict with status, message, and manager info
        """
        if not self.enabled:
            logger.warning("Escalation attempted but escalation system is disabled")
            return {
                'success': False,
                'message': 'Escalation system is currently disabled',
                'error': 'ESCALATION_DISABLED'
            }

        try:
            logger.info("="*80)
            logger.info("🚨 ESCALATING TO HUMAN")
            logger.info("="*80)
            logger.info(f"📋 ESCALATION DETAILS:")
            logger.info(f"   Customer Name: '{customer_name}' (length: {len(customer_name)} chars)")
            logger.info(f"   Customer Phone: '{customer_phone}'")
            logger.info(f"   Escalation Type: '{escalation_type}'")
            logger.info(f"   Platform: '{platform}'")
            logger.info(f"   Reason: '{escalation_reason}'")
            logger.info(f"   Customer Message Preview: '{customer_message[:100]}...'")
            logger.info(f"   Customer Message Length: {len(customer_message)} chars")
            logger.debug(f"   FULL Customer Message: '{customer_message}'")

            # Get appropriate manager contact based on escalation type
            logger.info(f"🔍 Finding manager for escalation type: '{escalation_type}'")
            manager_contact = self.get_escalation_contact(escalation_type)

            if not manager_contact:
                logger.error(f"❌ No manager contact found for escalation type: {escalation_type}")
                return {
                    'success': False,
                    'message': 'Could not find appropriate contact for escalation',
                    'error': 'NO_CONTACT_FOUND'
                }

            logger.info(f"✓ Manager found: {manager_contact['name']} ({manager_contact['role']})")
            logger.info(f"   Manager Phone: {manager_contact['phone']}")

            # Format escalation message
            logger.info(f"📝 Formatting escalation message...")
            escalation_message = self.format_escalation_message(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_message=customer_message,
                escalation_reason=escalation_reason,
                platform=platform
            )
            logger.debug(f"   Formatted message length: {len(escalation_message)} chars")
            logger.debug(f"   Formatted message:\n{escalation_message}")

            # Send escalation message to manager via WhatsApp
            logger.info(f"📤 Sending escalation to manager: {manager_contact['phone']}")
            send_result = self._send_whatsapp_message(
                to_phone=manager_contact['phone'],
                message=escalation_message
            )

            if send_result['success']:
                logger.info(f"✅ ESCALATION SENT SUCCESSFULLY!")
                logger.info(f"   To: {manager_contact['name']} ({manager_contact['role']})")
                logger.info(f"   Phone: {manager_contact['phone']}")
                logger.info(f"   Message ID: {send_result.get('message_id', 'N/A')}")
                logger.info(f"   From Customer: {customer_name} ({customer_phone})")
                logger.info(f"   Platform: {platform}")

                # Log escalation if enabled
                if self.log_escalations:
                    logger.debug(f"📄 Logging escalation to file: {self.log_file}")
                    self.log_escalation(
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        escalation_reason=escalation_reason,
                        escalation_type=escalation_type,
                        manager_name=manager_contact['name'],
                        manager_phone=manager_contact['phone'],
                        platform=platform
                    )

                logger.info("="*80)
                return {
                    'success': True,
                    'message': f"Escalation sent to {manager_contact['name']}",
                    'manager': manager_contact,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ FAILED TO SEND ESCALATION MESSAGE!")
                logger.error(f"   Error: {send_result.get('error')}")
                logger.error(f"   Details: {send_result}")
                logger.info("="*80)
                return {
                    'success': False,
                    'message': 'Failed to send escalation message',
                    'error': send_result.get('error', 'SEND_FAILED')
                }

        except Exception as e:
            logger.error(f"Error during escalation: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Escalation failed: {str(e)}',
                'error': 'ESCALATION_ERROR'
            }


    def format_escalation_message(
        self,
        customer_name: str,
        customer_phone: str,
        customer_message: str,
        escalation_reason: str,
        platform: str
    ) -> str:
        """
        Format escalation message in standardized template

        Args:
            customer_name: Customer's name
            customer_phone: Customer's WhatsApp number
            customer_message: Original customer message
            escalation_reason: Reason for escalation
            platform: Source platform

        Returns:
            Formatted escalation message string
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = f"""🚨 ESCALATION ALERT 🚨

Customer Information:
- Name: {customer_name}
- Phone: {customer_phone}
- Platform: {platform.upper()}
- Date & Time: {timestamp}

Escalation Reason:
{escalation_reason}

Customer's Message:
"{customer_message}"

---
Please contact the customer at the above number.

Jessica Agent - Serenity Reflexology"""

        return message


    def get_escalation_contact(self, escalation_type: str) -> Optional[Dict[str, str]]:
        """
        Get appropriate manager contact based on escalation type

        Args:
            escalation_type: Type of escalation

        Returns:
            dict with manager info (name, phone, role) or None if not found
        """
        contacts = self.config.get('contacts', {})

        # Map escalation types to contact roles
        type_mapping = {
            'complaint': 'branch_manager',
            'special_request': 'branch_manager',
            'vip_customer': 'branch_manager',
            'system_issue': 'operations_manager',
            'booking_problem': 'operations_manager',
            'membership': 'membership_coordinator',
            'birthday_promotion': 'membership_coordinator',
            'general': 'customer_service_supervisor'
        }

        # Get contact key based on escalation type
        contact_key = type_mapping.get(escalation_type, 'branch_manager')

        # Get contact info
        contact_info = contacts.get(contact_key)

        if contact_info:
            return {
                'name': contact_info['name'],
                'phone': contact_info['phone'],
                'role': contact_info['role']
            }

        # Fallback to first available contact if specific type not found
        if contacts:
            first_contact_key = list(contacts.keys())[0]
            first_contact = contacts[first_contact_key]
            logger.warning(f"Escalation type '{escalation_type}' not mapped, using fallback: {first_contact_key}")
            return {
                'name': first_contact['name'],
                'phone': first_contact['phone'],
                'role': first_contact['role']
            }

        return None


    def _send_whatsapp_message(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        Send WhatsApp message via Whapi API

        Args:
            to_phone: Recipient's WhatsApp number
            message: Message text to send

        Returns:
            dict with success status and result
        """
        try:
            url = f"{self.base_url}/messages/text"
            headers = {
                "Authorization": f"Bearer {self.whapi_token}",
                "Content-Type": "application/json"
            }
            data = {
                "to": to_phone,
                "body": message
            }

            logger.debug(f"Sending escalation message to: {to_phone}")
            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 200 or response.status_code == 201:
                logger.debug(f"✓ Message sent successfully to {to_phone}")
                return {
                    'success': True,
                    'response': response.json()
                }
            else:
                logger.error(f"Failed to send message. Status: {response.status_code}, Response: {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'details': response.text
                }

        except requests.exceptions.Timeout:
            logger.error("Timeout while sending WhatsApp message")
            return {
                'success': False,
                'error': 'TIMEOUT'
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


    def log_escalation(
        self,
        customer_name: str,
        customer_phone: str,
        escalation_reason: str,
        escalation_type: str,
        manager_name: str,
        manager_phone: str,
        platform: str
    ) -> None:
        """
        Log escalation to file for tracking and analytics

        Args:
            customer_name: Customer's name
            customer_phone: Customer's phone
            escalation_reason: Reason for escalation
            escalation_type: Type of escalation
            manager_name: Manager who received escalation
            manager_phone: Manager's phone
            platform: Source platform
        """
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            log_entry = (
                f"{timestamp} | "
                f"Type: {escalation_type} | "
                f"Customer: {customer_name} ({customer_phone}) | "
                f"Reason: {escalation_reason} | "
                f"Manager: {manager_name} ({manager_phone}) | "
                f"Platform: {platform}\n"
            )

            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)

            logger.debug(f"Escalation logged to {self.log_file}")

        except Exception as e:
            logger.error(f"Failed to log escalation: {str(e)}", exc_info=True)


# Convenience functions for easy import and use

def create_escalation_tool(whapi_token: str, whapi_channel_id: str, escalation_config: Dict[str, Any]) -> EscalationTool:
    """
    Create and return an EscalationTool instance

    Args:
        whapi_token: Whapi API token
        whapi_channel_id: Whapi channel ID
        escalation_config: Escalation configuration dict

    Returns:
        EscalationTool instance
    """
    return EscalationTool(whapi_token, whapi_channel_id, escalation_config)


def escalate(
    tool: EscalationTool,
    customer_name: str,
    customer_phone: str,
    customer_message: str,
    escalation_reason: str,
    platform: str = 'whatsapp',
    escalation_type: str = 'general'
) -> Dict[str, Any]:
    """
    Quick escalation function

    Args:
        tool: EscalationTool instance
        customer_name: Customer's name
        customer_phone: Customer's phone
        customer_message: Original message
        escalation_reason: Reason for escalation
        platform: Source platform
        escalation_type: Type of escalation

    Returns:
        Result dict with success status
    """
    return tool.escalate_to_human(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_message=customer_message,
        escalation_reason=escalation_reason,
        platform=platform,
        escalation_type=escalation_type
    )
