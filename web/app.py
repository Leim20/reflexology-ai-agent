"""
Main Flask Application
Chat agent web application with WhatsApp integration
"""

import os
import secrets
import time
import random
import hashlib
import json
import atexit
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler

# Import core modules
from core import load_config, get_config, AIEngine, ConversationManager, ResponseValidator, AntiSpamManager, WebhookValidator
from handlers import WhatsAppHandler, WebHandler
from handlers.tools import process_document, process_image, process_voice, create_escalation_tool
from handlers.tools.lead_manager import LeadManager
from utils.rate_limiter import throttle_if_busy
from handlers.tools.follow_up_manager import FollowUpManager
from handlers.tools.broadcast_manager import BroadcastManager
from utils import setup_logging, get_logger, check_file_size, allowed_file

# Initialize Flask app
app = Flask(__name__)

# Will be set after config is loaded
app.secret_key = None

# Global instances (initialized in init_app())
config = None
ai_engine = None
conversation_manager = None
response_validator = None
whatsapp_handler = None
web_handler = None
escalation_tool = None
lead_manager = None
follow_up_manager = None  # Follow-up campaign manager
broadcast_manager = None  # Scheduled broadcast manager
anti_spam_manager = None  # Anti-spam protection system
webhook_validator = None  # Webhook signature verification
logger = None
scheduler = None  # Background scheduler for follow-up campaigns and broadcasts

# Track escalated messages to prevent spam (message_id -> timestamp)
escalated_messages = set()

# Track processed messages to prevent duplicate responses (message_id -> timestamp)
processed_messages = {}
PROCESSED_MESSAGE_TIMEOUT = 300  # Keep message IDs for 5 minutes

# ============================================================================
# HELPER FUNCTIONS - MEMORY SYSTEM
# ============================================================================

def build_tiered_memory(customer_memory: dict) -> str:
    """
    Build tiered memory context for AI (optimized for token usage)

    Format (configurable in config.json):
    - Recent 3 conversations: Detailed summaries
    - Conversations 4-10: Medium detail
    - Conversations 11-20: Brief mention

    Args:
        customer_memory: Dict from lead_manager.get_customer_memory()

    Returns:
        Formatted memory string for AI context
    """
    if not customer_memory or not customer_memory.get('is_returning'):
        return ""

    # Get config settings (with defaults)
    recent_detailed = config.get('memory.tiered_detail.recent_detailed', 3)
    medium_detail = config.get('memory.tiered_detail.medium_detail', 10)
    brief_mention = config.get('memory.tiered_detail.brief_mention', 20)

    name = customer_memory.get('name', 'Unknown')
    preferences = customer_memory.get('preferences', 'None')
    total_convs = customer_memory.get('total_conversations', 0)
    last_visit = customer_memory.get('last_visit', 'Unknown')
    current_interest = customer_memory.get('current_interest', 'Unknown')
    conversation_history = customer_memory.get('conversation_history', [])

    # Build memory text
    memory_parts = []

    # Customer summary
    memory_parts.append(f"RETURNING CUSTOMER: {name}")
    memory_parts.append(f"Total Conversations: {total_convs}")
    memory_parts.append(f"Last Visit: {last_visit}")
    memory_parts.append(f"Current Interest: {current_interest}")
    if preferences and preferences != 'None':
        memory_parts.append(f"Preferences: {preferences}")

    # Conversation history (tiered)
    if conversation_history:
        memory_parts.append("\nCONVERSATION HISTORY:")

        # Reverse to get most recent first
        history_reversed = list(reversed(conversation_history))

        # Recent: Detailed
        for i, conv in enumerate(history_reversed[:recent_detailed]):
            memory_parts.append(f"\n[Recent {i+1}] {conv['date']}")
            memory_parts.append(f"  Summary: {conv['summary']}")
            memory_parts.append(f"  Interest: {conv['category']}")

        # Medium detail
        if len(history_reversed) > recent_detailed:
            memory_parts.append(f"\n[Earlier conversations {recent_detailed+1}-{medium_detail}]:")
            for conv in history_reversed[recent_detailed:medium_detail]:
                memory_parts.append(f"  - {conv['date']}: {conv['category']}")

        # Brief
        if len(history_reversed) > medium_detail:
            categories = [conv['category'] for conv in history_reversed[medium_detail:brief_mention]]
            memory_parts.append(f"\n[Older conversations {medium_detail+1}-{brief_mention}]: {', '.join(categories)}")

    return "\n".join(memory_parts)


# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

def init_app():
    """
    Initialize the application

    - Load configuration
    - Setup logging
    - Initialize AI engine
    - Initialize conversation manager
    - Initialize handlers
    - Initialize anti-spam protection
    """
    global config, ai_engine, conversation_manager, response_validator
    global whatsapp_handler, web_handler, escalation_tool, lead_manager, follow_up_manager, broadcast_manager
    global anti_spam_manager, webhook_validator, logger, scheduler

    print("="*80)
    print("INITIALIZING CHAT AGENT APPLICATION")
    print("="*80)

    # Load configuration
    config = load_config()

    # Setup logging
    agent_name = config.get('agent.name', 'ChatAgent')
    log_level = config.get('logging.level', 'DEBUG')
    log_dir = config.get('logging.log_dir', 'logs')

    # Convert log level string to logging constant
    import logging
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level_int = log_level_map.get(log_level, logging.DEBUG)

    setup_logging(log_dir=log_dir, log_level=log_level_int, agent_name=agent_name)
    logger = get_logger(__name__)

    logger.info("="*80)
    logger.info("APPLICATION INITIALIZATION STARTING")
    logger.info("="*80)

    # Set Flask secret key
    flask_secret = config.get_env('FLASK_SECRET_KEY')
    if not flask_secret or flask_secret.startswith('{{'):
        logger.warning("FLASK_SECRET_KEY not set, generating random key")
        flask_secret = secrets.token_hex(32)

    app.secret_key = flask_secret
    logger.info("✓ Flask secret key configured")

    # Initialize AI Engine
    openai_key = config.get_env('OPENAI_API_KEY')
    if not openai_key or openai_key.startswith('{{'):
        logger.error("❌ OPENAI_API_KEY not configured!")
        raise ValueError("OPENAI_API_KEY must be set in .env file")

    ai_engine = AIEngine(
        api_key=openai_key,
        model=config.get('ai.model', 'gpt-4o'),
        temperature=config.get('ai.temperature', 0.7),
        max_tokens=config.get('ai.max_tokens', 1500)
    )
    logger.info("✓ AI Engine initialized")

    # Initialize Conversation Manager
    conversation_manager = ConversationManager(max_history_length=50)
    logger.info("✓ Conversation Manager initialized")

    # Initialize Response Validator
    knowledge_base = config.knowledge_base if config.has_knowledge_base else ""
    response_validator = ResponseValidator(knowledge_base=knowledge_base)
    logger.info("✓ Response Validator initialized")

    # Initialize WhatsApp Handler (if enabled)
    if config.get('platforms.whatsapp.enabled', False):
        whapi_token = config.get_env('WHAPI_API_TOKEN')
        if whapi_token and not whapi_token.startswith('{{'):
            whatsapp_handler = WhatsAppHandler(api_token=whapi_token)
            logger.info("✓ WhatsApp Handler initialized")
        else:
            logger.warning("WhatsApp enabled but WHAPI_API_TOKEN not configured")

    # Initialize Escalation Tool (if enabled)
    if config.get('escalation.enabled', False):
        whapi_token = config.get_env('WHAPI_API_TOKEN')
        whapi_channel_id = config.get_env('WHAPI_CHANNEL_ID')
        escalation_config = config.get('escalation', {})

        if whapi_token and not whapi_token.startswith('{{'):
            escalation_tool = create_escalation_tool(
                whapi_token=whapi_token,
                whapi_channel_id=whapi_channel_id,
                escalation_config=escalation_config
            )
            logger.info("✓ Escalation Tool initialized")
        else:
            logger.warning("Escalation enabled but WHAPI_API_TOKEN not configured")

    # Initialize Lead Manager (if enabled)
    if config.get('lead_tracking.enabled', False):
        try:
            credentials_file = config.get('lead_tracking.credentials_file', '<PUT_YOUR_GOOGLE_CREDENTIALS_PATH_HERE>')  # <-- put your Google credentials path here
            spreadsheet_name = config.get('lead_tracking.spreadsheet_name', 'Customer record')

            lead_manager = LeadManager(
                credentials_file=credentials_file,
                spreadsheet_name=spreadsheet_name
            )
            logger.info("✓ Lead Manager initialized")

            # Initialize Follow-up Manager (uses same credentials)
            try:
                follow_up_manager = FollowUpManager(
                    credentials_file=credentials_file,
                    spreadsheet_name=spreadsheet_name
                )
                logger.info("✓ Follow-up Manager initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Follow-up Manager: {e}")
                logger.warning("   Follow-up campaigns will be disabled")
                follow_up_manager = None

            # Initialize Broadcast Manager (uses same credentials)
            try:
                broadcast_manager = BroadcastManager(
                    credentials_file=credentials_file,
                    spreadsheet_name=spreadsheet_name
                )
                logger.info("✓ Broadcast Manager initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Broadcast Manager: {e}")
                logger.warning("   Scheduled broadcasts will be disabled")
                broadcast_manager = None

        except Exception as e:
            logger.error(f"❌ Failed to initialize Lead Manager: {e}")
            logger.warning("   Lead tracking will be disabled")
            lead_manager = None
            follow_up_manager = None
            broadcast_manager = None

    # Initialize Web Handler
    web_handler = WebHandler()
    logger.info("✓ Web Handler initialized")

    # Initialize Anti-Spam Manager
    anti_spam_config = config.get('anti_spam', {})
    anti_spam_manager = AntiSpamManager(config=anti_spam_config)
    logger.info("✓ Anti-Spam Manager initialized")

    # Initialize Webhook Validator (for Whapi signature verification)
    webhook_secret = config.get_env('WHAPI_WEBHOOK_SECRET')
    webhook_validator = WebhookValidator(webhook_secret=webhook_secret)
    if webhook_secret and not webhook_secret.startswith('{{'):
        logger.info("✓ Webhook Validator initialized (signature verification enabled)")
    else:
        logger.warning("⚠️ Webhook signature verification disabled (WHAPI_WEBHOOK_SECRET not set)")

    # Create required directories
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # Initialize Background Scheduler for follow-up campaigns
    scheduler = BackgroundScheduler()

    # Register scheduler jobs
    if follow_up_manager and lead_manager and whatsapp_handler:
        # Job 1: Check and enroll leads in campaigns (every 10 minutes)
        scheduler.add_job(
            func=check_and_enroll_leads_job,
            trigger='interval',
            minutes=10,
            seconds=random.randint(-60, 60),  # Fix #5: Add jitter
            id='check_enroll_leads',
            name='Check and enroll leads in follow-up campaigns',
            replace_existing=True
        )

        # Job 2: Process pending follow-ups (every 5 minutes)
        scheduler.add_job(
            func=process_pending_followups_job,
            trigger='interval',
            minutes=5,
            seconds=random.randint(-30, 30),  # Fix #5: Add jitter
            id='process_followups',
            name='Process and send pending follow-up messages',
            replace_existing=True
        )

        logger.info("✓ Follow-up scheduler jobs registered")
        logger.info("   - Check enrollments: Every 10 minutes")
        logger.info("   - Process follow-ups: Every 5 minutes")
    else:
        logger.warning("⚠️  Follow-up scheduler jobs not registered (missing dependencies)")

    # Register broadcast scheduler job
    if broadcast_manager and whatsapp_handler:
        # Job 3: Check and send scheduled broadcasts (every 1 minute)
        scheduler.add_job(
            func=check_and_send_broadcasts_job,
            trigger='interval',
            minutes=1,
            seconds=random.randint(-15, 15),  # Fix #5: Add jitter
            id='check_send_broadcasts',
            name='Check and send scheduled broadcast messages',
            replace_existing=True
        )

        logger.info("✓ Broadcast scheduler job registered")
        logger.info("   - Check broadcasts: Every 1 minute")
    else:
        logger.warning("⚠️  Broadcast scheduler job not registered (missing dependencies)")

    scheduler.start()
    logger.info("✓ Background Scheduler initialized")

    # Register shutdown handler to stop scheduler gracefully
    atexit.register(lambda: scheduler.shutdown() if scheduler else None)

    logger.info("="*80)
    logger.info("✅ APPLICATION INITIALIZATION COMPLETE")
    logger.info("="*80)

# ============================================================================
# FOLLOW-UP CAMPAIGN SCHEDULER JOBS
# ============================================================================

def check_and_enroll_leads_job():
    """
    Scheduler job: Check all leads and enroll them in matching campaigns
    Runs every 10 minutes
    """
    try:
        if not follow_up_manager or not lead_manager:
            return

        logger.info("🔄 [SCHEDULER] Running check_and_enroll_leads_job...")
        stats = follow_up_manager.check_and_enroll_leads(lead_manager)
        logger.info(f"✅ [SCHEDULER] Enrolled {stats.get('enrolled', 0)} leads in campaigns")

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Error in check_and_enroll_leads_job: {e}")


def process_pending_followups_job():
    """
    Scheduler job: Process and send pending follow-up messages
    Runs every 5 minutes
    """
    try:
        if not follow_up_manager or not whatsapp_handler:
            return

        logger.info("🔄 [SCHEDULER] Running process_pending_followups_job...")

        # Get all pending follow-ups
        pending = follow_up_manager.get_pending_followups()

        if not pending:
            logger.info("   No pending follow-ups to send")
            return

        logger.info(f"   Found {len(pending)} pending follow-ups")

        sent_count = 0
        error_count = 0

        for followup in pending:
            try:
                phone = followup.get('Phone', '')
                campaign_id = followup.get('Campaign ID', '')

                # Get next message
                message_text, message_number = follow_up_manager.get_next_message(phone, campaign_id)

                if not message_text:
                    logger.warning(f"   ⚠️  No message found for {phone}, campaign {campaign_id}")
                    continue

                # Send via WhatsApp
                logger.info(f"   📤 Sending message {message_number} to {phone}")
                result = whatsapp_handler.send_message(to=phone, message=message_text)

                if result.get('success'):
                    # Mark as sent
                    follow_up_manager.mark_followup_sent(
                        phone=phone,
                        campaign_id=campaign_id,
                        message_number=message_number,
                        message_text=message_text
                    )
                    sent_count += 1
                    logger.info(f"   ✅ Sent successfully to {phone}")
                else:
                    error_count += 1
                    logger.error(f"   ❌ Failed to send to {phone}: {result.get('message')}")

            except Exception as e:
                error_count += 1
                logger.error(f"   ❌ Error processing follow-up: {e}")

        logger.info(f"✅ [SCHEDULER] Sent {sent_count} follow-ups, {error_count} errors")

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Error in process_pending_followups_job: {e}")


# ============================================================================
# BROADCAST SCHEDULER JOB
# ============================================================================

def check_and_send_broadcasts_job():
    """
    Scheduler job: Check for scheduled broadcasts and send them
    Runs every 1 minute
    """
    try:
        if not broadcast_manager or not whatsapp_handler:
            return

        logger.debug("🔄 [SCHEDULER] Checking for pending broadcasts...")

        # Get all broadcasts ready to send
        pending_broadcasts = broadcast_manager.get_pending_broadcasts()

        if not pending_broadcasts:
            logger.debug("   No pending broadcasts")
            return

        logger.info(f"📢 [SCHEDULER] Found {len(pending_broadcasts)} broadcasts ready to send")

        # Send each broadcast
        for broadcast in pending_broadcasts:
            broadcast_id = broadcast.get('Broadcast ID', 'UNKNOWN')
            title = broadcast.get('Title', 'Untitled')

            logger.info(f"📤 [SCHEDULER] Sending broadcast: {broadcast_id} - {title}")

            # Define send function to pass to broadcast_manager
            def send_whatsapp_message(phone: str, message: str) -> bool:
                """Helper function to send WhatsApp message"""
                try:
                    result = whatsapp_handler.send_message(to=phone, message=message)
                    return result.get('success', False)
                except Exception as e:
                    logger.error(f"❌ Error sending WhatsApp message to {phone}: {e}")
                    return False

            # Send broadcast to all recipients
            stats = broadcast_manager.send_broadcast(broadcast, send_whatsapp_message)

            logger.info(f"✅ [SCHEDULER] Broadcast {broadcast_id} sent:")
            logger.info(f"   Delivered: {stats.get('sent', 0)}/{stats.get('total', 0)}")
            logger.info(f"   Failed: {stats.get('failed', 0)}/{stats.get('total', 0)}")

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Error in check_and_send_broadcasts_job: {e}")


# Initialize app on module load
init_app()

# ============================================================================
# FUNCTION CALLING - ESCALATION
# ============================================================================

def get_escalation_function_definition():
    """
    Define escalation function for OpenAI function calling

    This tells OpenAI about the escalate_to_human function and when/how to use it.
    """
    return {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate customer inquiry to human manager or staff member when you cannot help or when they request it. Use this when: customer needs special assistance (discounts, group bookings, custom packages), has complaints about service, asks to speak with manager, has complex membership/billing questions, or inquiry requires human judgment. DO NOT use for simple price/service inquiries you can answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_message": {
                        "type": "string",
                        "description": "The customer's original message or request that needs escalation"
                    },
                    "escalation_reason": {
                        "type": "string",
                        "description": "Brief clear reason why escalation is needed (e.g., 'Customer requests group discount for 25 people', 'Complaint about service quality', 'Complex membership inquiry about points')"
                    },
                    "escalation_type": {
                        "type": "string",
                        "enum": ["special_request", "complaint", "membership", "system_issue", "general"],
                        "description": "Type of escalation to route to correct manager: special_request (discounts/custom packages/group bookings), complaint (service issues/quality problems), membership (billing/points/birthday promotions), system_issue (booking problems/technical issues), general (other inquiries)"
                    }
                },
                "required": ["customer_message", "escalation_reason", "escalation_type"]
            }
        }
    }


def get_register_member_function_definition():
    """
    Define register_member function for OpenAI function calling

    This tells OpenAI about the register_member function and when/how to use it.
    """
    return {
        "type": "function",
        "function": {
            "name": "register_member",
            "description": "Register a new member in the Members database when customer provides their Name, Phone, and Birthday. ONLY call this function AFTER customer confirms their information is correct. Do NOT call this speculatively - wait for explicit confirmation from customer (e.g., '对', '是的', '正确', 'yes', 'correct').",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's full name as provided by them (e.g., '李明', 'John Smith')"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number as provided by them (e.g., '60123456789', '012-345-6789', '+60 12-345 6789'). Extract digits only from any format they provide."
                    },
                    "customer_birthday": {
                        "type": "string",
                        "description": "Customer's birthday in YYYY-MM-DD format (e.g., '1990-05-15'). Convert from any format they provide to YYYY-MM-DD."
                    }
                },
                "required": ["customer_name", "customer_phone", "customer_birthday"]
            }
        }
    }


def handle_register_member_function_call(
    function_args: dict,
    whatsapp_phone: str
) -> dict:
    """
    Handle register_member function call from AI

    This is called when AI decides to register a customer as member.
    It executes the registration and returns result to AI.

    Args:
        function_args: Arguments from AI (customer_name, customer_phone, customer_birthday)
        whatsapp_phone: Customer's WhatsApp phone (for logging/fallback only)

    Returns:
        dict with success status and message for AI
    """
    logger.info("="*80)
    logger.info("👤 HANDLING MEMBER REGISTRATION FUNCTION CALL")
    logger.info("="*80)

    # Extract function arguments provided by AI
    customer_name = function_args.get('customer_name', '')
    customer_phone = function_args.get('customer_phone', '')
    customer_birthday = function_args.get('customer_birthday', '')

    logger.info(f"📋 Function Arguments from AI:")
    logger.info(f"   Name: '{customer_name}'")
    logger.info(f"   Phone: '{customer_phone}' (provided by customer)")
    logger.info(f"   WhatsApp Phone: '{whatsapp_phone}' (for reference)")
    logger.info(f"   Birthday: '{customer_birthday}'")

    # Validate inputs
    if not customer_name or not customer_phone or not customer_birthday:
        logger.error("❌ Missing required fields for registration")
        return {
            'success': False,
            'message': 'Missing name, phone, or birthday information'
        }

    # Validate birthday format (should be YYYY-MM-DD)
    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', customer_birthday):
        logger.error(f"❌ Invalid birthday format: {customer_birthday}")
        return {
            'success': False,
            'message': f'Invalid birthday format: {customer_birthday}. Expected YYYY-MM-DD.'
        }

    # Call lead_manager.register_member()
    if not lead_manager:
        logger.error("❌ Lead manager not available")
        return {
            'success': False,
            'message': 'Member registration system not available'
        }

    try:
        # Normalize phone number
        normalized_phone = customer_phone.replace('@s.whatsapp.net', '')

        logger.info("🔄 Calling lead_manager.register_member()...")
        result = lead_manager.register_member(
            phone=normalized_phone,
            name=customer_name,
            birthday=customer_birthday
        )

        if result['success']:
            action = result['action']
            row = result['row']

            logger.info(f"✅ Registration {action}: Row {row}")
            logger.info(f"   Name: {customer_name}")
            logger.info(f"   Birthday: {customer_birthday}")
            logger.info(f"   Phone: {normalized_phone}")
            logger.info("="*80)

            # Return success message for AI
            if action == 'created':
                return {
                    'success': True,
                    'message': f'Member registered successfully! Name: {customer_name}, Birthday: {customer_birthday}',
                    'action': 'created'
                }
            elif action == 'updated':
                return {
                    'success': True,
                    'message': f'Member information updated. Name: {customer_name}, Birthday: {customer_birthday}',
                    'action': 'updated'
                }
            else:  # already_exists
                return {
                    'success': True,
                    'message': f'Member already registered with this information.',
                    'action': 'already_exists'
                }
        else:
            logger.error(f"❌ Registration failed: {result['message']}")
            logger.error("="*80)
            return {
                'success': False,
                'message': f'Registration failed: {result["message"]}'
            }

    except Exception as e:
        logger.error(f"❌ Exception during member registration: {str(e)}")
        logger.exception("Full error traceback:")
        logger.error("="*80)
        return {
            'success': False,
            'message': f'Error during registration: {str(e)}'
        }


def handle_escalation_function_call(
    function_args: dict,
    customer_phone: str,
    customer_name: str,
    message_id: str,
    platform: str
) -> dict:
    """
    Handle escalation function call from AI

    This is called when AI decides to escalate a customer inquiry.
    It executes the actual escalation and returns result to AI.

    Args:
        function_args: Arguments from AI (customer_message, escalation_reason, escalation_type)
        customer_phone: Customer's phone number
        customer_name: Customer's name (or phone if name not available)
        message_id: Message ID for deduplication
        platform: 'whatsapp' or 'web'

    Returns:
        dict with success status and message for AI
    """
    logger.info("="*80)
    logger.info("🚨 HANDLING ESCALATION FUNCTION CALL")
    logger.info("="*80)

    # Extract function arguments provided by AI
    customer_message = function_args.get('customer_message', '')
    escalation_reason = function_args.get('escalation_reason', '')
    escalation_type = function_args.get('escalation_type', 'general')

    logger.info(f"📋 Function Arguments from AI:")
    logger.info(f"   Customer Message: '{customer_message[:100]}...'")
    logger.info(f"   Escalation Reason: '{escalation_reason}'")
    logger.info(f"   Escalation Type: '{escalation_type}'")
    logger.info(f"   Customer Name: '{customer_name}'")
    logger.info(f"   Customer Phone: '{customer_phone}'")
    logger.info(f"   Platform: '{platform}'")

    # Create unique escalation ID to prevent duplicates
    escalation_id = f"{platform}_{customer_phone}_{message_id}"

    # Check if already escalated (spam prevention)
    if escalation_id in escalated_messages:
        logger.info(f"⏭️ DUPLICATE ESCALATION DETECTED - SKIPPING")
        logger.info(f"   Escalation ID: {escalation_id}")
        logger.info("="*80)
        return {
            "success": False,
            "message": "This request has already been forwarded to the manager. They will contact the customer soon."
        }

    logger.info(f"✓ New escalation (not a duplicate)")

    # Trigger escalation if tool is available
    if escalation_tool:
        logger.info(f"✓ Escalation tool available - executing...")

        escalation_result = escalation_tool.escalate_to_human(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_message=customer_message,
            escalation_reason=escalation_reason,
            platform=platform,
            escalation_type=escalation_type
        )

        if escalation_result['success']:
            logger.info(f"✅ ESCALATION SUCCESSFUL!")
            logger.info(f"   Sent to: {escalation_result['manager']['name']}")
            logger.info(f"   Manager Role: {escalation_result['manager']['role']}")
            logger.info("="*80)

            # Mark as escalated to prevent duplicates
            escalated_messages.add(escalation_id)
            logger.debug(f"   Added to escalated_messages set (total: {len(escalated_messages)})")

            return {
                "success": True,
                "message": f"Request successfully forwarded to {escalation_result['manager']['name']} ({escalation_result['manager']['role']}). They will contact the customer at {customer_phone} shortly."
            }
        else:
            logger.error(f"❌ ESCALATION FAILED!")
            logger.error(f"   Error: {escalation_result.get('message')}")
            logger.error("="*80)
            return {
                "success": False,
                "message": f"Unable to forward request: {escalation_result.get('message')}"
            }
    else:
        logger.warning("⚠️ Escalation tool not available!")
        logger.warning("   Check if escalation_tool was initialized properly")
        logger.info("="*80)
        return {
            "success": False,
            "message": "Escalation system is currently unavailable. Please have the customer contact us directly."
        }


# ============================================================================
# ROUTES - WEB CHAT
# ============================================================================

@app.route('/')
def index():
    """Render main chat interface"""
    logger.info("="*60)
    logger.info("WEB CHAT PAGE ACCESSED")
    logger.info("="*60)

    # Create new session ID
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
        logger.info(f"New session created: {session['session_id']}")

    logger.debug(f"Rendering index.html for session: {session['session_id']}")
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and file uploads"""
    logger.info("="*80)
    logger.info("CHAT REQUEST RECEIVED")
    logger.info("="*80)

    start_time = time.time()

    try:
        user_message = request.form.get('message', '').strip()
        file = request.files.get('file')

        session_id = session.get('session_id')
        logger.debug(f"Session ID: {session_id}")
        logger.debug(f"User message: {user_message[:100]}..." if user_message else "No message text")
        logger.debug(f"File uploaded: {file.filename if file else 'No'}")

        if not session_id:
            logger.error("No session ID found")
            return jsonify({'error': 'Session expired. Please refresh the page.'}), 400

        # ===================================================================
        # ANTI-SPAM CHECK - Web Chat
        # ===================================================================
        if anti_spam_manager and user_message:
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address:
                ip_address = ip_address.split(',')[0].strip()  # Get first IP if multiple

            allowed, reason = anti_spam_manager.check_message(
                user_id=f"web_{session_id}",
                message=user_message,
                ip_address=ip_address
            )

            if not allowed:
                logger.warning(f"🚫 Message blocked by anti-spam: {reason}")
                return jsonify({
                    'error': reason,
                    'success': False,
                    'spam_blocked': True
                }), 429  # 429 Too Many Requests

            logger.debug("✅ Anti-spam check passed")
            # THROTTLE: Check rate limit before making any API calls
            try:
                throttle_if_busy()
            except Exception as e:
                logger.warning(f"Rate limiter check: {e}")
        # ===================================================================

        # Initialize conversation if new
        if not conversation_manager.session_exists(session_id):
            logger.info(f"Initializing new conversation for session: {session_id}")

            # Get appropriate system prompt
            if config.has_knowledge_base:
                system_prompt = config.get_prompt('web_with_knowledge')
            else:
                system_prompt = config.get_prompt('web_without_knowledge')

            conversation_manager.create_session(session_id, system_prompt)

        # Process uploaded file if present
        file_result = None
        if file and file.filename and allowed_file(file.filename):
            logger.info(f"Processing uploaded file: {file.filename}")

            filename = secure_filename(file.filename)
            file_path = os.path.join('data/uploads', f"{session_id}_{filename}")
            file.save(file_path)

            logger.debug(f"File saved to: {file_path}")

            # Check file size
            size_check = check_file_size(file_path, filename)

            if not size_check['valid']:
                logger.warning(f"File size check failed: {size_check['error']}")
                try:
                    os.remove(file_path)
                except:
                    pass
                return jsonify({'error': size_check['error'], 'success': False}), 400

            # Process the file based on type
            try:
                from utils.helpers import is_image_file, is_document_file, is_voice_file, get_file_extension

                ext = get_file_extension(filename)

                if is_document_file(filename):
                    logger.info("Processing document...")
                    content = process_document(file_path, ext)
                    file_result = {'type': 'document', 'content': content}

                elif is_image_file(filename):
                    logger.info("Processing image...")
                    base64_data, mime_type = process_image(file_path, ext)
                    file_result = {'type': 'image', 'content': base64_data, 'mime_type': mime_type}

                elif is_voice_file(filename):
                    logger.info("Processing voice...")
                    voice_result = process_voice(file_path, ext, ai_engine)
                    file_result = {'type': 'voice', 'content': voice_result['transcription'],
                                  'audio_info': voice_result['audio_info']}

                logger.info(f"✓ File processed successfully: {file_result['type']}")

            except Exception as e:
                logger.error(f"❌ File processing failed: {str(e)}")
                logger.exception("Full error traceback:")
                try:
                    os.remove(file_path)
                except:
                    pass
                return jsonify({'error': f"File processing error: {str(e)}", 'success': False}), 400

            finally:
                # Clean up uploaded file
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug("Temporary file cleaned up")
                except:
                    pass

        # Build user message
        if file_result:
            logger.info(f"Building multimodal message (type: {file_result['type']})")

            if file_result['type'] == 'document':
                full_message = f"{user_message}\n\n[Uploaded Document]:\n{file_result['content']}" if user_message else f"[Uploaded Document]:\n{file_result['content']}"
                conversation_manager.add_message(session_id, 'user', full_message)

            elif file_result['type'] == 'image':
                message_content = [
                    {"type": "text", "text": user_message if user_message else "I've uploaded an image. Please analyze it."}
                ]
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{file_result['mime_type']};base64,{file_result['content']}"}
                })
                conversation_manager.add_message(session_id, 'user', message_content)

            elif file_result['type'] == 'voice':
                transcription = file_result['content']
                audio_info = file_result['audio_info']
                full_message = f"{user_message}\n\n[Voice Message - {audio_info['estimated_duration_min']} min]:\n{transcription}" if user_message else f"[Voice Message]:\n{transcription}"
                conversation_manager.add_message(session_id, 'user', full_message)

        else:
            # Text-only message
            if not user_message:
                logger.warning("No message and no file provided")
                return jsonify({'error': 'Please provide a message or upload a file'}), 400

            conversation_manager.add_message(session_id, 'user', user_message)

        # Generate AI response
        logger.info("Calling AI Engine...")
        messages = conversation_manager.get_conversation_for_api(session_id)
        ai_response = ai_engine.generate_response(messages)

        if not ai_response['success']:
            logger.error(f"AI response generation failed: {ai_response['error']}")
            return jsonify({'error': f"AI error: {ai_response['error']}", 'success': False}), 500

        assistant_message = ai_response['content']
        logger.info(f"✓ AI response received ({len(assistant_message)} chars)")

        # Validate response if feature enabled
        if config.get('features.response_validation', True) and config.has_knowledge_base:
            logger.info("Validating response...")
            validation_result = response_validator.validate(assistant_message)
            logger.info(f"Validation: confidence={validation_result['confidence']:.1%}, valid={validation_result['is_valid']}")

        # ===================================================================
        # ESCALATION DETECTION - Auto-trigger if AI mentions forwarding
        # ===================================================================
        escalation_keywords = [
            'forward this to',
            'forward your request to',
            'forward your inquiry to',
            "i'll forward",
            'forwarding to our',
            'let me forward'
        ]

        assistant_lower = assistant_message.lower()
        if any(keyword in assistant_lower for keyword in escalation_keywords):
            logger.info("🚨 Escalation detected in AI response!")

            try:
                # Create unique escalation ID to prevent duplicates
                message_hash = hashlib.md5(user_message.encode()).hexdigest()[:8]
                escalation_id = f"web_{session_id}_{message_hash}"

                # Check if already escalated
                if escalation_id in escalated_messages:
                    logger.info(f"⏭️ Escalation already sent for this message, skipping")
                else:
                    # Extract customer info from session
                    customer_name = session.get('customer_name', 'Web User')
                    customer_phone = session.get('customer_phone', 'Web chat - no phone provided')

                    # Determine escalation type based on AI response
                    if 'branch manager' in assistant_lower:
                        escalation_type = 'special_request'
                    elif 'operations manager' in assistant_lower:
                        escalation_type = 'system_issue'
                    elif 'membership coordinator' in assistant_lower:
                        escalation_type = 'membership'
                    else:
                        escalation_type = 'general'

                    # Trigger escalation if tool is available
                    if escalation_tool:
                        escalation_result = escalation_tool.escalate_to_human(
                            customer_name=customer_name,
                            customer_phone=customer_phone,
                            customer_message=user_message,
                            escalation_reason=f"Web chat inquiry - {user_message[:100]}",
                            platform='web',
                            escalation_type=escalation_type
                        )

                        if escalation_result['success']:
                            logger.info(f"✓ Escalation sent to {escalation_result['manager']['name']}")
                            # Mark as escalated to prevent duplicates
                            escalated_messages.add(escalation_id)
                        else:
                            logger.error(f"❌ Escalation failed: {escalation_result.get('message')}")
                    else:
                        logger.warning("Escalation tool not available")

            except Exception as e:
                logger.error(f"Error during escalation: {str(e)}", exc_info=True)
        # ===================================================================

        # Add assistant response to conversation
        conversation_manager.add_message(session_id, 'assistant', assistant_message)

        elapsed_time = time.time() - start_time
        logger.info(f"✅ Chat request completed in {elapsed_time:.2f}s")
        logger.info("="*80)

        return jsonify({
            'response': assistant_message,
            'success': True
        })

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ Chat request failed after {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        logger.error("="*80)

        return jsonify({
            'error': f"An error occurred: {str(e)}",
            'success': False
        }), 500


@app.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    logger.info("Clear conversation requested")

    session_id = session.get('session_id')
    if session_id:
        conversation_manager.clear_session(session_id)
        logger.info(f"✓ Conversation cleared for session: {session_id}")

    return jsonify({'success': True})


@app.route('/export', methods=['GET'])
def export_conversation():
    """Export conversation history as text file"""
    logger.info("Export conversation requested")

    session_id = session.get('session_id')
    if not session_id or not conversation_manager.session_exists(session_id):
        logger.warning("No conversation to export")
        return jsonify({'error': 'No conversation to export'}), 400

    agent_name = config.get('agent.name', 'Assistant')
    export_text = conversation_manager.export_conversation(session_id, agent_name)

    if not export_text:
        return jsonify({'error': 'Failed to export conversation'}), 500

    logger.info(f"✓ Conversation exported ({len(export_text)} chars)")

    return jsonify({
        'success': True,
        'content': export_text,
        'filename': f"{agent_name.lower()}_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    })


# ============================================================================
# HELPER FUNCTIONS - MENU IMAGE
# ============================================================================

def should_send_menu_image(message: str, config) -> tuple:
    """
    Check if customer message contains menu/price keywords and return menu image info.

    Args:
        message (str): Customer's message text
        config: Configuration object with menu_image settings

    Returns:
        tuple: (should_send: bool, image_url: str, caption: str, language: str)
    """
    menu_config = config.get('menu_image', {})

    # Check if feature is enabled
    if not menu_config.get('enabled', False):
        return False, None, None, None

    # Get keywords from config
    keywords = menu_config.get('send_for_keywords', [])

    # Normalize message for comparison
    message_lower = message.lower().strip()

    # Check if any keyword matches
    for keyword in keywords:
        if keyword.lower() in message_lower:
            # Detect language - simple check for Chinese characters
            is_chinese = any(ord(char) > 127 for char in message if char.isalpha() or ord(char) > 127)

            if is_chinese:
                image_url = menu_config.get('chinese_url')
                caption = menu_config.get('caption_chinese', '')
                language = 'chinese'
            else:
                image_url = menu_config.get('english_url')
                caption = menu_config.get('caption_english', '')
                language = 'english'

            return True, image_url, caption, language

    return False, None, None, None


# ============================================================================
# ROUTES - WHATSAPP WEBHOOK
# ============================================================================

@app.route('/webhook/whapi', methods=['POST'])
def whapi_webhook():
    """Webhook endpoint to receive WhatsApp messages from Whapi"""
    logger.info("="*80)
    logger.info("WHATSAPP WEBHOOK RECEIVED")
    logger.info("="*80)

    start_time = time.time()

    try:
        # ===================================================================
        # WEBHOOK SIGNATURE VERIFICATION
        # Verify the webhook is authentic and from Whapi
        # ===================================================================
        if webhook_validator and webhook_validator.enabled:
            signature = request.headers.get('X-Webhook-Signature', '')
            if not signature:
                logger.warning("🚫 No webhook signature provided")
                return jsonify({'success': False, 'error': 'Missing signature'}), 401

            # Get raw request body for signature verification
            payload = request.get_data()

            if not webhook_validator.verify_signature(payload, signature):
                logger.error("🚫 WEBHOOK SIGNATURE VERIFICATION FAILED!")
                logger.error("   This webhook may be forged or tampered with")
                return jsonify({'success': False, 'error': 'Invalid signature'}), 401

            logger.debug("✅ Webhook signature verified")
        # ===================================================================

        webhook_data = request.get_json()

        # Log webhook payload for debugging
        logger.debug(f"🔍 Raw webhook data keys: {list(webhook_data.keys()) if webhook_data else 'None'}")
        if webhook_data:
            logger.debug(f"🔍 Webhook structure: {webhook_data}")

        # Log webhook event type
        event_type = webhook_data.get('event', {}).get('type', 'unknown')
        logger.info(f"Event type: {event_type}")

        # Check for messages array
        messages = webhook_data.get('messages', [])
        logger.debug(f"🔍 Messages in webhook: {len(messages)}")

        # Skip status updates
        if event_type == 'statuses':
            logger.info("Status update received (read receipt), skipping")
            return jsonify({'success': True, 'message': 'Status update processed'}), 200

        # Extract message
        message_data = whatsapp_handler.receive_message(webhook_data)

        if not message_data:
            logger.warning("No valid message in webhook")
            return jsonify({'success': True, 'message': 'No message to process'}), 200

        sender = message_data['from']
        user_message = message_data['message']
        message_type = message_data['type']

        logger.info(f"From: {sender}")
        logger.info(f"Type: {message_type}")

        # ===================================================================
        # DUPLICATE MESSAGE DETECTION
        # Prevent processing the same message twice (Whapi sometimes sends duplicates)
        # ===================================================================
        message_id = message_data.get('message_id', '')

        if message_id:
            current_time = time.time()

            # Clean up old message IDs (older than 5 minutes)
            expired_ids = [mid for mid, timestamp in processed_messages.items()
                          if current_time - timestamp > PROCESSED_MESSAGE_TIMEOUT]
            for mid in expired_ids:
                del processed_messages[mid]

            # Check if we've already processed this message
            if message_id in processed_messages:
                logger.warning("="*80)
                logger.warning("⏭️ DUPLICATE MESSAGE DETECTED - SKIPPING")
                logger.warning(f"   Message ID: {message_id}")
                logger.warning(f"   From: {sender}")
                logger.warning(f"   Already processed {current_time - processed_messages[message_id]:.1f}s ago")
                logger.warning("   This prevents duplicate responses")
                logger.warning("="*80)
                return jsonify({'success': True, 'message': 'Duplicate message skipped'}), 200

            # Mark this message as processed
            processed_messages[message_id] = current_time
            logger.info(f"✓ New message (ID: {message_id[:20]}...)")
        else:
            logger.warning("⚠️ No message ID provided - cannot check for duplicates")
        # ===================================================================

        # ===================================================================
        # FILTER: Skip escalation alert messages only
        # Allow managers to use bot normally, but skip processing escalation alerts
        # ===================================================================
        if config.get('escalation.enabled', False):
            # Skip only if message contains escalation alert pattern
            # This allows managers to use bot as normal customers
            if user_message and '🚨 ESCALATION ALERT 🚨' in user_message:
                logger.info("⏭️ Skipping escalation alert message")
                logger.info("This prevents bot from responding to its own escalation notifications")
                return jsonify({'success': True, 'message': 'Escalation alert detected, skipped'}), 200
        # ===================================================================

        # ===================================================================
        # NOTE: Bot's own messages are now filtered in whatsapp_handler.py
        # via the fromMe field (Whapi sends fromMe: true for bot's messages)
        # This is the proper way to filter bot messages at the source
        # ===================================================================
        sender_clean = sender.replace('@s.whatsapp.net', '')

        # ===================================================================
        # ANTI-SPAM CHECK - WhatsApp Messages
        # ===================================================================
        if anti_spam_manager and user_message:
            allowed, reason = anti_spam_manager.check_message(
                user_id=sender_clean,
                message=user_message
            )

            if not allowed:
                logger.warning(f"🚫 WhatsApp message blocked by anti-spam: {reason}")
                # Send warning message to user
                whatsapp_handler.send_message(
                    to=sender,
                    message=f"⚠️ {reason}\n\nPlease slow down and try again shortly."
                )
                return jsonify({'success': True, 'message': 'Spam blocked'}), 200

            logger.debug("✅ Anti-spam check passed")
            # THROTTLE: Check rate limit before making any API calls
            try:
                throttle_if_busy()
            except Exception as e:
                logger.warning(f"Rate limiter check: {e}")
        # ===================================================================

        # Create session ID for WhatsApp user
        session_id = f"whatsapp_{sender}"

        # Initialize conversation if new
        if not conversation_manager.session_exists(session_id):
            logger.info(f"Initializing WhatsApp conversation for: {sender}")

            if config.has_knowledge_base:
                system_prompt = config.get_prompt('whatsapp_with_knowledge')
            else:
                system_prompt = config.get_prompt('whatsapp_without_knowledge')

            # ===================================================================
            # MEMBER STATUS INJECTION - Check if customer is registered member
            # ===================================================================
            if lead_manager and config.get('lead_tracking.enabled', False):
                try:
                    customer_phone_clean = sender.replace('@s.whatsapp.net', '')
                    is_member = lead_manager.check_if_member(customer_phone_clean)

                    if is_member:
                        # Get member details
                        member_info = lead_manager.get_member_info(customer_phone_clean)
                        if member_info:
                            member_context = f"""
===== CUSTOMER MEMBER STATUS =====
✅ REGISTERED MEMBER
Name: {member_info['name']}
Birthday: {member_info['birthday']}
Registration Date: {member_info['registration_date']}
Points Balance: {member_info['points']}
Birthday Benefit Used This Year: {member_info['birthday_benefit_used']}

IMPORTANT: This customer is ALREADY a member!
- If they ask about membership, give SHORT benefits summary (they know the benefits)
- Do NOT send the full registration template
- They can already use member pricing
==================================
"""
                            system_prompt += member_context
                            logger.info(f"✅ Customer is registered member: {member_info['name']}")
                    else:
                        member_context = """
===== CUSTOMER MEMBER STATUS =====
❌ NOT A REGISTERED MEMBER
- This customer's phone is NOT in Members database
- If they ask about membership, send FULL registration template
- Watch for Name + Birthday to register them
==================================
"""
                        system_prompt += member_context
                        logger.info("📭 Customer is not a registered member")
                except Exception as e:
                    logger.error(f"Error checking member status: {e}")
            # ===================================================================

            conversation_manager.create_session(session_id, system_prompt)

        # Process message based on type
        if message_type == 'image' and message_data.get('image'):
            logger.info("Processing image message...")
            image_url = message_data['image']['url']
            image_base64 = whatsapp_handler.download_image(image_url)

            if image_base64:
                mime_type = message_data['image']['mime_type']
                message_content = [
                    {"type": "text", "text": user_message if user_message else "I've sent an image. Can you help?"}
                ]
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}
                })
                conversation_manager.add_message(session_id, 'user', message_content)

        elif message_type in ['voice', 'audio', 'ptt'] and message_data.get('voice'):
            logger.info("Processing voice message...")
            audio_url = message_data['voice']['url']

            # Determine extension from MIME type
            mime_type = message_data['voice']['mime_type']
            ext = 'ogg' if 'ogg' in mime_type else 'mp3' if 'mp3' in mime_type else 'm4a'

            # Download audio
            temp_path = os.path.join('data/uploads', f"whatsapp_voice_{int(time.time())}.{ext}")
            if whatsapp_handler.download_audio(audio_url, temp_path):
                try:
                    voice_result = process_voice(temp_path, ext, ai_engine)
                    transcription = voice_result['transcription']
                    full_message = f"[Voice Message]:\n{transcription}"
                    conversation_manager.add_message(session_id, 'user', full_message)
                except Exception as e:
                    logger.error(f"Voice processing failed: {str(e)}")
                    return jsonify({'success': True}), 200
                finally:
                    try:
                        os.remove(temp_path)
                    except:
                        pass

        else:
            # Text message
            if not user_message.strip():
                logger.warning("Empty message, skipping")
                return jsonify({'success': True}), 200

            conversation_manager.add_message(session_id, 'user', user_message)

        # ===================================================================
        # FOLLOW-UP CAMPAIGNS - Stop active campaigns when lead responds
        # ===================================================================
        if follow_up_manager and config.get('lead_tracking.enabled', False):
            try:
                customer_phone_normalized = sender.replace('@s.whatsapp.net', '')
                logger.info("Checking for active follow-up campaigns...")

                # Stop all active campaigns for this lead (they responded!)
                stopped = follow_up_manager.mark_lead_responded(
                    phone=customer_phone_normalized,
                    response_text=user_message if message_type == 'text' else f"[{message_type} message]"
                )

                if stopped:
                    logger.info(f"✅ Stopped follow-up campaigns for {customer_phone_normalized} (responded)")

            except Exception as e:
                logger.error(f"Error stopping follow-up campaigns: {e}")
        # ===================================================================

        # ===================================================================
        # MEMORY RETRIEVAL - Read customer memory before AI response
        # ===================================================================
        customer_memory = None
        customer_phone_normalized = sender.replace('@s.whatsapp.net', '')

        if lead_manager and config.get('lead_tracking.enabled', False) and config.get('memory.enabled', True):
            try:
                logger.info("Checking for customer memory...")
                customer_memory = lead_manager.get_customer_memory(customer_phone_normalized)

                if customer_memory and customer_memory.get('is_returning'):
                    logger.info("="*80)
                    logger.info("💭 RETURNING CUSTOMER DETECTED")
                    logger.info("="*80)
                    logger.info(f"Name: {customer_memory['name']}")
                    logger.info(f"Total Conversations: {customer_memory['total_conversations']}")
                    logger.info(f"Last Visit: {customer_memory['last_visit']}")
                    logger.info(f"Current Interest: {customer_memory['current_interest']}")
                    logger.info(f"Preferences: {customer_memory.get('preferences', 'None')}")
                    logger.info(f"Conversation History: {len(customer_memory['conversation_history'])} records")
                    logger.info("="*80)
                else:
                    logger.info("🆕 New customer - no previous memory found")

            except Exception as e:
                logger.error(f"Error retrieving customer memory: {e}")
                customer_memory = None
        # ===================================================================

        # Generate AI response WITH FUNCTION CALLING
        logger.info("Generating AI response with function calling enabled...")
        messages = conversation_manager.get_conversation_for_api(session_id)

        # ===================================================================
        # MEMORY INJECTION - Add customer memory to AI context
        # ===================================================================
        if customer_memory and customer_memory.get('is_returning'):
            logger.info("Injecting customer memory into AI context...")

            # Build tiered memory context
            memory_text = build_tiered_memory(customer_memory)

            if memory_text:
                # Insert memory context after system prompt, before conversation
                memory_context = {
                    "role": "system",
                    "content": f"""
CUSTOMER MEMORY CONTEXT:
{memory_text}

INSTRUCTIONS:
- Acknowledge returning customer naturally (e.g., "Welcome back!")
- Reference their previous interests/preferences when relevant
- Provide personalized recommendations based on history
- Don't repeat information they already know
- Be friendly and show you remember them
"""
                }

                # Insert after first message (system prompt)
                messages_with_memory = [messages[0], memory_context] + messages[1:]
                logger.info(f"Memory context added ({len(memory_text)} chars)")
            else:
                messages_with_memory = messages
        else:
            messages_with_memory = messages
        # ===================================================================

        # Define available tools (escalation function + member registration)
        tools = [
            get_escalation_function_definition(),
            get_register_member_function_definition()
        ]

        # Call AI with function calling enabled
        ai_response = ai_engine.generate_response(messages_with_memory, tools=tools, tool_choice="auto")

        if not ai_response['success']:
            logger.error(f"AI response failed: {ai_response['error']}")
            return jsonify({'success': True}), 200

        # Check if AI wants to call escalation function
        tool_calls = ai_response.get('tool_calls')

        if tool_calls:
            logger.info("="*80)
            logger.info("🔧 AI IS CALLING FUNCTION(S)")
            logger.info("="*80)

            # Process function calls
            function_results = []

            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                function_args = json.loads(tool_call['function']['arguments'])

                logger.info(f"Function called: {function_name}")
                logger.debug(f"Arguments: {function_args}")

                if function_name == "escalate_to_human":
                    # Execute escalation
                    escalation_result = handle_escalation_function_call(
                        function_args=function_args,
                        customer_phone=sender,
                        customer_name=message_data.get('from_name', sender),
                        message_id=message_data.get('message_id', ''),
                        platform='whatsapp'
                    )

                    function_results.append({
                        "tool_call_id": tool_call['id'],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(escalation_result)
                    })

                elif function_name == "register_member":
                    # Execute member registration
                    registration_result = handle_register_member_function_call(
                        function_args=function_args,
                        whatsapp_phone=sender
                    )

                    function_results.append({
                        "tool_call_id": tool_call['id'],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(registration_result)
                    })

            # Note: AI called a function, we'll add the final response after execution

            # Add function results to messages for final response
            messages_with_results = messages_with_memory + [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tc['id'],
                            "type": tc['type'],
                            "function": {
                                "name": tc['function']['name'],
                                "arguments": tc['function']['arguments']
                            }
                        } for tc in tool_calls
                    ]
                }
            ] + function_results

            # Get final response from AI after executing function
            logger.info("Getting final response from AI after function execution...")
            final_response = ai_engine.generate_response(messages_with_results)

            if not final_response['success']:
                logger.error(f"Final response failed: {final_response['error']}")
                return jsonify({'success': True}), 200

            assistant_message = final_response['content']

        else:
            # No function call, use AI's text response directly
            assistant_message = ai_response['content']

        # Validate response
        if config.get('features.response_validation', True) and config.has_knowledge_base and assistant_message:
            validation_result = response_validator.validate(assistant_message)
            logger.info(f"Validation: confidence={validation_result['confidence']:.1%}")

        # Add to conversation (if not already added by function calling)
        if not tool_calls:
            conversation_manager.add_message(session_id, 'assistant', assistant_message)
        else:
            # For function calls, add the final response
            conversation_manager.add_message(session_id, 'assistant', assistant_message)

        # ⭐ CHECK FOR MENU IMAGE REQUEST ⭐
        # If customer asks for menu/prices, send menu image before text response
        should_send_menu, menu_image_url, menu_caption, detected_language = should_send_menu_image(user_message, config)

        if should_send_menu and menu_image_url:
            logger.info(f"📸 Menu image request detected ({detected_language})")
            logger.info(f"   Sending menu image: {menu_image_url[:60]}...")
            menu_result = whatsapp_handler.send_image(sender, menu_image_url, menu_caption)
            if menu_result['success']:
                logger.info(f"   ✅ Menu image sent successfully (Message ID: {menu_result.get('message_id', 'N/A')})")
            else:
                logger.warning(f"   ⚠️  Failed to send menu image: {menu_result.get('error', 'Unknown error')}")

        # Send response via WhatsApp
        logger.info("Sending response to WhatsApp...")
        send_result = whatsapp_handler.send_message(sender, assistant_message)

        if send_result['success']:
            logger.info("✅ WhatsApp message sent successfully")

            # ⭐ AUTOMATIC LEAD TRACKING & MEMORY UPDATE ⭐
            # Record customer data to Google Sheets and save conversation history
            if lead_manager and config.get('lead_tracking.enabled', False):
                try:
                    # Get conversation history
                    messages = conversation_manager.get_conversation_for_api(session_id)

                    # Check if we have enough messages to record (avoid spam)
                    min_messages = config.get('lead_tracking.auto_record_after_messages', 3)

                    if len(messages) >= min_messages:
                        logger.info("="*80)
                        logger.info("📊 AUTOMATIC LEAD TRACKING & MEMORY UPDATE")
                        logger.info("="*80)

                        # Extract customer information
                        customer_name = message_data.get('from_name', 'Unknown')
                        customer_phone = sender.replace('@s.whatsapp.net', '')

                        logger.info(f"Customer: {customer_name} ({customer_phone})")

                        # Use AI to analyze conversation and extract interest
                        lead_info = {}
                        if config.get('lead_tracking.use_ai_analysis', True):
                            logger.info("Using AI to analyze conversation...")
                            lead_info = lead_manager.extract_lead_info_from_conversation(
                                messages=messages,
                                customer_phone=customer_phone,
                                ai_engine=ai_engine
                            )

                        current_interest = lead_info.get('current_interest', 'Initial contact')

                        # Record to Google Sheets (Customer Record sheet)
                        logger.info(f"Recording lead with interest: {current_interest}")
                        result = lead_manager.record_lead(
                            customer_phone=customer_phone,
                            customer_name=customer_name if customer_name != 'Unknown' else None,
                            current_interest=current_interest
                        )

                        if result['success']:
                            logger.info(f"✅ Lead {result['action']} successfully (Row {result['row']})")
                            logger.info(f"   Name: {customer_name}")
                            logger.info(f"   Phone: {customer_phone}")
                            logger.info(f"   Interest: {current_interest}")
                        else:
                            logger.error(f"❌ Failed to record lead: {result['message']}")

                        # ====================================================
                        # MEMORY UPDATE - Save conversation to history sheet
                        # ====================================================
                        if config.get('memory.enabled', True):
                            logger.info("Updating customer memory...")

                            # Generate conversation summary using AI
                            try:
                                if config.get('memory.save_conversation_summary', True):
                                    # Extract ONLY customer messages (filter out agent responses)
                                    customer_messages = [
                                        msg.get('content', '')[:200]
                                        for msg in messages[-10:]
                                        if msg.get('role') == 'user' and isinstance(msg.get('content'), str)
                                    ]

                                    customer_text = "\n".join([f"- {msg}" for msg in customer_messages if msg.strip()])

                                    summary_prompt = f"""Summarize what the customer asked about or wanted based on their messages only.

Customer's messages:
{customer_text}

Create a brief summary (maximum 15 words) of what the customer wanted.
Format: "Customer asked about X" or "Customer wanted Y"
Do NOT mention the agent, business name, or any responses.

Examples:
- "Customer asked about operating hours and foot massage pricing"
- "Customer inquired about female therapist availability"
- "Customer wanted weekend appointment"

Summary:"""

                                    summary_response = ai_engine.generate_response(
                                        [{"role": "user", "content": summary_prompt}],
                                        temperature=0.3,
                                        max_tokens=100
                                    )

                                    conversation_summary = summary_response['content'].strip() if summary_response.get('success') else "Conversation about services"

                                    logger.info(f"Summary: {conversation_summary}")

                                    # Save to Conversation History sheet
                                    history_saved = lead_manager.add_conversation_to_history(
                                        phone=customer_phone,
                                        conversation_summary=conversation_summary,
                                        category=current_interest,
                                        confidence="High"
                                    )

                                    if history_saved:
                                        logger.info("✅ Conversation saved to history sheet")
                                    else:
                                        logger.warning("⚠️ Failed to save conversation to history")

                                # Extract and update preferences
                                if config.get('memory.extract_preferences', True):
                                    logger.info("Extracting customer preferences...")
                                    preferences = lead_manager.extract_preferences(messages, ai_engine)

                                    if preferences and preferences != "None":
                                        logger.info(f"Preferences found: {preferences}")

                                        # Update preferences in Customer Record sheet
                                        if customer_memory:
                                            row_num = customer_memory['row']
                                            lead_manager.customer_sheet.update_cell(row_num, lead_manager.columns['preferences'], preferences)
                                            logger.info("✅ Preferences updated in Customer Record")

                                # Increment conversation count
                                if customer_memory:
                                    new_count = customer_memory['total_conversations'] + 1
                                    row_num = customer_memory['row']
                                    lead_manager.customer_sheet.update_cell(row_num, lead_manager.columns['total_conversations'], new_count)
                                    logger.info(f"✅ Conversation count updated: {new_count}")

                            except Exception as e:
                                logger.error(f"⚠️ Error updating memory: {e}")
                                logger.exception("Memory update error:")
                        # ====================================================

                        logger.info("="*80)

                    else:
                        logger.info(f"⏭️ Skipping lead recording - only {len(messages)} messages (need {min_messages}+)")

                except Exception as e:
                    logger.error(f"❌ Lead tracking error: {e}")
                    logger.exception("Lead tracking traceback:")
                    # Don't crash the webhook if lead tracking fails

        else:
            logger.error(f"❌ Failed to send WhatsApp message: {send_result['error']}")

        elapsed_time = time.time() - start_time
        logger.info(f"✅ Webhook processed in {elapsed_time:.2f}s")
        logger.info("="*80)

        return jsonify({'success': True}), 200

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ Webhook processing failed after {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        logger.error("="*80)

        return jsonify({'success': True, 'error': str(e)}), 200


# ============================================================================
# ROUTES - API ENDPOINTS
# ============================================================================

@app.route('/api/track-outbound', methods=['POST'])
def track_outbound_call():
    """
    API endpoint for MacroDroid to notify when it sends an auto-message
    Records the lead immediately, even if customer doesn't respond

    Expected JSON payload:
    {
        "phone": "+60123456789",
        "name": "John Doe" (optional),
        "call_time": "2025-11-14T10:30:00" (optional),
        "message": "Your prefilled message" (optional)
    }
    """
    logger.info("="*80)
    logger.info("📞 OUTBOUND MESSAGE TRACKING (MacroDroid)")
    logger.info("="*80)

    try:
        data = request.get_json()

        if not data:
            logger.error("❌ No JSON data received")
            return jsonify({
                'success': False,
                'error': 'No JSON data in request body'
            }), 400

        # Extract data from MacroDroid
        caller_phone = data.get('phone')  # Required
        caller_name = data.get('name', 'Unknown')  # Optional
        call_time = data.get('call_time')  # Optional
        message_sent = data.get('message')  # Optional (the prefilled message)

        if not caller_phone:
            logger.error("❌ Missing phone number")
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400

        logger.info(f"📋 Received Data:")
        logger.info(f"   Caller Phone: {caller_phone}")
        logger.info(f"   Caller Name: {caller_name}")
        logger.info(f"   Call Time: {call_time if call_time else 'Not provided'}")
        logger.info(f"   Message: {message_sent[:50] + '...' if message_sent and len(message_sent) > 50 else message_sent if message_sent else 'Not provided'}")

        # Normalize phone number (remove WhatsApp suffix if present)
        normalized_phone = caller_phone.replace('@s.whatsapp.net', '').replace('+', '').replace('-', '').replace(' ', '')

        # ⭐ AUTO-FETCH WHATSAPP NAME if caller name is Unknown/empty
        if not caller_name or caller_name.strip() in ['Unknown', '']:
            logger.info("🔍 Caller name is Unknown - attempting to fetch from WhatsApp...")

            if whatsapp_handler:
                try:
                    contact_info = whatsapp_handler.get_contact_info(normalized_phone)

                    if contact_info:
                        # Try to get the best available name
                        fetched_name = contact_info.get('name') or contact_info.get('pushName')

                        if fetched_name and fetched_name != normalized_phone:
                            caller_name = fetched_name
                            logger.info(f"✅ WhatsApp name fetched: {caller_name}")
                        else:
                            logger.info("⚠️ No name available in WhatsApp profile")
                            caller_name = "Unknown"
                    else:
                        logger.info("⚠️ Could not fetch WhatsApp profile")
                        caller_name = "Unknown"

                except Exception as e:
                    logger.error(f"❌ Error fetching WhatsApp name: {e}")
                    caller_name = "Unknown"
            else:
                logger.warning("⚠️ WhatsApp handler not initialized")
                caller_name = "Unknown"
        else:
            logger.info(f"✓ Caller name provided: {caller_name}")

        # Check if lead tracking is enabled
        if not lead_manager:
            logger.warning("⚠️ Lead Manager not initialized")
            return jsonify({
                'success': False,
                'error': 'Lead tracking not enabled'
            }), 503

        # Check if lead already exists
        existing_lead = lead_manager.get_lead_by_phone(normalized_phone)

        if existing_lead:
            logger.info(f"♻️ Existing lead found (Row {existing_lead['row']})")
            logger.info("   Updating last contact time...")

            # Update existing lead
            result = lead_manager.record_lead(
                customer_phone=normalized_phone,
                customer_name=caller_name if caller_name and caller_name != 'Unknown' else None,
                current_interest="Phone call - sent auto-response (no reply yet)"
            )
        else:
            logger.info("✨ New lead - creating record...")

            # Create NEW lead
            result = lead_manager.record_lead(
                customer_phone=normalized_phone,
                customer_name=caller_name if caller_name else None,
                current_interest="Phone call - sent auto-response (no reply yet)"
            )

        if result['success']:
            logger.info(f"✅ Lead {result['action']} successfully")
            logger.info(f"   Row: {result['row']}")
            logger.info(f"   Name: {caller_name}")
            logger.info(f"   Phone: {normalized_phone}")
            logger.info("="*80)

            return jsonify({
                'success': True,
                'message': f'Lead {result["action"]} successfully',
                'row': result['row'],
                'action': result['action']
            }), 200
        else:
            logger.error(f"❌ Failed to record lead: {result['message']}")
            logger.error("="*80)
            return jsonify({
                'success': False,
                'error': result['message']
            }), 500

    except Exception as e:
        logger.error(f"❌ Error tracking outbound call: {e}")
        logger.exception("Full traceback:")
        logger.error("="*80)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ROUTES - HEALTH & DIAGNOSTICS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with diagnostic information"""
    logger.debug("Health check requested")

    health_data = {
        'status': 'running',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'agent': {
            'name': config.get('agent.name', 'Unknown'),
            'role': config.get('agent.role', 'Unknown')
        },
        'ai': {
            'model': config.get('ai.model', 'Unknown')
        },
        'knowledge_base': {
            'loaded': config.has_knowledge_base,
            'size_chars': len(config.knowledge_base) if config.has_knowledge_base else 0
        },
        'conversations': conversation_manager.get_stats(),
        'platforms': {
            'web': True,
            'whatsapp': whatsapp_handler is not None
        }
    }

    if not config.has_knowledge_base:
        health_data['status'] = 'degraded'
        health_data['warning'] = 'Knowledge base not loaded'

    return jsonify(health_data)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    host = config.get('platforms.web.host', '0.0.0.0')
    port = config.get('platforms.web.port', 5000)

    logger.info("="*80)
    logger.info(f"STARTING FLASK SERVER")
    logger.info("="*80)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Agent: {config.get('agent.name', 'Unknown')}")
    logger.info(f"Knowledge Base: {'✅ Loaded' if config.has_knowledge_base else '❌ Not Loaded'}")
    logger.info("="*80)

    app.run(debug=True, host=host, port=port)
