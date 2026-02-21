# Lead Manager (Google Sheets Integration)

## Overview

The Lead Manager is the **central Google Sheets integration module** that handles all customer data operations — customer records, bookings, members, conversation history, and analytics. It's the backbone of the CRM functionality.

**Location:** `handlers/tools/lead_manager.py` (~800+ lines)
**Dependencies:** `gspread`, `google-auth`, `utils/cache_manager.py`, `utils/rate_limiter.py`

---

## What is the Purpose?

The Lead Manager exists to:

1. **Store Customer Records** — Track all customers who interact with the bot.

2. **Manage Bookings** — Record, update, and query booking information.

3. **Track Members** — Handle member registration and loyalty points.

4. **Log Conversations** — Store conversation summaries and insights.

5. **Enable Follow-ups** — Provide data for follow-up campaigns.

6. **Optimize API Usage** — Cache data to reduce Google Sheets API calls.

---

## Google Sheets Structure

### Sheets/Tabs Used

| Sheet Name | Purpose |
|------------|---------|
| Customer Record | All customer contact info |
| Conversation History | Conversation summaries |
| Members | Registered members with birthday |
| Bookings | All booking records |
| Conversation Insights | Pain points & recommendations |
| Cancellation Log | Cancellation reasons |

### Customer Record Columns

| Column | Field | Description |
|--------|-------|-------------|
| A | Name | Customer name |
| B | Phone | Phone number (key) |
| C | Interest | Current interest |
| D | Last Visit | Last visit date |
| E | Preferences | Customer preferences |
| F | Total Conversations | Conversation count |
| G | Last Updated | Timestamp |

### Bookings Columns

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | Customer phone |
| B | Name | Customer name |
| C | Gender | Customer gender |
| D | Booking Date | Appointment date |
| E | Booking Time | Appointment time |
| F | Service | Service booked |
| G | Therapist Gender | Preference |
| H | Status | Confirmed/Cancelled |
| I | Created At | Record timestamp |

### Members Columns

| Column | Field | Description |
|--------|-------|-------------|
| A | Phone | Member phone (key) |
| B | Name | Member name |
| C | Birthday | YYYY-MM-DD |
| D | Registration Date | When registered |
| E | Points | Loyalty points |
| F | Birthday Benefit Used | Yes/No |

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Lead Manager                            │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Cache     │  │   Rate      │  │   gspread   │         │
│  │   Manager   │  │   Limiter   │  │   Client    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Google Sheets API                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│  │ Customer  │   │ Bookings  │   │  Members  │            │
│  │  Record   │   │   Sheet   │   │   Sheet   │            │
│  └───────────┘   └───────────┘   └───────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                     Request Flow                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Check Cache (TTL: 300 seconds / 5 minutes)                 │
│                                                              │
│  CACHE HIT?                                                 │
│  ├── YES → Return cached data (0ms)                         │
│  └── NO  → Continue to API                                  │
└─────────────────────────┬───────────────────────────────────┘
                          │ CACHE MISS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Rate Limiter Check                                          │
│                                                              │
│  - throttle_if_busy() - Wait if too many recent calls       │
│  - track_api_call() - Record this call                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Google Sheets API Call                                      │
│                                                              │
│  - Retry on 429 quota errors (exponential backoff)          │
│  - Store result in cache                                    │
│  - Return data                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Initialization

```python
class LeadManager:
    def __init__(self, credentials_file: str, spreadsheet_name: str):
        """
        Initialize Lead Manager with Google Sheets connection

        Args:
            credentials_file: Path to service account JSON
            spreadsheet_name: Spreadsheet name or ID
        """
        # Google Sheets API scope
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]

        # Authenticate
        credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=SCOPES
        )
        self.gc = gspread.authorize(credentials)

        # Open spreadsheet
        self.spreadsheet = self.gc.open(spreadsheet_name)

        # Access sheets
        self.customer_sheet = self.spreadsheet.worksheet("Customer Record")
        self.history_sheet = self.spreadsheet.worksheet("Conversation History")
        self.members_sheet = self.spreadsheet.worksheet("Members")
        self.bookings_sheet = self.spreadsheet.worksheet("Bookings")
        self.conversation_insights_sheet = self.spreadsheet.worksheet("Conversation Insights")
        self.cancellation_log_sheet = self.spreadsheet.worksheet("Cancellation Log")

        # Column mappings
        self.columns = {
            'name': 1, 'phone': 2, 'interest': 3,
            'last_visit': 4, 'preferences': 5,
            'total_conversations': 6, 'last_updated': 7
        }

        # Initialize cache (5 minute TTL)
        self.cache_manager = CacheManager(default_ttl=300)

        # Pre-load members into cache
        self._refresh_members_cache()
```

---

## Key Methods

### 1. record_lead() — Create/Update Customer

```python
def record_lead(
    self,
    customer_phone: str,
    customer_name: Optional[str] = None,
    current_interest: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record or update lead in Google Sheets

    Args:
        customer_phone: Customer's phone number (required)
        customer_name: Customer's name (optional)
        current_interest: What customer is interested in (optional)

    Returns:
        {'success': bool, 'message': str, 'row': int, 'action': str}
    """
    # Check if lead exists
    existing_lead = self.get_lead_by_phone(customer_phone)

    if existing_lead:
        # UPDATE existing
        row_num = existing_lead['row']
        cells_to_update = []

        if customer_name:
            cells_to_update.append(Cell(row_num, self.columns['name'], customer_name))
        if current_interest:
            cells_to_update.append(Cell(row_num, self.columns['interest'], current_interest))

        # Batch update (single API call)
        self.sheet.update_cells(cells_to_update)

        # Invalidate cache
        self.cache_manager.invalidate(f"lead_by_phone:{customer_phone}")

        return {'success': True, 'action': 'updated', 'row': row_num}
    else:
        # INSERT new
        new_row = [
            customer_name or 'Unknown',
            customer_phone,
            current_interest or 'Initial Contact',
            datetime.now().strftime("%Y-%m-%d"),
            '',  # Preferences
            0,   # Total conversations
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        self.sheet.append_row(new_row)

        return {'success': True, 'action': 'created'}
```

### 2. get_lead_by_phone() — Find Customer

```python
def get_lead_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
    """
    Find existing lead by phone number (with caching)

    Args:
        phone: Phone number to search for

    Returns:
        dict with lead data if found, None if not found
    """
    # Check cache first
    cache_key = f"lead_by_phone:{phone}"
    cached_result = self.cache_manager.get(cache_key)

    if cached_result is not None:
        logger.info(f"CACHE HIT: Lead data from cache")
        return cached_result

    # Cache miss - query Google Sheets
    logger.info(f"CACHE MISS: Fetching from Google Sheets")

    phone_column = self.sheet.col_values(self.columns['phone'])
    normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '')

    for idx, cell_phone in enumerate(phone_column):
        if idx == 0:  # Skip header
            continue

        normalized_cell = cell_phone.replace('+', '').replace('-', '').replace(' ', '')

        if normalized_cell == normalized_phone:
            row_num = idx + 1
            row_data = self.sheet.row_values(row_num)

            result = {
                'row': row_num,
                'name': row_data[0] if len(row_data) > 0 else '',
                'phone': row_data[1] if len(row_data) > 1 else '',
                'interest': row_data[2] if len(row_data) > 2 else ''
            }

            # Store in cache
            self.cache_manager.set(cache_key, result, ttl=300)

            return result

    return None
```

### 3. record_booking() — Save Booking

```python
def record_booking(
    self,
    phone: str,
    name: str,
    gender: str,
    date: str,
    time: str,
    service: str,
    therapist_gender: str
) -> dict:
    """
    Record new booking to Bookings sheet

    Args:
        phone: Customer phone
        name: Customer name
        gender: Customer gender
        date: Booking date (YYYY-MM-DD)
        time: Booking time
        service: Service booked
        therapist_gender: Therapist preference

    Returns:
        {'success': bool, 'message': str, 'row': int}
    """
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        phone,
        name,
        gender,
        date,
        time,
        service,
        therapist_gender,
        'Confirmed',
        created_at
    ]

    self.bookings_sheet.append_row(row)

    return {
        'success': True,
        'message': 'Booking recorded',
        'row': len(self.bookings_sheet.get_all_values())
    }
```

### 4. get_bookings() — Query Bookings

```python
def get_bookings(self, phone: str) -> dict:
    """
    Get all bookings for a phone number

    Args:
        phone: Customer phone number

    Returns:
        {'success': bool, 'count': int, 'bookings': list}
    """
    # Check cache
    cache_key = f"bookings:{phone}"
    cached = self.cache_manager.get(cache_key)
    if cached:
        return cached

    # Query sheets
    all_bookings = self.bookings_sheet.get_all_records()
    normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '')

    customer_bookings = []
    for booking in all_bookings:
        booking_phone = str(booking.get('Phone', '')).replace('+', '').replace('-', '').replace(' ', '')
        if booking_phone == normalized_phone:
            customer_bookings.append({
                'Name': booking.get('Name', ''),
                'Booking Date': booking.get('Booking Date', ''),
                'Booking Time': booking.get('Booking Time', ''),
                'Service': booking.get('Service', ''),
                'Therapist Gender': booking.get('Therapist Gender', ''),
                'Status': booking.get('Status', '')
            })

    result = {
        'success': True,
        'count': len(customer_bookings),
        'bookings': customer_bookings
    }

    # Cache result
    self.cache_manager.set(cache_key, result, ttl=300)

    return result
```

### 5. register_member() — Register Member

```python
def register_member(self, phone: str, name: str, birthday: str) -> dict:
    """
    Register new member or update existing

    Args:
        phone: Customer phone
        name: Customer name
        birthday: Birthday (YYYY-MM-DD)

    Returns:
        {'success': bool, 'action': str, 'row': int}
    """
    # Check if already exists
    existing = self.get_member(phone)

    if existing['success'] and existing.get('member'):
        member = existing['member']

        # Check if info is same
        if member['name'] == name and member['birthday'] == birthday:
            return {
                'success': True,
                'action': 'already_exists',
                'row': existing['row']
            }
        else:
            # Update existing
            row = existing['row']
            self.members_sheet.update(f'B{row}:C{row}', [[name, birthday]])

            # Invalidate cache
            self.cache_manager.invalidate("all_members")

            return {
                'success': True,
                'action': 'updated',
                'row': row
            }

    # Create new member
    registration_date = datetime.now().strftime('%Y-%m-%d')
    row = [phone, name, birthday, registration_date, 0, 'No']

    self.members_sheet.append_row(row)

    # Invalidate cache
    self.cache_manager.invalidate("all_members")

    return {
        'success': True,
        'action': 'created',
        'row': len(self.members_sheet.get_all_values())
    }
```

### 6. get_member() — Get Member Info

```python
def get_member(self, phone: str) -> dict:
    """
    Get member by phone number (from cache)

    Args:
        phone: Member phone

    Returns:
        {'success': bool, 'member': dict, 'row': int}
    """
    normalized_phone = phone.replace('+', '').replace('-', '').replace(' ', '')

    # Try cache first
    all_members = self.cache_manager.get("all_members")

    if all_members and normalized_phone in all_members:
        member = all_members[normalized_phone]
        return {
            'success': True,
            'member': {
                'Name': member['name'],
                'Birthday': member['birthday'],
                'Points': member['points'],
                'Registration Date': member['registration_date'],
                'Birthday Benefit Used': member['birthday_benefit_used']
            },
            'row': member['row']
        }

    # Cache miss - refresh cache
    self._refresh_members_cache()

    # Try again
    all_members = self.cache_manager.get("all_members")
    if all_members and normalized_phone in all_members:
        member = all_members[normalized_phone]
        return {
            'success': True,
            'member': {...},
            'row': member['row']
        }

    return {'success': False, 'message': 'Member not found'}
```

### 7. get_customer_memory() — AI Context

```python
def get_customer_memory(self, phone: str) -> dict:
    """
    Get customer memory for AI context (tiered history)

    Args:
        phone: Customer phone

    Returns:
        {
            'is_returning': bool,
            'name': str,
            'total_conversations': int,
            'last_visit': str,
            'preferences': str,
            'current_interest': str,
            'conversation_history': list
        }
    """
    # Get customer record
    lead = self.get_lead_by_phone(phone)

    if not lead:
        return {'is_returning': False}

    # Get conversation history
    history = self.get_conversation_history(phone)

    return {
        'is_returning': True,
        'name': lead.get('name', 'Customer'),
        'total_conversations': lead.get('total_conversations', 0),
        'last_visit': lead.get('last_visit', 'Unknown'),
        'preferences': lead.get('preferences', ''),
        'current_interest': lead.get('interest', ''),
        'conversation_history': history[:20]  # Last 20 conversations
    }
```

---

## Rate Limiting & Quota Handling

### Throttling

```python
from utils.rate_limiter import throttle_if_busy, track_api_call

# Before each API call
throttle_if_busy()  # Wait if too many recent calls
self.sheet.get_all_values()  # API call
track_api_call()  # Record this call
```

### Retry on 429 Errors

```python
def _retry_on_quota(self, func, max_attempts=3):
    """Retry with exponential backoff on quota errors"""
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except APIError as e:
            if "[429]" in str(e):
                if attempt < max_attempts:
                    wait_time = 2 ** (attempt - 1)  # 1s, 2s, 4s
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise
```

---

## Caching Strategy

### Cache Keys

| Key Pattern | Data | TTL |
|-------------|------|-----|
| `lead_by_phone:{phone}` | Single lead | 300s |
| `all_leads` | All leads | 300s |
| `all_members` | All members | 300s |
| `bookings:{phone}` | Customer bookings | 300s |

### Cache Invalidation

```python
# After any write operation:
self.cache_manager.invalidate(f"lead_by_phone:{phone}")
self.cache_manager.invalidate("all_leads")
```

### Pre-loading Members

```python
def _refresh_members_cache(self):
    """Load all members into cache on startup"""
    all_members_rows = self.members_sheet.get_all_values()

    members_dict = {}
    for idx, row_data in enumerate(all_members_rows[1:], start=2):
        if row_data[0]:  # Has phone
            normalized_phone = row_data[0].replace('+', '')...
            members_dict[normalized_phone] = {
                'phone': row_data[0],
                'name': row_data[1],
                'birthday': row_data[2],
                ...
            }

    self.cache_manager.set("all_members", members_dict, ttl=300)
```

---

## Integration in app.py

```python
from handlers.tools.lead_manager import LeadManager

# Initialize at startup
lead_manager = LeadManager(
    credentials_file=config.get('lead_tracking.credentials_file'),
    spreadsheet_name=config.get('lead_tracking.spreadsheet_name')
)

# Use in webhook handler
def handle_message(phone, message):
    # Record/update lead
    lead_manager.record_lead(
        customer_phone=phone,
        customer_name=extracted_name,
        current_interest=detected_interest
    )

    # Get customer memory for AI
    memory = lead_manager.get_customer_memory(phone)

    # Include in AI context
    system_prompt = f"Customer info: {memory}"
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 429 Quota Error | Too many API calls | Increase cache TTL |
| Sheet not found | Wrong name | Check spreadsheet name |
| Auth failed | Invalid credentials | Check service account JSON |
| Data not updating | Cache stale | Invalidate cache on write |

### Debug Logging

```
📝 Recording lead for phone: 60123456789
CACHE MISS: Fetching from Google Sheets
✅ Found existing lead at row 15
♻️ Updating existing lead at row 15
   Batch updated 3 fields (1 API call)
   Cache invalidated for updated lead
```

---

## Summary

The Lead Manager is the **Google Sheets integration backbone**:

- **6 sheets** for complete CRM functionality
- **Caching** reduces API calls by 80-90%
- **Rate limiting** prevents quota errors
- **Batch updates** minimize API calls
- **Cache invalidation** keeps data fresh

This enables reliable, scalable customer data management without hitting Google API limits.
