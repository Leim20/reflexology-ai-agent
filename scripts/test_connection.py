#!/usr/bin/env python3
"""
Test Connection Script
Tests API connections before deployment
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from openai import OpenAI
import requests


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def print_test(text):
    """Print test description"""
    print(f"\n🔍 {text}...")


def print_success(text):
    """Print success message"""
    print(f"   ✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"   ✗ {text}")


def print_info(text):
    """Print info message"""
    print(f"   ℹ {text}")


def test_environment_variables():
    """Test if environment variables are set"""
    print_header("TESTING ENVIRONMENT VARIABLES")

    load_dotenv()

    required_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY')
    }

    optional_vars = {
        'WHAPI_API_TOKEN': os.getenv('WHAPI_API_TOKEN'),
        'WHAPI_CHANNEL_ID': os.getenv('WHAPI_CHANNEL_ID'),
        'WEBHOOK_URL': os.getenv('WEBHOOK_URL')
    }

    all_ok = True

    print_test("Checking required environment variables")
    for var_name, var_value in required_vars.items():
        if var_value and not var_value.startswith('{{'):
            masked_value = f"{var_value[:8]}...{var_value[-4:]}" if len(var_value) > 12 else "***"
            print_success(f"{var_name}: {masked_value}")
        else:
            print_error(f"{var_name}: NOT SET or still has placeholder")
            all_ok = False

    print_test("Checking optional environment variables")
    for var_name, var_value in optional_vars.items():
        if var_value and not var_value.startswith('{{'):
            masked_value = f"{var_value[:8]}..." if len(var_value) > 12 else "***"
            print_success(f"{var_name}: {masked_value}")
        else:
            print_info(f"{var_name}: Not configured (optional)")

    return all_ok


def test_openai_connection():
    """Test OpenAI API connection"""
    print_header("TESTING OPENAI API CONNECTION")

    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key or openai_key.startswith('{{'):
        print_error("OpenAI API key not configured")
        return False

    try:
        print_test("Initializing OpenAI client")
        client = OpenAI(api_key=openai_key)
        print_success("Client initialized")

        print_test("Testing API with simple completion")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Connection test successful'"}],
            max_tokens=20
        )

        result = response.choices[0].message.content
        print_success(f"API Response: {result}")
        print_info(f"Tokens used: {response.usage.total_tokens}")

        return True

    except Exception as e:
        print_error(f"OpenAI API test failed: {str(e)}")
        return False


def test_whapi_connection():
    """Test Whapi API connection"""
    print_header("TESTING WHAPI API CONNECTION")

    whapi_token = os.getenv('WHAPI_API_TOKEN')

    if not whapi_token or whapi_token.startswith('{{'):
        print_info("Whapi API token not configured (skipping WhatsApp tests)")
        return True

    try:
        print_test("Testing Whapi API")
        url = "https://gate.whapi.cloud/settings"
        headers = {
            'Authorization': f'Bearer {whapi_token}'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        print_success("Whapi API connection successful")
        print_info(f"Account status: {data.get('status', 'Unknown')}")

        return True

    except Exception as e:
        print_error(f"Whapi API test failed: {str(e)}")
        return False


def test_configuration_files():
    """Test if configuration files are valid"""
    print_header("TESTING CONFIGURATION FILES")

    all_ok = True

    # Test config.json
    print_test("Checking config/config.json")
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        agent_name = config.get('agent', {}).get('name', '')
        if '{{' in agent_name:
            print_error("config.json still contains placeholders!")
            print_info("Run: python scripts/setup_agent.py")
            all_ok = False
        else:
            print_success(f"config.json valid (Agent: {agent_name})")

    except FileNotFoundError:
        print_error("config/config.json not found")
        all_ok = False
    except json.JSONDecodeError as e:
        print_error(f"config/config.json is not valid JSON: {e}")
        all_ok = False

    # Test prompts.yaml
    print_test("Checking config/prompts.yaml")
    try:
        import yaml
        with open('config/prompts.yaml', 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)
        print_success("prompts.yaml valid")
    except FileNotFoundError:
        print_error("config/prompts.yaml not found")
        all_ok = False
    except Exception as e:
        print_error(f"prompts.yaml error: {e}")
        all_ok = False

    # Test knowledge base
    print_test("Checking knowledge base")
    kb_path = 'data/knowledge_base/catalog.txt'
    if os.path.exists(kb_path):
        size = os.path.getsize(kb_path)
        if size > 100:
            print_success(f"Knowledge base exists ({size} bytes)")
        else:
            print_info("Knowledge base exists but is very small (might be empty)")
    else:
        print_error("Knowledge base not found")
        all_ok = False

    return all_ok


def test_dependencies():
    """Test if required Python packages are installed"""
    print_header("TESTING PYTHON DEPENDENCIES")

    required_packages = [
        ('flask', 'Flask'),
        ('openai', 'OpenAI'),
        ('dotenv', 'python-dotenv'),
        ('PyPDF2', 'PyPDF2'),
        ('docx', 'python-docx'),
        ('PIL', 'Pillow'),
        ('yaml', 'PyYAML'),
        ('requests', 'requests')
    ]

    all_ok = True

    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print_success(f"{package_name}")
        except ImportError:
            print_error(f"{package_name} - NOT INSTALLED")
            all_ok = False

    if not all_ok:
        print_info("\nInstall missing packages with:")
        print_info("pip install -r requirements.txt")

    return all_ok


def main():
    """Main test function"""
    print_header("CHAT AGENT - CONNECTION TESTS")

    print("This script will test:")
    print("  - Environment variables")
    print("  - Configuration files")
    print("  - Python dependencies")
    print("  - OpenAI API connection")
    print("  - Whapi API connection (if configured)")
    print()

    input("Press Enter to start tests...")

    results = {}

    # Run tests
    results['env'] = test_environment_variables()
    results['config'] = test_configuration_files()
    results['deps'] = test_dependencies()
    results['openai'] = test_openai_connection()
    results['whapi'] = test_whapi_connection()

    # Summary
    print_header("TEST SUMMARY")

    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():15} {status}")

    print("\n" + "="*80)

    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Your agent is ready to run.")
        print("\nStart the agent with:")
        print("  python web/app.py")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Please fix the issues above before running the agent.")
        print("\nCommon fixes:")
        print("  - Run setup: python scripts/setup_agent.py")
        print("  - Install deps: pip install -r requirements.txt")
        print("  - Check .env file has correct API keys")

    print("="*80 + "\n")

    return 0 if all_passed else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✗ Tests cancelled by user")
        sys.exit(1)
