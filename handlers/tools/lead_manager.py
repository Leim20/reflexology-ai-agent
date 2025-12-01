"""
Lead Manager Tool
Automatically tracks customer leads and stores in Google Sheets
Handles automatic categorization and data organization
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
from utils.logger import get_logger
from utils.cache_manager import CacheManager
from utils.rate_limiter import wait_with_backoff, should_retry, sleep_with_backoff, throttle_if_busy, track_api_call
import time

logger = get_logger(__name__)


class LeadManager:
    """
    Manages customer leads and Google Sheets integration
    Automatically categorizes and organizes lead data
    """

    def __init__(self, credentials_file: str, spreadsheet_name: str):
        """
        Initialize Lead Manager with Google Sheets connection

        Args:
            credentials_file: Path to Google service account JSON
            spreadsheet_name: Name of Google Sheet to use
        """
        logger.info("🔧 Initializing Lead Manager...")

        # Define Google Sheets API scope
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]

        try:
            # Authenticate using service account
            logger.info(f"📝 Loading credentials from: {credentials_file}")
            credentials = Credentials.from_service_account_file(
                credentials_file,
                scopes=SCOPES
            )

            # Connect to Google Sheets
            self.gc = gspread.authorize(credentials)

            # Open spreadsheet (try by name first, then by URL if it fails)
            logger.info(f"📊 Opening spreadsheet: {spreadsheet_name}")

            try:
                # Try opening by name first
                self.spreadsheet = self.gc.open(spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                # If name doesn't work, try as URL or ID
                logger.info(f"   Name not found, trying as URL/ID...")
                if 'docs.google.com/spreadsheets/d/' in spreadsheet_name:
                    # It's a full URL
                    self.spreadsheet = self.gc.open_by_url(spreadsheet_name)
                else:
                    # Assume it's an ID
                    self.spreadsheet = self.gc.open_by_key(spreadsheet_name)

            # Access THREE sheets
            self.customer_sheet = self.spreadsheet.worksheet("Customer Record")
            self.history_sheet = self.spreadsheet.worksheet("Conversation History")

            # NEW: Members sheet for member registration tracking
            try:
                self.members_sheet = self.spreadsheet.worksheet("Members")
                logger.info("✓ Members sheet found")
            except gspread.WorksheetNotFound:
                logger.warning("⚠️ Members sheet not found - member functions will not work")
                logger.warning("   Run scripts/setup_members_sheet.py to create it")
                self.members_sheet = None

            # Keep reference to main sheet for backward compatibility
            self.sheet = self.customer_sheet

            # ⭐ AUTOMATIC CATEGORIZATION: Column Mapping for Customer Record
            self.columns = {
                'name': 1,                  # Column A - Customer Name
                'phone': 2,                 # Column B - Phone Number
                'interest': 3,              # Column C - Current Interest
                'last_visit': 4,            # Column D - Last Visit Date
                'preferences': 5,           # Column E - Preferences
                'total_conversations': 6,   # Column F - Total Conversations
                'last_updated': 7           # Column G - Last Updated
            }

            # Column Mapping for Conversation History sheet
            self.history_columns = {
                'phone': 1,         # Column A - Phone Number
                'date': 2,          # Column B - Date
                'summary': 3,       # Column C - Conversation Summary
                'category': 4,      # Column D - Interest Category
                'confidence': 5     # Column E - AI Confidence
            }

            # Column Mapping for Members sheet
            self.members_columns = {
                'phone': 1,                         # Column A - Phone Number
                'name': 2,                          # Column B - Name
                'birthday': 3,                      # Column C - Birthday (YYYY-MM-DD)
                'registration_date': 4,             # Column D - Registration Date
                'points': 5,                        # Column E - Loyalty Points
                'birthday_benefit_used': 6          # Column F - Birthday Benefit Used This Year
            }

            logger.info("✅ Lead Manager initialized successfully!")
            logger.info(f"   Spreadsheet: {spreadsheet_name}")
            logger.info(f"   Customer Sheet: {self.customer_sheet.title}")
            logger.info(f"   History Sheet: {self.history_sheet.title}")
            if self.members_sheet:
                logger.info(f"   Members Sheet: {self.members_sheet.title}")
            logger.info(f"   Column Mapping: Name→A, Phone→B, Interest→C, LastVisit→D, Preferences→E, TotalConvs→F, LastUpdated→G")

            # Initialize cache manager for reducing API calls
            logger.info("=" * 80)
            logger.info("Initializing CACHE MANAGER for Lead Manager...")
            self.cache_manager = CacheManager(default_ttl=60)  # 60 second cache
            logger.info("   Cache TTL: 60 seconds (customer data)")
            logger.info("   Cache will reduce Google Sheets API calls by 80-90%")
            logger.info("CACHE MANAGER initialized successfully")
            logger.info("=" * 80)

        except FileNotFoundError:
            logger.error(f"❌ Credentials file not found: {credentials_file}")
            raise
        except gspread.SpreadsheetNotFound:
            logger.error(f"❌ Spreadsheet not found: {spreadsheet_name}")
            logger.error("   Make sure you've shared the sheet with the service account email!")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Lead Manager: {e}")
            raise


    def _retry_on_quota(self, func, max_attempts=3):
        """
        Retry an API call with exponential backoff on 429 quota errors.
        
        Args:
            func: Callable that makes the API call
            max_attempts: Maximum number of retry attempts
            
        Returns:
            Result of the API call
            
        Raises:
            APIError: If all attempts fail
        """
        from gspread.exceptions import APIError
        import time
        
        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except APIError as e:
                if "[429]" in str(e):
                    if attempt < max_attempts:
                        wait_time = 2 ** (attempt - 1)  # 1s, 2s, 4s exponential backoff
                        logger.warning(f"[Quota 429] Attempt {attempt}/{max_attempts} failed. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"[Quota 429] All {max_attempts} attempts failed. Raising error.")
                        raise
                else:
                    # Not a quota error, raise immediately
                    raise

    def record_lead(
        self,
        customer_phone: str,
        customer_name: Optional[str] = None,
        current_interest: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ⭐ AUTOMATIC DATA PLACEMENT
        Record or update lead in Google Sheets
        Automatically places data in correct columns

        Args:
            customer_phone: Customer's phone number (required)
            customer_name: Customer's name (optional)
            current_interest: What customer is interested in (optional)

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'row': int,
                'action': 'created' | 'updated' | 'failed'
            }
        """
        logger.info(f"📝 Recording lead for phone: {customer_phone}")

        try:
            # Check if lead already exists (prevent duplicates)
            existing_lead = self.get_lead_by_phone(customer_phone)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if existing_lead:
                # UPDATE existing lead
                row_num = existing_lead['row']
                logger.info(f"♻️ Updating existing lead at row {row_num}")

                # Batch update fields (Fix #1: single API call instead of 4)
                from gspread import Cell
                cells_to_update = []

                if customer_name:
                    logger.info(f"   Updating name: {customer_name}")
                    cells_to_update.append(Cell(row_num, self.columns['name'], customer_name))

                if current_interest:
                    logger.info(f"   Updating interest: {current_interest}")
                    cells_to_update.append(Cell(row_num, self.columns['interest'], current_interest))

                # Always update last visit and last updated
                cells_to_update.append(Cell(row_num, self.columns['last_visit'], datetime.now().strftime("%Y-%m-%d")))
                cells_to_update.append(Cell(row_num, self.columns['last_updated'], timestamp))

                # Batch update all fields in single API call
                if cells_to_update:
                    throttle_if_busy()
                    self.sheet.update_cells(cells_to_update)
                    logger.info(f"   Batch updated {len(cells_to_update)} fields (1 API call)")
                    track_api_call()

                logger.info(f"✅ Lead updated successfully at row {row_num}")
                
                # CACHE INVALIDATION: Clear cache for this phone since data changed
                cache_key = f"lead_by_phone:{customer_phone}"
                self.cache_manager.invalidate(cache_key)
                self.cache_manager.invalidate("all_leads")
                logger.info("   Cache invalidated for updated lead (phone-specific and all-leads cache)")
                
                return {
                    'success': True,
                    'message': 'Lead updated successfully',
                    'row': row_num,
                    'action': 'updated'
                }

            else:
                # INSERT new lead
                logger.info("✨ Creating new lead entry")

                # ⭐ AUTOMATIC COLUMN MAPPING
                # Data automatically goes to correct columns (A-G)
                new_row = [
                    customer_name or 'Unknown',                # Column A - Name
                    customer_phone,                             # Column B - Phone
                    current_interest or 'Initial Contact',     # Column C - Interest
                    datetime.now().strftime("%Y-%m-%d"),       # Column D - Last Visit Date
                    '',                                         # Column E - Preferences (empty for new)
                    0,                                          # Column F - Total Conversations
                    timestamp                                   # Column G - Last Updated
                ]

                logger.info(f"   Name: {new_row[0]}")
                logger.info(f"   Phone: {new_row[1]}")
                logger.info(f"   Interest: {new_row[2]}")

                # Append to Google Sheet
                throttle_if_busy()
                self.sheet.append_row(new_row)
                track_api_call()

                # Get row number (header is row 1, so data starts at row 2)
                throttle_if_busy()
                row_num = len(self.sheet.get_all_values())

                track_api_call()
                logger.info(f"✅ New lead created at row {row_num}")
                
                # CACHE INVALIDATION: Clear cache since new lead was added
                cache_key = f"lead_by_phone:{customer_phone}"
                self.cache_manager.invalidate(cache_key)
                self.cache_manager.invalidate("all_leads")
                logger.info("   Cache invalidated for new lead (all-leads cache cleared)")
                
                return {
                    'success': True,
                    'message': 'New lead created successfully',
                    'row': row_num,
                    'action': 'created'
                }

        except Exception as e:
            logger.error(f"❌ Failed to record lead: {e}")
            return {
                'success': False,
                'message': str(e),
                'action': 'failed'
            }


    def get_lead_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Find existing lead by phone number (prevents duplicates)
        NOW WITH CACHING to reduce API calls

        Args:
            phone: Phone number to search for

        Returns:
            dict with lead data if found, None if not found
        """
        import time
        start_time = time.time()
        
        logger.info(f"🔍 Searching for existing lead: {phone}")
        
        # CACHE CHECK: Try to get from cache first
        cache_key = f"lead_by_phone:{phone}"
        cached_result = self.cache_manager.get(cache_key)
        
        if cached_result is not None:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"CACHE HIT: Lead data served from cache | elapsed={elapsed_ms:.2f}ms | phone={phone}")
            logger.info(f"   API call SAVED! Using cached data instead of querying Google Sheets")
            return cached_result
        
        logger.info(f"CACHE MISS: Fetching from Google Sheets | phone={phone}")
        api_start_time = time.time()

        try:
            # Get all phone numbers from column B
            throttle_if_busy()
            phone_column = self.sheet.col_values(self.columns['phone'])
            track_api_call()

            # Normalize phone for comparison (remove spaces, dashes, plus signs)
            normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '')

            # Search for matching phone
            for idx, cell_phone in enumerate(phone_column):
                if not cell_phone:
                    continue

                # Skip header row
                if idx == 0:
                    continue

                # Normalize cell phone for comparison
                normalized_cell = cell_phone.replace('+', '').replace('-', '').replace(' ', '')

                if normalized_cell == normalized_phone:
                    row_num = idx + 1  # Sheets are 1-indexed
                    logger.info(f"✅ Found existing lead at row {row_num}")

                    # Get entire row data
                    throttle_if_busy()
                    row_data = self.sheet.row_values(row_num)
                    track_api_call()

                    return {
                        'row': row_num,
                        'name': row_data[0] if len(row_data) > 0 else '',
                        'phone': row_data[1] if len(row_data) > 1 else '',
                        'interest': row_data[2] if len(row_data) > 2 else ''
                    }

            logger.info("📭 No existing lead found")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to search for lead: {e}")
            return None


    def extract_lead_info_from_conversation(
        self,
        messages: List[Dict[str, Any]],
        customer_phone: str,
        ai_engine
    ) -> Dict[str, Any]:
        """
        ⭐ SMART CATEGORIZATION
        Use AI to analyze conversation and extract customer interests
        Automatically categorizes the type of interest

        Args:
            messages: Conversation history
            customer_phone: Customer's phone number
            ai_engine: AI engine instance for analysis

        Returns:
            dict: {
                'current_interest': str,  # AI-categorized interest
                'confidence': str         # High/Medium/Low
            }
        """
        logger.info("🤖 Extracting lead info using AI analysis...")

        # Create analysis prompt for AI
        analysis_prompt = """Analyze this conversation and extract the customer's PRIMARY interest.

Conversation:
{conversation}

Categorize the customer's interest into ONE of these categories:
1. "Booking - [service type and duration]" - Customer wants to book (e.g., "Booking - foot massage 45min")
2. "Pricing inquiry - [service]" - Just asking about prices (e.g., "Pricing inquiry - body massage")
3. "Membership inquiry" - Asking about membership benefits
4. "Service question - [topic]" - General questions about services (e.g., "Service question - difference between foot and body")
5. "Complaint - [issue]" - Customer complaint or feedback issue
6. "Special request - [request]" - Special discounts, group bookings, etc.
7. "Initial contact" - Just greeting or very brief chat

Focus on the LATEST and MOST IMPORTANT intent. If customer asked multiple things, prioritize booking > special request > membership > pricing.

Respond with ONLY the category string, nothing else.

Examples:
- Customer asks price then books → "Booking - body massage 90min"
- Customer only asks price → "Pricing inquiry - foot massage"
- Customer asks about membership → "Membership inquiry"
"""

        # Format conversation (last 10 messages for context)
        conversation_text = ""
        for msg in messages[-10:]:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if isinstance(content, str) and content.strip():
                speaker = "Customer" if role == "user" else "Jessica"
                conversation_text += f"{speaker}: {content}\n"

        # Call AI for analysis
        analysis_messages = [
            {
                "role": "system",
                "content": "You are a CRM assistant analyzing customer conversations. Be precise and concise."
            },
            {
                "role": "user",
                "content": analysis_prompt.format(conversation=conversation_text)
            }
        ]

        try:
            logger.info("   Calling AI for conversation analysis...")
            response = ai_engine.generate_response(
                analysis_messages,
                temperature=0.3,  # Lower temperature = more factual/consistent
                max_tokens=100
            )

            if response.get('success'):
                interest = response.get('content', '').strip()
                logger.info(f"✅ AI categorized interest as: {interest}")

                return {
                    'current_interest': interest,
                    'confidence': 'High'
                }
            else:
                logger.error(f"❌ AI analysis failed: {response.get('error')}")
                return {
                    'current_interest': 'Initial contact',
                    'confidence': 'Low'
                }

        except Exception as e:
            logger.error(f"❌ Failed to extract lead info: {e}")
            return {
                'current_interest': 'Initial contact',
                'confidence': 'Low'
            }


    def get_conversation_history(
        self,
        phone: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get last 20 conversations for a specific customer from history sheet
        Filters mixed data to return ONLY this customer's conversations
        ⭐ WITH CACHING: Reduces API calls from 21+ to 1 (after cache hit)

        Args:
            phone: Customer phone number
            limit: Number of conversations to retrieve (default 20)

        Returns:
            list of conversation dictionaries, most recent last
        """
        logger.info(f"🔍 Getting conversation history for: {phone} (last {limit})")

        try:
            # Normalize phone
            normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('@s.whatsapp.net', '')

            # ⭐ CACHE CHECK: Look for cached conversation history
            cache_key = f"conversation_history:{normalized_phone}"
            cached_history = self.cache_manager.get(cache_key)
            if cached_history is not None:
                logger.info(f"   CACHE HIT: Conversation history served from cache | phone={normalized_phone}")
                # Return last N conversations from cache
                recent = cached_history[-limit:] if len(cached_history) > limit else cached_history
                logger.info(f"   ✅ Found {len(recent)} conversations from cache (total cached: {len(cached_history)})")
                return recent

            # ⭐ CACHE MISS: Fetch from API
            logger.info(f"   CACHE MISS: Fetching from Google Sheets API...")

            # Find all rows with this phone number (filters mixed data!)
            throttle_if_busy()
            matching_cells = self.history_sheet.findall(normalized_phone)
            track_api_call()

            if not matching_cells:
                logger.info(f"   No conversation history found for {phone}")
                # Cache empty result to avoid repeated searches
                self.cache_manager.set(cache_key, [], ttl=300)  # Cache for 5 minutes
                return []

            # Extract conversation data from matching rows
            conversations = []
            for cell in matching_cells:
                row_num = cell.row
                throttle_if_busy()
                row_data = self.history_sheet.row_values(row_num)
                track_api_call()

                # Skip header row
                if row_num == 1:
                    continue

                conversations.append({
                    'phone': row_data[0] if len(row_data) > 0 else '',
                    'date': row_data[1] if len(row_data) > 1 else '',
                    'summary': row_data[2] if len(row_data) > 2 else '',
                    'category': row_data[3] if len(row_data) > 3 else '',
                    'confidence': row_data[4] if len(row_data) > 4 else '',
                    'row': row_num
                })

            # Sort by date (most recent last)
            conversations.sort(key=lambda x: x['date'])

            # ⭐ CACHE STORE: Store full history in cache for future requests
            self.cache_manager.set(cache_key, conversations, ttl=300)  # Cache for 5 minutes
            logger.info(f"   📝 Cached {len(conversations)} conversations for {normalized_phone}")

            # Get last N conversations
            recent_conversations = conversations[-limit:] if len(conversations) > limit else conversations

            logger.info(f"   ✅ Found {len(recent_conversations)} conversations from API (total: {len(conversations)})")

            return recent_conversations

        except Exception as e:
            logger.error(f"❌ Failed to get conversation history: {e}")
            return []


    def add_conversation_to_history(
        self,
        phone: str,
        conversation_summary: str,
        category: str = "General",
        confidence: str = "High"
    ) -> bool:
        """
        Add new conversation to history sheet
        Appends as new row (mixed with other customers)
        ⭐ WITH CACHE INVALIDATION: Clears cached history for this customer

        Args:
            phone: Customer phone number
            conversation_summary: Brief summary of conversation
            category: Interest category
            confidence: AI confidence level

        Returns:
            bool: Success
        """
        logger.info(f"💾 Adding conversation to history for: {phone}")

        try:
            # Normalize phone
            normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('@s.whatsapp.net', '')

            # Current date
            date = datetime.now().strftime("%Y-%m-%d")

            # Create new row
            new_row = [
                normalized_phone,           # Column A - Phone
                date,                       # Column B - Date
                conversation_summary,       # Column C - Summary
                category,                   # Column D - Category
                confidence                  # Column E - Confidence
            ]

            # Append to history sheet (mixed with other customers)
            throttle_if_busy()
            self.history_sheet.append_row(new_row)
            track_api_call()

            logger.info(f"   ✅ Conversation added: [{date}] {conversation_summary}")

            # ⭐ CACHE INVALIDATION: Clear cached history for this customer
            # Next call to get_conversation_history() will fetch fresh data from API
            cache_key = f"conversation_history:{normalized_phone}"
            self.cache_manager.delete(cache_key)
            logger.info(f"   📝 Cache invalidated for {normalized_phone}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to add conversation to history: {e}")
            return False


    def get_customer_memory(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get COMPLETE customer memory (main sheet + conversation history)
        This provides full context for AI personalization

        Args:
            phone: Customer phone number

        Returns:
            dict with complete customer memory or None if not found
        """
        logger.info(f"🧠 Retrieving complete memory for: {phone}")

        try:
            # CACHE CHECK
            cache_key = f"customer_memory:{phone}"
            cached_memory = self.cache_manager.get(cache_key)
            if cached_memory is not None:
                logger.info(f"CACHE HIT: Customer memory served from cache | phone={phone}")
                return cached_memory

            # Get basic lead info from main sheet
            lead = self.get_lead_by_phone(phone)

            if not lead:
                logger.info(f"   No memory found - new customer")
                return None

            # Get row data from main sheet
            throttle_if_busy()
            row_data = self.customer_sheet.row_values(lead['row'])
            track_api_call()

            # Get conversation history (last 20)
            conversations = self.get_conversation_history(phone, limit=20)

            # Build complete memory
            memory = {
                'name': row_data[0] if len(row_data) > 0 else '',
                'phone': row_data[1] if len(row_data) > 1 else '',
                'current_interest': row_data[2] if len(row_data) > 2 else '',
                'last_visit': row_data[3] if len(row_data) > 3 else '',
                'preferences': row_data[4] if len(row_data) > 4 else '',
                'total_conversations': int(row_data[5]) if len(row_data) > 5 and row_data[5] else 0,
                'last_updated': row_data[6] if len(row_data) > 6 else '',
                'conversation_history': conversations,  # List of last 20 conversations
                'is_returning': len(conversations) > 0,
                'row': lead['row']
            }

            logger.info(f"   ✅ Memory retrieved: {memory['name']} ({len(conversations)} conversations)")

            # CACHE STORE to avoid repeated rebuilds during a session
            self.cache_manager.set(cache_key, memory, ttl=120)
            return memory

        except Exception as e:
            logger.error(f"❌ Failed to get customer memory: {e}")
            return None


    def extract_preferences(
        self,
        messages: List[Dict],
        ai_engine
    ) -> str:
        """
        Use AI to extract customer preferences from conversation

        Args:
            messages: Conversation history
            ai_engine: AI engine instance

        Returns:
            str: Comma-separated preferences (e.g., "Female therapist, 90min body massage")
        """
        logger.info("🤖 Extracting preferences using AI...")

        # Create prompt for AI
        prompt = """Analyze this conversation and extract customer preferences.

Conversation:
{conversation}

Extract ONLY clear preferences mentioned by customer:
- Service preference (foot/body massage, duration)
- Therapist preference (male/female/specific number)
- Time preference (morning/evening/specific times)
- Any special requests

Format as comma-separated list. If no preferences mentioned, return "None".

Example: "Female therapist, 90min body massage, evening slots"
"""

        # Format conversation (last 10 messages)
        conversation_text = ""
        for msg in messages[-10:]:
            role = msg.get('role')
            content = msg.get('content', '')
            if isinstance(content, str) and content.strip():
                speaker = "Customer" if role == "user" else "Agent"
                conversation_text += f"{speaker}: {content}\n"

        # Call AI
        analysis_messages = [{
            "role": "user",
            "content": prompt.format(conversation=conversation_text)
        }]

        try:
            response = ai_engine.generate_response(
                analysis_messages,
                temperature=0.3,
                max_tokens=100
            )

            if response.get('success'):
                preferences = response['content'].strip()
                logger.info(f"   ✅ Preferences extracted: {preferences}")
                return preferences
            else:
                logger.error(f"   ❌ AI extraction failed")
                return "None"

        except Exception as e:
            logger.error(f"❌ Failed to extract preferences: {e}")
            return "None"


    def get_all_leads(self) -> List[Dict[str, Any]]:
        """
        Get all leads from Google Sheet
        NOW WITH CACHING to reduce API calls

        Returns:
            list of lead dictionaries
        """
        import time
        start_time = time.time()
        
        logger.info("📋 Fetching all leads...")
        
        # CACHE CHECK: This is heavily called by follow-up manager every minute
        cache_key = "all_leads"
        cached_result = self.cache_manager.get(cache_key)
        
        if cached_result is not None:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"CACHE HIT: All leads served from cache | count={len(cached_result)} | elapsed={elapsed_ms:.2f}ms")
            logger.info(f"   API call SAVED! This saves significant time for {len(cached_result)} leads")
            return cached_result
        
        logger.info("CACHE MISS: Fetching all leads from Google Sheets...")
        api_start_time = time.time()

        try:
            throttle_if_busy()
            all_records = self.sheet.get_all_records()
            track_api_call()
            
            # CACHE STORE: Cache for 2 minutes (follow-up manager checks every minute)
            api_elapsed_ms = (time.time() - api_start_time) * 1000
            self.cache_manager.set(cache_key, all_records, ttl=120)
            total_elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Retrieved {len(all_records)} leads")
            logger.info(f"All leads cached | api_time={api_elapsed_ms:.2f}ms | total_time={total_elapsed_ms:.2f}ms | ttl=120s")
            logger.info(f"   Next {len(all_records)} lead queries will be instant for 2 minutes")
            
            return all_records
        except Exception as e:
            logger.error(f"❌ Failed to fetch leads: {e}")
            return []


    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about leads

        Returns:
            dict with lead statistics
        """
        logger.info("📊 Calculating lead statistics...")

        try:
            throttle_if_busy()
            all_data = self.sheet.get_all_values()
            track_api_call()

            # Skip header row
            data_rows = all_data[1:] if len(all_data) > 1 else []

            total_leads = len(data_rows)

            # Count interest categories
            interests = {}
            for row in data_rows:
                if len(row) > 2:
                    interest = row[2]
                    interests[interest] = interests.get(interest, 0) + 1

            stats = {
                'total_leads': total_leads,
                'interests': interests
            }

            logger.info(f"✅ Stats: {total_leads} total leads")
            return stats

        except Exception as e:
            logger.error(f"❌ Failed to calculate stats: {e}")
            return {'total_leads': 0, 'interests': {}}


    # ========================================================================
    # MEMBER MANAGEMENT FUNCTIONS
    # ========================================================================

    def check_if_member(self, phone: str) -> bool:
        """
        Check if a customer is a registered member

        Args:
            phone: Customer phone number

        Returns:
            bool: True if member exists, False otherwise
        """
        logger.info(f"🔍 Checking if {phone} is a member...")

        if not self.members_sheet:
            logger.error("❌ Members sheet not initialized")
            return False

        try:
            # Normalize phone number
            normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('@s.whatsapp.net', '')

            # Search for phone in Members sheet (Column A)
            throttle_if_busy()
            phone_column = self.members_sheet.col_values(self.members_columns['phone'])
            track_api_call()

            for idx, cell_phone in enumerate(phone_column):
                # Skip header row
                if idx == 0:
                    continue

                if not cell_phone:
                    continue

                # Normalize cell phone
                normalized_cell = cell_phone.replace('+', '').replace('-', '').replace(' ', '')

                if normalized_cell == normalized_phone:
                    logger.info(f"✅ Member found at row {idx + 1}")
                    return True

            logger.info(f"📭 Not a member")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to check member status: {e}")
            return False


    def get_member_info(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get member information from Members sheet

        Args:
            phone: Customer phone number

        Returns:
            dict or None: Member information if found, None otherwise
            {
                'phone': str,
                'name': str,
                'birthday': str,
                'registration_date': str,
                'points': int,
                'birthday_benefit_used': str,
                'row': int
            }
        """
        logger.info(f"🔍 Getting member info for: {phone}")

        if not self.members_sheet:
            logger.error("❌ Members sheet not initialized")
            return None

        try:
            # Normalize phone number
            normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('@s.whatsapp.net', '')

            # Search for phone in Members sheet
            phone_column = self.members_sheet.col_values(self.members_columns['phone'])

            for idx, cell_phone in enumerate(phone_column):
                # Skip header row
                if idx == 0:
                    continue

                if not cell_phone:
                    continue

                # Normalize cell phone
                normalized_cell = cell_phone.replace('+', '').replace('-', '').replace(' ', '')

                if normalized_cell == normalized_phone:
                    row_num = idx + 1
                    logger.info(f"✅ Member found at row {row_num}")

                    # Get entire row data
                    row_data = self.members_sheet.row_values(row_num)

                    member_info = {
                        'phone': row_data[0] if len(row_data) > 0 else '',
                        'name': row_data[1] if len(row_data) > 1 else '',
                        'birthday': row_data[2] if len(row_data) > 2 else '',
                        'registration_date': row_data[3] if len(row_data) > 3 else '',
                        'points': int(row_data[4]) if len(row_data) > 4 and row_data[4] else 0,
                        'birthday_benefit_used': row_data[5] if len(row_data) > 5 else 'No',
                        'row': row_num
                    }

                    logger.info(f"   Name: {member_info['name']}")
                    logger.info(f"   Birthday: {member_info['birthday']}")
                    logger.info(f"   Points: {member_info['points']}")

                    return member_info

            logger.info("📭 Member not found")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get member info: {e}")
            logger.exception("Full error traceback:")
            return None


    def register_member(
        self,
        phone: str,
        name: str,
        birthday: str
    ) -> Dict[str, Any]:
        """
        Register a new member in Members sheet

        Args:
            phone: Customer phone number
            name: Customer name
            birthday: Birthday in YYYY-MM-DD format

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'action': 'created' | 'updated' | 'already_exists' | 'failed',
                'row': int or None
            }
        """
        logger.info(f"👤 Registering member: {name} ({phone})")

        if not self.members_sheet:
            logger.error("❌ Members sheet not initialized")
            return {
                'success': False,
                'message': 'Members sheet not available',
                'action': 'failed',
                'row': None
            }

        try:
            # Normalize phone number
            normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('@s.whatsapp.net', '')

            # Check if member already exists
            # Handle API quota errors gracefully
            existing_member = None
            try:
                existing_member = self.get_member_info(normalized_phone)
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'Quota exceeded' in error_str:
                    logger.warning(f"⚠️ API quota error when checking existing member, will proceed with registration: {e}")
                    # Continue with registration - better to create duplicate than fail
                else:
                    # For other errors, re-raise
                    raise

            if existing_member:
                # Member already registered
                logger.warning(f"⚠️ Member already exists at row {existing_member['row']}")
                logger.warning(f"   Existing name: {existing_member['name']}")
                logger.warning(f"   Existing birthday: {existing_member['birthday']}")

                # Update name and birthday if provided values are different
                if name != existing_member['name'] or birthday != existing_member['birthday']:
                    logger.info("Updating existing member information...")
                    row_num = existing_member['row']

                    if name and name != existing_member['name']:
                        self.members_sheet.update_cell(row_num, self.members_columns['name'], name)
                        logger.info(f"   Updated name: {name}")

                    if birthday and birthday != existing_member['birthday']:
                        self.members_sheet.update_cell(row_num, self.members_columns['birthday'], birthday)
                        logger.info(f"   Updated birthday: {birthday}")

                    return {
                        'success': True,
                        'message': 'Member information updated',
                        'action': 'updated',
                        'row': row_num
                    }
                else:
                    return {
                        'success': True,
                        'message': 'Member already registered with same information',
                        'action': 'already_exists',
                        'row': existing_member['row']
                    }

            # Register new member
            logger.info("✨ Creating new member registration")

            today = datetime.now().strftime("%Y-%m-%d")

            new_row = [
                normalized_phone,       # Column A - Phone
                name,                   # Column B - Name
                birthday,               # Column C - Birthday (YYYY-MM-DD)
                today,                  # Column D - Registration Date
                0,                      # Column E - Points (start with 0)
                'No'                    # Column F - Birthday Benefit Used This Year
            ]

            logger.info(f"   Phone: {normalized_phone}")
            logger.info(f"   Name: {name}")
            logger.info(f"   Birthday: {birthday}")
            logger.info(f"   Registration Date: {today}")

            # Append to Members sheet
            self.members_sheet.append_row(new_row)

            # Get row number (with error handling)
            row_num = None
            try:
                row_num = len(self.members_sheet.get_all_values())
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'Quota exceeded' in error_str:
                    logger.warning(f"⚠️ API quota error when getting row number, but member was added successfully")
                    # Member was added, so return success even without row number
                else:
                    logger.warning(f"⚠️ Could not get row number: {e}")
                # Continue anyway - member was added

            logger.info(f"✅ Member registered successfully at row {row_num}")

            return {
                'success': True,
                'message': 'Member registered successfully',
                'action': 'created',
                'row': row_num
            }

        except Exception as e:
            logger.error(f"❌ Failed to register member: {e}")
            logger.exception("Full error traceback:")
            return {
                'success': False,
                'message': str(e),
                'action': 'failed',
                'row': None
            }
