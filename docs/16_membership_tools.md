# Membership Function Tools

## Overview

The Membership Tools are **2 OpenAI function calling tools** that handle member registration and membership status queries. They integrate with Google Sheets to store member data and provide real-time membership information to the AI.

**Location:** `web/app.py` (lines 997-1143, 1587-1600)
**Tools:** `register_member`, `check_my_membership`
**Dependencies:** `handlers/tools/lead_manager.py`, Google Sheets (Members tab)

---

## What is the Purpose?

The Membership Tools exist to:

1. **Register New Members** — Save customer name, phone, and birthday to Members sheet.

2. **Track Loyalty Points** — Members earn points for visits (future feature).

3. **Birthday Benefits** — Enable birthday promotions and tracking.

4. **Query Membership Status** — Let customers check their membership info.

5. **Prevent Duplicate Registration** — Check if customer is already a member.

---

## The 2 Membership Tools

| Tool | When Called | Purpose |
|------|-------------|---------|
| `register_member` | After customer confirms info | Save new member to Google Sheets |
| `check_my_membership` | When customer asks about status | Refresh membership data |

---

## Tool 1: register_member

### Purpose

Register a new member in the Members database when customer provides their **Name, Phone, and Birthday** and confirms the information is correct.

### Function Definition

```python
def get_register_member_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "register_member",
            "description": "Register a new member in the Members database when customer provides their Name, Phone, and Birthday. ONLY call this function AFTER customer confirms their information is correct. Do NOT call this speculatively - wait for explicit confirmation (e.g., '对', '是的', 'yes', 'correct').",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's full name (e.g., '李明', 'John Smith')"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number. Extract digits only from any format."
                    },
                    "customer_birthday": {
                        "type": "string",
                        "description": "Customer's birthday in YYYY-MM-DD format. Convert from any format they provide."
                    }
                },
                "required": ["customer_name", "customer_phone", "customer_birthday"]
            }
        }
    }
```

### Handler Implementation

```python
def handle_register_member_function_call(
    function_args: dict,
    whatsapp_phone: str
) -> dict:
    """
    Handle register_member function call from AI

    Args:
        function_args: Arguments from AI (name, phone, birthday)
        whatsapp_phone: Customer's WhatsApp phone (for fallback)

    Returns:
        dict with success status and message for AI
    """
    logger.info("="*80)
    logger.info("HANDLING MEMBER REGISTRATION FUNCTION CALL")
    logger.info("="*80)

    # Extract function arguments
    customer_name = function_args.get('customer_name', '')
    customer_phone = function_args.get('customer_phone', '')
    customer_birthday = function_args.get('customer_birthday', '')

    logger.info(f"Name: '{customer_name}'")
    logger.info(f"Phone: '{customer_phone}'")
    logger.info(f"Birthday: '{customer_birthday}'")

    # Validate inputs
    if not customer_name or not customer_phone or not customer_birthday:
        logger.error("Missing required fields for registration")
        return {
            'success': False,
            'message': 'Missing name, phone, or birthday information'
        }

    # Validate birthday format (YYYY-MM-DD)
    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', customer_birthday):
        logger.error(f"Invalid birthday format: {customer_birthday}")
        return {
            'success': False,
            'message': f'Invalid birthday format: {customer_birthday}. Expected YYYY-MM-DD.'
        }

    # Check if lead_manager is available
    if not lead_manager:
        logger.error("Lead manager not available")
        return {
            'success': False,
            'message': 'Member registration system not available'
        }

    try:
        # Normalize phone number
        normalized_phone = customer_phone.replace('@s.whatsapp.net', '')
        normalized_phone = ''.join(filter(str.isdigit, normalized_phone))

        # Call lead_manager.register_member()
        result = lead_manager.register_member(
            phone=normalized_phone,
            name=customer_name,
            birthday=customer_birthday
        )

        if result['success']:
            action = result['action']
            row = result['row']

            logger.info(f"Registration {action}: Row {row}")

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
            logger.error(f"Registration failed: {result['message']}")
            return {
                'success': False,
                'message': f'Registration failed: {result["message"]}'
            }

    except Exception as e:
        logger.error(f"Exception during member registration: {str(e)}")
        return {
            'success': False,
            'message': f'Error during registration: {str(e)}'
        }
```

### Registration Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Customer: "I want to register as member"                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI: "Sure! I'll need your name, phone, and birthday.      │
│       What's your full name?"                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Customer: "李明, 012-345-6789, 5月15号1990年"              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI: "Let me confirm your details:                          │
│       Name: 李明                                            │
│       Phone: 60123456789                                    │
│       Birthday: 1990-05-15                                  │
│       Is this correct?"                                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Customer: "对的" / "Yes" / "Correct"                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI calls: register_member(                                 │
│      customer_name="李明",                                  │
│      customer_phone="60123456789",                          │
│      customer_birthday="1990-05-15"                         │
│  )                                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Handler:                                                    │
│  1. Validate inputs                                         │
│  2. Normalize phone number                                  │
│  3. Call lead_manager.register_member()                     │
│  4. Save to Google Sheets (Members tab)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI: "Congratulations! You're now registered as a member.  │
│       You'll receive birthday benefits and earn points!"    │
└─────────────────────────────────────────────────────────────┘
```

### Google Sheets: Members Tab Structure

| Column | Field | Example |
|--------|-------|---------|
| A | Phone | 60123456789 |
| B | Name | 李明 |
| C | Birthday | 1990-05-15 |
| D | Registration Date | 2026-02-21 |
| E | Points | 0 |
| F | Birthday Benefit Used | No |

---

## Tool 2: check_my_membership

### Purpose

Refresh customer membership data when they ask about their status. This is a **secure tool** that only returns data for the current WhatsApp sender.

### Function Definition

```python
def get_check_my_membership_function_definition():
    return {
        "type": "function",
        "function": {
            "name": "check_my_membership",
            "description": "Refresh customer membership data. Only use this if customer says their membership info seems wrong or outdated. Membership status is already pre-loaded - do NOT call this for normal membership questions.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
```

### Handler Implementation

```python
def handle_check_my_membership(sender: str) -> dict:
    """
    Handle check_my_membership function call

    Security: Uses sender's WhatsApp phone only, not user input

    Args:
        sender: Customer's WhatsApp phone (from webhook, not user input)

    Returns:
        dict with membership information
    """
    logger.info("="*80)
    logger.info("HANDLING CHECK_MY_MEMBERSHIP FUNCTION CALL")
    logger.info("="*80)
    logger.info(f"Phone: {sender}")

    if not lead_manager:
        return {
            'success': False,
            'message': 'Membership system not available'
        }

    try:
        # Normalize phone
        normalized_phone = sender.replace('@s.whatsapp.net', '')

        # Get membership info
        result = lead_manager.get_member(normalized_phone)

        if result['success'] and result.get('member'):
            member = result['member']
            return {
                'success': True,
                'is_member': True,
                'name': member.get('Name', 'Unknown'),
                'birthday': member.get('Birthday', 'Unknown'),
                'points': member.get('Points', 0),
                'registration_date': member.get('Registration Date', 'Unknown'),
                'birthday_benefit_used': member.get('Birthday Benefit Used', 'No')
            }
        else:
            return {
                'success': True,
                'is_member': False,
                'message': 'You are not registered as a member yet.'
            }

    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return {
            'success': False,
            'message': f'Error checking membership: {str(e)}'
        }
```

### Security: No Parameters

Notice that `check_my_membership` has **no parameters**. This is intentional security design:

```python
# SECURE: Phone comes from WhatsApp webhook, not user input
def handle_check_my_membership(sender: str):
    # sender = "60123456789" from webhook
    result = lead_manager.get_member(sender)  # Only returns THIS user's data

# INSECURE (not implemented): If we allowed phone as parameter
def insecure_check_membership(phone: str):
    # User could ask: "Check membership for 60120000000"
    # And access someone else's data!
```

---

## Pre-loaded Membership Status

Membership data is **pre-fetched** when conversation starts, so AI already knows:

```python
def pre_fetch_membership_status(phone: str) -> dict:
    """Pre-fetch membership status for session context"""
    result = {
        "is_member": False,
        "name": None,
        "birthday": None,
        "points": 0
    }

    if not lead_manager:
        return result

    try:
        member_result = lead_manager.get_member(phone)

        if member_result.get("success") and member_result.get("member"):
            member = member_result["member"]
            result["is_member"] = True
            result["name"] = member.get("Name")
            result["birthday"] = member.get("Birthday")
            result["points"] = member.get("Points", 0)
    except:
        pass

    return result
```

This data is included in the system prompt:

```
CUSTOMER MEMBERSHIP STATUS:
- Is Member: Yes
- Name: 李明
- Birthday: 1990-05-15
- Points: 150
```

So AI can answer membership questions **without calling the tool** unless refresh is needed.

---

## LeadManager Integration

### register_member() Method

```python
def register_member(self, phone: str, name: str, birthday: str) -> dict:
    """
    Register new member or update existing

    Args:
        phone: Customer phone number
        name: Customer name
        birthday: Birthday in YYYY-MM-DD format

    Returns:
        dict: {success, action, row, message}
    """
    # Check if already exists
    existing = self.get_member(phone)

    if existing['success'] and existing.get('member'):
        # Check if info is same
        member = existing['member']
        if member['Name'] == name and member['Birthday'] == birthday:
            return {
                'success': True,
                'action': 'already_exists',
                'row': existing['row']
            }
        else:
            # Update existing
            self.members_sheet.update(f'B{existing["row"]}:C{existing["row"]}',
                                      [[name, birthday]])
            return {
                'success': True,
                'action': 'updated',
                'row': existing['row']
            }

    # Create new
    registration_date = datetime.now().strftime('%Y-%m-%d')
    row = [phone, name, birthday, registration_date, 0, 'No']
    self.members_sheet.append_row(row)

    return {
        'success': True,
        'action': 'created',
        'row': len(self.members_sheet.get_all_values())
    }
```

### get_member() Method

```python
def get_member(self, phone: str) -> dict:
    """
    Get member by phone number

    Args:
        phone: Customer phone number

    Returns:
        dict: {success, member, row}
    """
    all_members = self.members_sheet.get_all_records()

    for idx, member in enumerate(all_members):
        if str(member.get('Phone', '')) == phone:
            return {
                'success': True,
                'member': member,
                'row': idx + 2  # +2 for header and 0-index
            }

    return {
        'success': False,
        'message': 'Member not found'
    }
```

---

## Birthday Promotion Integration

When customer is a member and it's their birthday month:

```python
def check_birthday_benefit(phone: str) -> dict:
    """Check if customer has birthday benefit available"""
    member_result = lead_manager.get_member(phone)

    if not member_result.get('member'):
        return {'eligible': False}

    member = member_result['member']
    birthday = member.get('Birthday', '')
    benefit_used = member.get('Birthday Benefit Used', 'No')

    # Check if birthday month
    if birthday:
        birth_month = int(birthday.split('-')[1])
        current_month = datetime.now().month

        if birth_month == current_month and benefit_used == 'No':
            return {
                'eligible': True,
                'benefit': '10% discount on any service',
                'expires': f'End of {datetime.now().strftime("%B")}'
            }

    return {'eligible': False}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Registration fails | Members sheet not found | Run setup_members_sheet.py |
| Invalid birthday | Wrong format | Ensure YYYY-MM-DD |
| Duplicate member | Already registered | Check existing first |
| Can't find member | Phone format mismatch | Normalize phone numbers |

### Debug Logging

```
HANDLING MEMBER REGISTRATION FUNCTION CALL
================================================================================
Name: '李明'
Phone: '60123456789'
Birthday: '1990-05-15'
Calling lead_manager.register_member()...
Registration created: Row 15
================================================================================
```

---

## Summary

The 2 Membership Tools provide **member management**:

- **`register_member`** — Save new members with name, phone, birthday
- **`check_my_membership`** — Secure query for current user's status

Features:
- Duplicate prevention (check before create)
- Update existing members
- Birthday benefit tracking
- Points system ready
- Pre-loaded status for quick AI responses

This enables a **loyalty program** that rewards repeat customers.
