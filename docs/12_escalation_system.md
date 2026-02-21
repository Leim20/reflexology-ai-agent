# Escalation System (Human Handoff)

## Overview

The Escalation System handles **automatic forwarding of customer issues to human staff** via WhatsApp. When the AI detects situations it can't handle (complaints, special requests, complex issues), it triggers an escalation that alerts the appropriate manager.

**Source file:** `handlers/tools/escalation.py`
**Lines of code:** ~417 lines
**Dependencies:** `requests`, `utils.logger`

---

## What is the Purpose?

The Escalation System exists to:

1. **Handle edge cases** — AI can't solve everything; humans need to step in.

2. **Route to right person** — Different issues go to different managers (complaints → branch manager, membership → coordinator).

3. **Provide context** — Staff receives customer name, phone, message, and reason for escalation.

4. **Enable quick response** — Staff can call/message customer directly from the alert.

5. **Track escalations** — Log all escalations for analytics and improvement.

---

## How It Works

### Escalation Flow

```
┌─────────────────────────────────────────────────────────────┐
│               Customer Message                               │
│     "I want a refund, your service was terrible!"           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Detection                              │
│   Recognizes: complaint, refund request, negative sentiment │
│   Decision: ESCALATE                                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              EscalationTool.escalate_to_human()             │
│                                                              │
│   1. Get escalation type: "complaint"                       │
│   2. Find manager: branch_manager (Ryan)                   │
│   3. Format message with all context                        │
│   4. Send via WhatsApp (Whapi)                              │
│   5. Log escalation to file                                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Manager Receives WhatsApp                       │
│                                                              │
│   🚨 ESCALATION ALERT 🚨                                    │
│                                                              │
│   Customer Information:                                      │
│   - Name: Alex                                              │
│   - Phone: 60123456789                                      │
│   - Platform: WHATSAPP                                      │
│   - Date & Time: 2026-02-13 15:30:45                       │
│                                                              │
│   Escalation Reason:                                        │
│   Customer requesting refund due to service complaint       │
│                                                              │
│   Customer's Message:                                       │
│   "I want a refund, your service was terrible!"            │
│                                                              │
│   ---                                                        │
│   Please contact the customer at the above number.          │
└─────────────────────────────────────────────────────────────┘
```

---

## Escalation Types and Routing

### Type-to-Manager Mapping

| Escalation Type | Routes To | When Used |
|-----------------|-----------|-----------|
| `complaint` | Branch Manager | Service complaints, refund requests |
| `special_request` | Branch Manager | Special discounts, VIP treatment |
| `vip_customer` | Branch Manager | High-value customers |
| `system_issue` | Operations Manager | Booking problems, technical issues |
| `booking_problem` | Operations Manager | Can't book, scheduling conflicts |
| `membership` | Membership Coordinator | Membership questions, points issues |
| `birthday_promotion` | Membership Coordinator | Birthday benefits, promotions |
| `general` | Customer Service Supervisor | Catch-all for other issues |

### Example Configuration

```json
{
    "escalation": {
        "enabled": true,
        "log_escalations": true,
        "log_file": "logs/escalations.log",
        "contacts": {
            "branch_manager": {
                "name": "Ryan",
                "phone": "60123456789",
                "role": "Branch Manager"
            },
            "operations_manager": {
                "name": "Sarah",
                "phone": "60120000000",
                "role": "Operations Manager"
            },
            "membership_coordinator": {
                "name": "Jason",
                "phone": "60444555666",
                "role": "Membership Coordinator"
            },
            "customer_service_supervisor": {
                "name": "Mary",
                "phone": "60777888999",
                "role": "Customer Service Supervisor"
            }
        }
    }
}
```

---

## Key Methods

### 1. `escalate_to_human()` — Main Escalation Function

**Purpose:** Send escalation alert to appropriate manager.

```python
result = escalation_tool.escalate_to_human(
    customer_name="Alex",
    customer_phone="60123456789",
    customer_message="I want a refund, your service was terrible!",
    escalation_reason="Customer requesting refund due to service complaint",
    platform="whatsapp",
    escalation_type="complaint"
)

# Returns:
# {
#     'success': True,
#     'message': 'Escalation sent to Ryan',
#     'manager': {
#         'name': 'Ryan',
#         'phone': '60123456789',
#         'role': 'Branch Manager'
#     },
#     'timestamp': '2026-02-13T15:30:45.123456'
# }
```

### 2. `get_escalation_contact()` — Find Right Manager

**Purpose:** Map escalation type to manager contact.

```python
manager = escalation_tool.get_escalation_contact("complaint")
# Returns: {'name': 'Ryan', 'phone': '60123456789', 'role': 'Branch Manager'}
```

### 3. `format_escalation_message()` — Create Alert Message

**Purpose:** Format escalation message with all context.

```python
message = escalation_tool.format_escalation_message(
    customer_name="Alex",
    customer_phone="60123456789",
    customer_message="I want a refund...",
    escalation_reason="Refund request",
    platform="whatsapp"
)
```

### 4. `log_escalation()` — Record to File

**Purpose:** Log escalation for analytics.

```python
# Automatically called after successful escalation
# Writes to: logs/escalations.log
```

---

## Step-by-Step: How I Built This

### Step 1: Initialize with Whapi Credentials

```python
class EscalationTool:
    def __init__(self, whapi_token: str, whapi_channel_id: str, escalation_config: Dict):
        self.whapi_token = whapi_token
        self.whapi_channel_id = whapi_channel_id
        self.base_url = 'https://gate.whapi.cloud'
        self.config = escalation_config
        self.enabled = escalation_config.get('enabled', True)
        self.log_escalations = escalation_config.get('log_escalations', True)
        self.log_file = escalation_config.get('log_file', 'logs/escalations.log')
```

### Step 2: Implement Manager Lookup

```python
def get_escalation_contact(self, escalation_type: str) -> Optional[Dict]:
    contacts = self.config.get('contacts', {})

    # Map types to contact roles
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

    contact_key = type_mapping.get(escalation_type, 'branch_manager')
    contact_info = contacts.get(contact_key)

    if contact_info:
        return {
            'name': contact_info['name'],
            'phone': contact_info['phone'],
            'role': contact_info['role']
        }

    # Fallback to first available contact
    if contacts:
        first_key = list(contacts.keys())[0]
        return contacts[first_key]

    return None
```

### Step 3: Implement Message Formatting

```python
def format_escalation_message(self, customer_name, customer_phone,
                              customer_message, escalation_reason, platform):
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
```

### Step 4: Implement WhatsApp Sending

```python
def _send_whatsapp_message(self, to_phone: str, message: str) -> Dict:
    url = f"{self.base_url}/messages/text"
    headers = {
        "Authorization": f"Bearer {self.whapi_token}",
        "Content-Type": "application/json"
    }
    data = {
        "to": to_phone,
        "body": message
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code in [200, 201]:
            return {'success': True, 'response': response.json()}
        else:
            return {'success': False, 'error': f"HTTP {response.status_code}"}

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'TIMEOUT'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### Step 5: Implement Main Escalation Logic

```python
def escalate_to_human(self, customer_name, customer_phone, customer_message,
                      escalation_reason, platform='whatsapp', escalation_type='general'):

    if not self.enabled:
        return {'success': False, 'error': 'ESCALATION_DISABLED'}

    # Get manager
    manager = self.get_escalation_contact(escalation_type)
    if not manager:
        return {'success': False, 'error': 'NO_CONTACT_FOUND'}

    # Format message
    escalation_message = self.format_escalation_message(
        customer_name, customer_phone, customer_message,
        escalation_reason, platform
    )

    # Send to manager
    send_result = self._send_whatsapp_message(manager['phone'], escalation_message)

    if send_result['success']:
        # Log escalation
        if self.log_escalations:
            self.log_escalation(
                customer_name, customer_phone, escalation_reason,
                escalation_type, manager['name'], manager['phone'], platform
            )

        return {
            'success': True,
            'message': f"Escalation sent to {manager['name']}",
            'manager': manager,
            'timestamp': datetime.now().isoformat()
        }
    else:
        return {
            'success': False,
            'message': 'Failed to send escalation',
            'error': send_result.get('error')
        }
```

### Step 6: Implement Logging

```python
def log_escalation(self, customer_name, customer_phone, escalation_reason,
                   escalation_type, manager_name, manager_phone, platform):
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

    except Exception as e:
        logger.error(f"Failed to log escalation: {e}")
```

---

## Integration in app.py

### Initialize Escalation Tool

```python
from handlers.tools.escalation import create_escalation_tool

escalation_tool = create_escalation_tool(
    whapi_token=config.get_env('WHAPI_API_TOKEN'),
    whapi_channel_id=config.get_env('WHAPI_CHANNEL_ID'),
    escalation_config=config.get('escalation', {})
)
```

### AI Function Calling Integration

The AI can trigger escalations via function calling:

```python
# Define tool for AI
ESCALATION_TOOL = {
    "type": "function",
    "function": {
        "name": "escalate_to_human",
        "description": "Escalate customer issue to human staff when AI cannot help",
        "parameters": {
            "type": "object",
            "properties": {
                "escalation_reason": {
                    "type": "string",
                    "description": "Why this is being escalated"
                },
                "escalation_type": {
                    "type": "string",
                    "enum": ["complaint", "special_request", "membership", "booking_problem", "general"]
                }
            },
            "required": ["escalation_reason", "escalation_type"]
        }
    }
}

# Handle AI function call
def handle_escalation_tool_call(args, customer_name, customer_phone, customer_message):
    result = escalation_tool.escalate_to_human(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_message=customer_message,
        escalation_reason=args['escalation_reason'],
        escalation_type=args['escalation_type'],
        platform='whatsapp'
    )
    return result
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Escalation not sent | Whapi token invalid | Check WHAPI_API_TOKEN |
| Wrong manager notified | Type mapping wrong | Check escalation_type |
| No manager found | Config missing | Add contacts to config |
| Log file not created | Permission denied | Check directory permissions |

### Debug Logging

```
🚨 ESCALATING TO HUMAN
📋 ESCALATION DETAILS:
   Customer Name: 'Alex' (length: 4 chars)
   Customer Phone: '60123456789'
   Escalation Type: 'complaint'
   Platform: 'whatsapp'
   Reason: 'Customer requesting refund'
🔍 Finding manager for type: 'complaint'
✓ Manager found: Ryan (Branch Manager)
📤 Sending escalation to manager: 60123456789
✅ ESCALATION SENT SUCCESSFULLY!
```

### Check Escalation Log

```bash
tail -f logs/escalations.log
```

Example log entry:
```
2026-02-13 15:30:45 | Type: complaint | Customer: Alex (60123456789) | Reason: Refund request | Manager: Ryan (60123456789) | Platform: whatsapp
```

---

## Best Practices

### 1. Always Provide Clear Reason

```python
# Good - specific reason
escalation_tool.escalate_to_human(
    escalation_reason="Customer requesting full refund due to no-show therapist on Feb 10"
)

# Bad - vague
escalation_tool.escalate_to_human(
    escalation_reason="Customer complaint"
)
```

### 2. Include Customer Message Context

```python
# Include the actual customer message
escalation_tool.escalate_to_human(
    customer_message=full_customer_message,  # Not truncated
    escalation_reason="Summary of why escalating"
)
```

### 3. Handle Escalation Failure

```python
result = escalation_tool.escalate_to_human(...)

if not result['success']:
    logger.error(f"Escalation failed: {result.get('error')}")
    # Inform customer
    return "I'm having trouble reaching our manager. Please call us at 03-1234 5678."
```

### 4. Confirm Escalation to Customer

```python
if result['success']:
    return f"I've notified our {result['manager']['role']} {result['manager']['name']}. They will contact you shortly."
```

---

## Summary

The Escalation System provides **intelligent human handoff**:

- **Type-based routing**: Different issues go to different managers
- **Rich context**: Full customer info and message in alert
- **WhatsApp delivery**: Instant notification to staff phones
- **Comprehensive logging**: Track all escalations for analytics
- **AI integration**: Can be triggered via function calling

This ensures no customer issue falls through the cracks, with appropriate staff notified immediately when the AI can't help.
