# Configuration System

## Overview

The Configuration System is the **centralized settings manager** for the entire chat agent. It loads, validates, and provides access to all configuration from three sources: `config.json`, `.env`, and `prompts.yaml` (or TXT files).

**Source file:** `core/config_loader.py`
**Lines of code:** ~408 lines
**Dependencies:** `python-dotenv`, `PyYAML`, `utils.logger`

---

## What is the Purpose?

The Configuration System exists to:

1. **Centralize all settings** — One place to manage agent name, AI model, API keys, feature flags, etc.

2. **Separate code from configuration** — Change behavior without modifying code.

3. **Protect secrets** — API keys stay in `.env` (not committed to git).

4. **Support template variables** — `{{AGENT_NAME}}` in prompts is replaced with actual name.

5. **Load knowledge base** — Automatically loads product catalog for AI context.

6. **Provide easy access** — Dot notation (`config.get('ai.model')`) for nested settings.

---

## How It Works

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                   Configuration System                       │
└─────────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────────┐
│   .env      │  │config.json  │  │ prompts/*.txt   │
│             │  │             │  │ or prompts.yaml │
│ - API Keys  │  │ - Agent     │  │                 │
│ - Secrets   │  │   settings  │  │ - System        │
│ - URLs      │  │ - Features  │  │   prompts       │
│             │  │ - AI config │  │ - Templates     │
└─────────────┘  └─────────────┘  └─────────────────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │ Knowledge Base  │
                │ (catalog.txt)   │
                └─────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │        Config Instance         │
         │                                │
         │  config.get('agent.name')      │
         │  config.get_env('OPENAI_KEY')  │
         │  config.get_prompt('whatsapp') │
         │  config.knowledge_base         │
         └────────────────────────────────┘
```

---

## Configuration Files

### 1. `.env` — Secrets and API Keys

```bash
# OpenAI API
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Whapi (WhatsApp API)
WHAPI_API_TOKEN=Ro10XvLAumv5m9xxxxx
WHAPI_CHANNEL_ID=60123456789
WHAPI_BROADCAST_TOKEN=xxxxx
WHAPI_BROADCAST_CHANNEL_ID=xxxxx

# Webhook
WEBHOOK_URL=https://your-domain.com

# Flask
FLASK_SECRET_KEY=your-secret-key-here

# Chatwoot CRM
CHATWOOT_API_ACCESS_TOKEN=xxxxx
CHATWOOT_BASE_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=12345
CHATWOOT_INBOX_ID=67890

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
```

### 2. `config/config.json` — Agent Settings

```json
{
    "agent": {
        "name": "Jessica",
        "role": "reflexology consultant",
        "description": "Friendly reflexology consultant..."
    },
    "ai": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1500
    },
    "platforms": {
        "web": {
            "enabled": true,
            "port": 5001
        },
        "whatsapp": {
            "enabled": true
        }
    },
    "knowledge_base": {
        "enabled": true,
        "path": "data/knowledge_base/catalog.txt",
        "section_marker": "[CATALOG]"
    },
    "lead_tracking": {
        "enabled": true,
        "spreadsheet_name": "1ZcuMMAS-5dvWV2...",
        "credentials_file": "config/service-account.json"
    },
    "booking_notification": {
        "enabled": true,
        "notify_phone": "60123456789",
        "notify_name": "Manager"
    },
    "escalation": {
        "enabled": true,
        "contacts": {
            "branch_manager": {
                "name": "Ryan",
                "phone": "60123456789",
                "role": "Branch Manager"
            }
        }
    },
    "google_sheets_features": {
        "follow_up_system": {"enabled": true},
        "broadcast_system": {"enabled": true}
    }
}
```

### 3. `config/prompts/*.txt` or `prompts.yaml` — System Prompts

**TXT format (preferred):**

```
config/prompts/
├── whatsapp_with_knowledge.txt
├── whatsapp_without_knowledge.txt
├── web_with_knowledge.txt
└── web_without_knowledge.txt
```

**Example prompt file:**

```text
You are {{AGENT_NAME}}, a {{AGENT_ROLE}} at Serenity Reflexology.

Your knowledge base:
{{KNOWLEDGE_BASE}}

Guidelines:
1. Be friendly and professional
2. Answer based on knowledge base only
3. If unsure, offer to escalate
...
```

---

## Key Methods

### 1. `load_config()` — Initialize Configuration

**Purpose:** Load all configuration files and create global instance.

```python
from core import load_config, get_config

# Initialize (call once at startup)
config = load_config(config_dir='config', env_file='.env')

# Access anywhere in code
config = get_config()
```

### 2. `config.get(key, default)` — Get Config Value

**Purpose:** Access nested configuration with dot notation.

```python
# Get agent name
name = config.get('agent.name', 'Assistant')
# Returns: "Jessica"

# Get AI model
model = config.get('ai.model', 'gpt-4o-mini')
# Returns: "gpt-4o-mini"

# Get nested value
port = config.get('platforms.web.port', 5000)
# Returns: 5001

# Get with default when missing
timeout = config.get('ai.timeout', 30)
# Returns: 30 (default, since not in config)
```

### 3. `config.get_env(key, default)` — Get Environment Variable

**Purpose:** Access secrets from `.env` file.

```python
# Get API key
api_key = config.get_env('OPENAI_API_KEY')
# Returns: "sk-proj-xxxxx..."

# Get with default
host = config.get_env('REDIS_HOST', '127.0.0.1')
```

### 4. `config.get_prompt(prompt_name)` — Get System Prompt

**Purpose:** Get prompt template with variables substituted.

```python
# Get WhatsApp prompt with knowledge base
prompt = config.get_prompt('whatsapp_with_knowledge')
# Returns prompt with {{AGENT_NAME}}, {{KNOWLEDGE_BASE}} replaced

# Get web prompt without knowledge
prompt = config.get_prompt('web_without_knowledge')
```

### 5. `config.knowledge_base` — Get Knowledge Base Content

**Purpose:** Access the loaded knowledge base.

```python
# Check if loaded
if config.has_knowledge_base:
    kb = config.knowledge_base
    print(f"Knowledge base: {len(kb)} characters")
```

---

## Step-by-Step: How I Built This

### Step 1: Create Config Class Structure

```python
class Config:
    def __init__(self, config_dir='config', env_file='.env'):
        self.config_dir = config_dir
        self.env_file = env_file

        # Storage
        self._config = {}       # config.json data
        self._env_vars = {}     # .env data
        self._prompts = {}      # prompts data
        self._knowledge_base = ""

        # Load all
        self._load_env()
        self._load_config_json()
        self._load_prompts()
        self._load_knowledge_base()
```

### Step 2: Load Environment Variables

```python
def _load_env(self):
    from dotenv import load_dotenv

    if os.path.exists(self.env_file):
        load_dotenv(self.env_file)

    # Load required variables
    required_env_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'WHAPI_API_TOKEN': os.getenv('WHAPI_API_TOKEN'),
        ...
    }

    for key, value in required_env_vars.items():
        if value and not value.startswith('{{'):  # Not a placeholder
            self._env_vars[key] = value
        else:
            logger.warning(f"{key}: NOT SET")
```

### Step 3: Load JSON Configuration

```python
def _load_config_json(self):
    config_file = os.path.join(self.config_dir, 'config.json')

    with open(config_file, 'r', encoding='utf-8') as f:
        self._config = json.load(f)

    # Log key values
    agent_name = self._config.get('agent', {}).get('name', 'Unknown')
    logger.info(f"Agent Name: {agent_name}")
```

### Step 4: Load Prompts (TXT or YAML)

```python
def _load_prompts(self):
    prompts_dir = os.path.join(self.config_dir, "prompts")
    prompts_yaml = os.path.join(self.config_dir, "prompts.yaml")

    # Try TXT files first (preferred)
    if os.path.isdir(prompts_dir):
        self._prompts = {"prompts": {}}
        txt_files = [f for f in os.listdir(prompts_dir) if f.endswith(".txt")]

        for txt_file in txt_files:
            prompt_name = txt_file.replace(".txt", "")
            with open(os.path.join(prompts_dir, txt_file), "r") as f:
                self._prompts["prompts"][prompt_name] = f.read()
        return

    # Fallback to YAML
    with open(prompts_yaml, "r") as f:
        self._prompts = yaml.safe_load(f)
```

### Step 5: Load Knowledge Base

```python
def _load_knowledge_base(self):
    kb_config = self._config.get('knowledge_base', {})
    if not kb_config.get('enabled', False):
        return

    kb_path = kb_config.get('path', 'data/knowledge_base/catalog.txt')
    section_marker = kb_config.get('section_marker', '[CATALOG]')

    with open(kb_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract section if marker exists
    if section_marker in content:
        start_idx = content.index(section_marker) + len(section_marker)
        self._knowledge_base = content[start_idx:].strip()
    else:
        self._knowledge_base = content.strip()
```

### Step 6: Implement Dot Notation Access

```python
def get(self, key: str, default: Any = None) -> Any:
    """Get config value with dot notation: 'ai.model'"""
    keys = key.split('.')
    value = self._config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value
```

### Step 7: Implement Template Variable Substitution

```python
def get_prompt(self, prompt_name: str) -> str:
    prompts = self._prompts.get('prompts', {})
    if prompt_name not in prompts:
        return f"You are {self.get('agent.name', 'an assistant')}."

    prompt_template = prompts[prompt_name]

    # Substitute variables
    variables = {
        'AGENT_NAME': self.get('agent.name', 'Assistant'),
        'AGENT_ROLE': self.get('agent.role', 'helper'),
        'KNOWLEDGE_BASE': self._knowledge_base
    }

    prompt = prompt_template
    for key, value in variables.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)

    return prompt
```

### Step 8: Create Global Singleton

```python
_config_instance: Optional[Config] = None

def load_config(config_dir='config', env_file='.env') -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_dir, env_file)
    return _config_instance

def get_config() -> Config:
    if _config_instance is None:
        raise ConfigurationError("Configuration not loaded. Call load_config() first.")
    return _config_instance
```

---

## Template Variables

### Available Variables in Prompts

| Variable | Source | Example Value |
|----------|--------|---------------|
| `{{AGENT_NAME}}` | config.json → agent.name | "Jessica" |
| `{{AGENT_ROLE}}` | config.json → agent.role | "reflexology consultant" |
| `{{KNOWLEDGE_BASE}}` | catalog.txt content | "[Services] ..." |

### Example Usage in Prompt File

```text
You are {{AGENT_NAME}}, a friendly {{AGENT_ROLE}} at Serenity Reflexology.

Your knowledge base:
{{KNOWLEDGE_BASE}}

When customers ask about services, refer to the knowledge base above.
```

**After substitution:**

```text
You are Jessica, a friendly reflexology consultant at Serenity Reflexology.

Your knowledge base:
[Services]
- 60-min Foot Reflexology: RM88
- 90-min Body Massage: RM128
...

When customers ask about services, refer to the knowledge base above.
```

---

## Integration Points

### Initialization in app.py

```python
from core import load_config, get_config

# Load at startup
config = load_config()

# Initialize AI Engine with config values
ai_engine = AIEngine(
    api_key=config.get_env('OPENAI_API_KEY'),
    model=config.get('ai.model', 'gpt-4o-mini'),
    temperature=config.get('ai.temperature', 0.7),
    max_tokens=config.get('ai.max_tokens', 1500)
)

# Get system prompt
system_prompt = config.get_prompt('whatsapp_with_knowledge')
```

### Feature Flags Usage

```python
# Check if follow-up system is enabled
if config.get('google_sheets_features.follow_up_system.enabled', False):
    follow_up_manager = FollowUpManager(...)

# Check if broadcast is enabled
if config.get('google_sheets_features.broadcast_system.enabled', False):
    broadcast_manager = BroadcastManager(...)
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ConfigurationError` | Config not loaded | Call `load_config()` first |
| API key not found | Not in .env | Check .env file exists |
| Placeholder in value | `{{KEY}}` not replaced | Run setup_agent.py |
| Prompt not found | Wrong name | Check prompts/*.txt files |

### Debug Checklist

1. Check .env file exists and has values
2. Check config.json is valid JSON
3. Check prompts folder has .txt files
4. Check knowledge base file exists
5. Review logs for "NOT SET" warnings

### Verification Script

```python
from core import load_config

config = load_config()

print(f"Agent: {config.get('agent.name')}")
print(f"Model: {config.get('ai.model')}")
print(f"API Key: {'SET' if config.get_env('OPENAI_API_KEY') else 'MISSING'}")
print(f"Knowledge Base: {len(config.knowledge_base)} chars")
print(f"Prompts: {list(config._prompts.get('prompts', {}).keys())}")
```

---

## Best Practices

### 1. Always Use Default Values

```python
# Good - has fallback
port = config.get('platforms.web.port', 5000)

# Bad - may crash
port = config.get('platforms.web.port')  # Returns None if missing
```

### 2. Check Feature Flags Before Using

```python
if config.get('lead_tracking.enabled', False):
    # Only initialize if enabled
    lead_manager = LeadManager(...)
```

### 3. Never Hardcode API Keys

```python
# Good
api_key = config.get_env('OPENAI_API_KEY')

# Bad - NEVER do this
api_key = "sk-proj-xxxxx"  # Security risk!
```

### 4. Log Configuration at Startup

```python
logger.info(f"Configuration loaded:")
logger.info(f"  Agent: {config.get('agent.name')}")
logger.info(f"  Model: {config.get('ai.model')}")
logger.info(f"  Port: {config.get('platforms.web.port')}")
```

---

## Summary

The Configuration System is the **settings backbone** of the chat agent:

- **Three-layer configuration**: .env (secrets) + config.json (settings) + prompts (templates)
- **Dot notation access** for nested values
- **Template variable substitution** in prompts
- **Knowledge base loading** for AI context
- **Global singleton** for easy access anywhere
- **Comprehensive logging** for debugging

All components depend on this module for their settings, making it foundational to the entire system.
