#!/usr/bin/env python3
"""
Setup Agent Script
Interactive setup wizard to configure a new agent from this template
"""

import os
import json
import secrets
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")


def print_success(text):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"✗ {text}")


def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print_error("This field is required!")


def main():
    """Main setup function"""
    print_header("CHAT AGENT TEMPLATE - SETUP WIZARD")

    print("Welcome to the Chat Agent Template Setup Wizard!")
    print("This will help you configure your new AI agent.")
    print("\nYou'll be asked to provide:")
    print("  - Agent name and role")
    print("  - API keys and tokens")
    print("  - Configuration settings")
    print("\nLet's get started!\n")

    input("Press Enter to continue...")

    # ========================================================================
    # Step 1: Agent Information
    # ========================================================================
    print_header("STEP 1: AGENT INFORMATION")

    agent_name = get_input("Agent Name (e.g., 'Ucore', 'ShopBot')", "ChatAgent")
    agent_role = get_input("Agent Role (e.g., 'clothing shop assistant', 'customer support')", "helpful assistant")
    agent_desc = get_input("Agent Description", f"{agent_name} - an AI {agent_role}")

    print_success(f"Agent configured: {agent_name} ({agent_role})")

    # ========================================================================
    # Step 2: API Keys
    # ========================================================================
    print_header("STEP 2: API KEYS")

    print("You'll need API keys from:")
    print("  - OpenAI: https://platform.openai.com/api-keys")
    print("  - Whapi (for WhatsApp): https://whapi.cloud")
    print()

    openai_key = get_input("OpenAI API Key (sk-proj-...)")

    enable_whatsapp = input("\nEnable WhatsApp integration? (y/n) [y]: ").strip().lower()
    enable_whatsapp = enable_whatsapp != 'n'

    whapi_token = None
    whapi_channel = None
    webhook_url = None

    if enable_whatsapp:
        whapi_token = get_input("Whapi API Token")
        whapi_channel = get_input("Whapi Channel ID (your WhatsApp number, e.g., 60123456789)")
        webhook_url = get_input("Webhook URL (e.g., https://your-domain.com/webhook/whapi)", "http://localhost:5000/webhook/whapi")
        print_success("WhatsApp integration configured")
    else:
        print("WhatsApp integration skipped")
        whapi_token = "<PUT_YOUR_WHAPI_API_TOKEN_HERE>"  # <-- put your Whapi API token here
        whapi_channel = "<PUT_YOUR_WHAPI_CHANNEL_ID_HERE>"  # <-- put your Whapi channel ID here
        webhook_url = "<PUT_YOUR_WEBHOOK_URL_HERE>"  # <-- put your webhook URL here

    # Generate Flask secret key
    flask_secret = secrets.token_hex(32)
    print_success("Flask secret key generated")

    # ========================================================================
    # Step 3: Model Configuration
    # ========================================================================
    print_header("STEP 3: AI MODEL CONFIGURATION")

    print("Available models:")
    print("  1. gpt-4o (recommended - best multimodal)")
    print("  2. gpt-4")
    print("  3. gpt-3.5-turbo")

    model_choice = input("\nChoose model (1-3) [1]: ").strip()
    model_map = {
        '1': 'gpt-4o',
        '2': 'gpt-4',
        '3': 'gpt-3.5-turbo',
        '': 'gpt-4o'
    }
    model = model_map.get(model_choice, 'gpt-4o')

    print_success(f"Model configured: {model}")

    # ========================================================================
    # Step 4: Update Configuration Files
    # ========================================================================
    print_header("STEP 4: UPDATING CONFIGURATION FILES")

    try:
        # Update config.json
        config_path = 'config/config.json'
        print(f"Updating {config_path}...")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        config['agent']['name'] = agent_name
        config['agent']['role'] = agent_role
        config['agent']['description'] = agent_desc
        config['ai']['model'] = model
        config['platforms']['whatsapp']['enabled'] = enable_whatsapp

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print_success(f"{config_path} updated")

        # Create .env file
        env_path = '.env'
        print(f"\nCreating {env_path}...")

        env_content = f"""# ============================================================================
# CHAT AGENT - ENVIRONMENT VARIABLES
# ============================================================================
# Generated by setup_agent.py
# Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ============================================================================

# ----------------------------------------------------------------------------
# OpenAI API Configuration
# ----------------------------------------------------------------------------
OPENAI_API_KEY={openai_key}

# ----------------------------------------------------------------------------
# WhatsApp Integration (Whapi)
# ----------------------------------------------------------------------------
WHAPI_API_TOKEN={whapi_token}
WHAPI_CHANNEL_ID={whapi_channel}

# ----------------------------------------------------------------------------
# Webhook Configuration
# ----------------------------------------------------------------------------
WEBHOOK_URL={webhook_url}

# ----------------------------------------------------------------------------
# Flask Configuration
# ----------------------------------------------------------------------------
FLASK_SECRET_KEY={flask_secret}
FLASK_ENV=development
FLASK_DEBUG=True
"""

        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)

        print_success(f"{env_path} created")

        # ========================================================================
        # Step 5: Verify Installation
        # ========================================================================
        print_header("STEP 5: VERIFICATION")

        print("Checking required directories...")
        dirs_to_check = ['data/uploads', 'data/knowledge_base', 'logs']
        for dir_path in dirs_to_check:
            if os.path.exists(dir_path):
                print_success(f"{dir_path} exists")
            else:
                os.makedirs(dir_path, exist_ok=True)
                print_success(f"{dir_path} created")

        print("\nChecking required files...")
        files_to_check = [
            'requirements.txt',
            'config/prompts.yaml',
            'data/knowledge_base/catalog.txt'
        ]
        for file_path in files_to_check:
            if os.path.exists(file_path):
                print_success(f"{file_path} exists")
            else:
                print_error(f"{file_path} MISSING!")

        # ========================================================================
        # Step 6: Final Instructions
        # ========================================================================
        print_header("SETUP COMPLETE!")

        print(f"✅ Your agent '{agent_name}' is configured and ready!")
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("\n1. Edit your knowledge base:")
        print("   nano data/knowledge_base/catalog.txt")
        print("\n2. Install dependencies:")
        print("   pip install -r requirements.txt")
        print("\n3. Run your agent:")
        print("   python web/app.py")
        print("\n4. Access the web interface:")
        print("   http://localhost:5000")

        if enable_whatsapp:
            print("\n5. Configure WhatsApp webhook in Whapi dashboard:")
            print(f"   Webhook URL: {webhook_url}")

        print("\n" + "="*80)
        print("For deployment to VPS, see DEPLOYMENT.md")
        print("="*80 + "\n")

        print("🎉 Happy chatting!")

    except Exception as e:
        print_error(f"Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        sys.exit(1)
