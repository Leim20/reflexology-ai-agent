"""
Configuration Loader
Loads and validates all configuration from config.json, .env, and prompts.yaml
"""

import json
import os
import yaml
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class Config:
    """
    Configuration manager for the chat agent

    Loads configuration from:
    - config/config.json (agent settings)
    - .env (environment variables with secrets)
    - config/prompts.yaml (system prompts)
    """

    def __init__(self, config_dir='config', env_file='.env'):
        """
        Initialize configuration loader

        Args:
            config_dir (str): Directory containing config files
            env_file (str): Path to .env file
        """
        logger.info("="*80)
        logger.info("INITIALIZING CONFIGURATION SYSTEM")
        logger.info("="*80)

        self.config_dir = config_dir
        self.env_file = env_file

        # Configuration storage
        self._config = {}
        self._env_vars = {}
        self._prompts = {}
        self._knowledge_base = ""

        # Load all configurations
        self._load_env()
        self._load_config_json()
        self._load_prompts()
        self._load_knowledge_base()

        logger.info("="*80)
        logger.info("CONFIGURATION LOADED SUCCESSFULLY")
        logger.info("="*80)

    def _load_env(self):
        """Load environment variables from .env file"""
        logger.info("Loading environment variables...")
        logger.debug(f"Looking for .env file at: {os.path.abspath(self.env_file)}")

        if not os.path.exists(self.env_file):
            logger.warning(f".env file not found at: {self.env_file}")
            logger.warning("Using environment variables from system only")
        else:
            load_dotenv(self.env_file)
            logger.info(f"✓ Loaded .env file from: {self.env_file}")

        # Load required environment variables
        required_env_vars = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'WHAPI_API_TOKEN': os.getenv('WHAPI_API_TOKEN'),
            'WHAPI_CHANNEL_ID': os.getenv('WHAPI_CHANNEL_ID'),
            'WEBHOOK_URL': os.getenv('WEBHOOK_URL'),
            'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY')
        }

        logger.debug("Checking environment variables:")
        for key, value in required_env_vars.items():
            if value and not value.startswith('{{'):
                # Mask sensitive values in logs
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                logger.debug(f"  ✓ {key}: {masked_value}")
                self._env_vars[key] = value
            else:
                logger.warning(f"  ✗ {key}: NOT SET or still has placeholder")
                self._env_vars[key] = None

        logger.info(f"Loaded {len([v for v in self._env_vars.values() if v])} environment variables")

    def _load_config_json(self):
        """Load main configuration from config.json"""
        config_file = os.path.join(self.config_dir, 'config.json')

        logger.info("Loading main configuration...")
        logger.debug(f"Config file path: {os.path.abspath(config_file)}")

        if not os.path.exists(config_file):
            raise ConfigurationError(f"Config file not found: {config_file}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)

            logger.info(f"✓ Loaded config.json successfully")
            logger.debug(f"Config keys: {list(self._config.keys())}")

            # Log key configuration values
            agent_name = self._config.get('agent', {}).get('name', 'Unknown')
            agent_role = self._config.get('agent', {}).get('role', 'Unknown')
            ai_model = self._config.get('ai', {}).get('model', 'Unknown')

            logger.info(f"  Agent Name: {agent_name}")
            logger.info(f"  Agent Role: {agent_role}")
            logger.info(f"  AI Model: {ai_model}")

            # Check for placeholders
            if '{{' in agent_name or '{{' in agent_role:
                logger.warning("⚠️  Config contains placeholders! Run setup_agent.py to configure.")

        except json.JSONDecodeError as e:
            logger.exception(f"Failed to parse config.json: {e}")
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            logger.exception(f"Error loading config.json: {e}")
            raise ConfigurationError(f"Failed to load config: {e}")

    def _load_prompts(self):
        """Load system prompts from TXT files or fallback to prompts.yaml"""
        prompts_dir = os.path.join(self.config_dir, "prompts")
        prompts_yaml = os.path.join(self.config_dir, "prompts.yaml")

        logger.info("Loading system prompts...")

        # Try loading from TXT files first
        if os.path.isdir(prompts_dir):
            logger.info(f"✓ Found prompts directory: {prompts_dir}")
            logger.info("Loading prompts from TXT files...")

            self._prompts = {"prompts": {}}
            txt_files = [f for f in os.listdir(prompts_dir) if f.endswith(".txt")]

            if txt_files:
                for txt_file in txt_files:
                    prompt_name = txt_file.replace(".txt", "")
                    txt_path = os.path.join(prompts_dir, txt_file)

                    try:
                        with open(txt_path, "r", encoding="utf-8") as f:
                            prompt_content = f.read()

                        self._prompts["prompts"][prompt_name] = prompt_content
                        logger.debug(f"  ✓ Loaded {txt_file} ({len(prompt_content):,} chars)")

                    except Exception as e:
                        logger.error(f"  ✗ Failed to load {txt_file}: {e}")

                logger.info(f"✓ Loaded {len(self._prompts.get('prompts', {}))} prompt(s) from TXT files")
                logger.info(f"  Available prompts: {list(self._prompts.get('prompts', {}).keys())}")
                return

        # Fallback to YAML if TXT files not found
        logger.info("TXT files not found, falling back to prompts.yaml...")
        logger.debug(f"Prompts file path: {os.path.abspath(prompts_yaml)}")

        if not os.path.exists(prompts_yaml):
            raise ConfigurationError(f"Prompts not found: neither {prompts_dir}/*.txt nor {prompts_yaml} exist")

        try:
            with open(prompts_yaml, "r", encoding="utf-8") as f:
                self._prompts = yaml.safe_load(f)

            logger.info(f"✓ Loaded prompts.yaml successfully")
            prompt_keys = list(self._prompts.get("prompts", {}).keys())
            logger.debug(f"Available prompts: {prompt_keys}")
            logger.info(f"  Found {len(prompt_keys)} prompt templates")

        except yaml.YAMLError as e:
            logger.exception(f"Failed to parse prompts.yaml: {e}")
            raise ConfigurationError(f"Invalid YAML in prompts file: {e}")
        except Exception as e:
            logger.exception(f"Error loading prompts.yaml: {e}")
            raise ConfigurationError(f"Failed to load prompts: {e}")

    def _load_knowledge_base(self):
        """Load knowledge base from configured path"""
        logger.info("Loading knowledge base...")

        kb_config = self._config.get('knowledge_base', {})
        if not kb_config.get('enabled', False):
            logger.warning("Knowledge base is DISABLED in config")
            return

        kb_path = kb_config.get('path', 'data/knowledge_base/catalog.txt')
        section_marker = kb_config.get('section_marker', '[CATALOG]')

        logger.debug(f"Knowledge base path: {os.path.abspath(kb_path)}")
        logger.debug(f"Section marker: {section_marker}")

        if not os.path.exists(kb_path):
            logger.warning(f"Knowledge base file not found: {kb_path}")

            # Try fallback to PDF
            if kb_config.get('fallback_to_pdf', False):
                logger.info("Attempting PDF fallback...")
                self._load_knowledge_from_pdf(kb_config.get('pdf_folder', 'data/knowledge_base/documents'))
            return

        try:
            with open(kb_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.debug(f"Read {len(content)} characters from knowledge base file")

            # Extract knowledge base section
            if section_marker in content:
                logger.debug(f"Found section marker: {section_marker}")
                start_idx = content.index(section_marker) + len(section_marker)
                remaining = content[start_idx:]

                # Find next section or end of file
                next_marker = remaining.find('\n[')
                if next_marker != -1:
                    self._knowledge_base = remaining[:next_marker].strip()
                else:
                    self._knowledge_base = remaining.strip()

                logger.info(f"✓ Loaded knowledge base ({len(self._knowledge_base)} chars)")
                logger.debug(f"Preview: {self._knowledge_base[:200]}...")
            else:
                # No section marker, use entire file
                logger.warning(f"Section marker '{section_marker}' not found, using entire file")
                self._knowledge_base = content.strip()
                logger.info(f"✓ Loaded entire file as knowledge base ({len(self._knowledge_base)} chars)")

        except Exception as e:
            logger.exception(f"Error loading knowledge base: {e}")
            logger.warning("Continuing without knowledge base")

    def _load_knowledge_from_pdf(self, pdf_folder):
        """Fallback: Load knowledge from PDF files"""
        logger.debug(f"Looking for PDFs in: {os.path.abspath(pdf_folder)}")

        if not os.path.exists(pdf_folder):
            logger.warning(f"PDF folder not found: {pdf_folder}")
            return

        pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
        logger.info(f"Found {len(pdf_files)} PDF files")

        if not pdf_files:
            logger.warning("No PDF files found for fallback")
            return

        # Import here to avoid circular dependency
        try:
            from handlers.tools.document import extract_from_pdf
            pdf_path = os.path.join(pdf_folder, pdf_files[0])
            logger.info(f"Attempting to load: {pdf_files[0]}")

            self._knowledge_base = extract_from_pdf(pdf_path)
            logger.info(f"✓ Loaded knowledge from PDF ({len(self._knowledge_base)} chars)")
        except Exception as e:
            logger.exception(f"Failed to load PDF: {e}")

    def get_prompt(self, prompt_name: str) -> str:
        """
        Get a system prompt by name, with variables substituted

        Args:
            prompt_name (str): Name of prompt (e.g., 'web_with_knowledge')

        Returns:
            str: Formatted prompt with variables substituted
        """
        logger.debug(f"Getting prompt: {prompt_name}")

        prompts = self._prompts.get('prompts', {})
        if prompt_name not in prompts:
            logger.error(f"Prompt '{prompt_name}' not found")
            logger.debug(f"Available prompts: {list(prompts.keys())}")
            return f"You are {self.get('agent.name', 'an assistant')}."

        prompt_template = prompts[prompt_name]

        # Substitute variables
        variables = {
            'AGENT_NAME': self.get('agent.name', 'Assistant'),
            'AGENT_ROLE': self.get('agent.role', 'helper'),
            'KNOWLEDGE_BASE': self._knowledge_base
        }

        logger.debug(f"Substituting variables: {list(variables.keys())}")

        prompt = prompt_template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            prompt = prompt.replace(placeholder, value)

        logger.debug(f"Prompt length after substitution: {len(prompt)} chars")
        return prompt

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key (str): Configuration key (e.g., 'agent.name', 'ai.model')
            default (Any): Default value if key not found

        Returns:
            Any: Configuration value
        """
        logger.debug(f"Getting config value: {key}")

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                logger.debug(f"Key '{key}' not found, using default: {default}")
                return default

        logger.debug(f"Config value for '{key}': {value}")
        return value

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable

        Args:
            key (str): Environment variable name
            default (str, optional): Default value

        Returns:
            str: Environment variable value
        """
        value = self._env_vars.get(key, default)
        if value is None:
            logger.warning(f"Environment variable '{key}' not set")
        return value

    @property
    def knowledge_base(self) -> str:
        """Get loaded knowledge base"""
        return self._knowledge_base

    @property
    def has_knowledge_base(self) -> bool:
        """Check if knowledge base is loaded"""
        return bool(self._knowledge_base)


# Global configuration instance
_config_instance: Optional[Config] = None


def load_config(config_dir='config', env_file='.env') -> Config:
    """
    Load global configuration

    Args:
        config_dir (str): Configuration directory
        env_file (str): Path to .env file

    Returns:
        Config: Configuration instance
    """
    global _config_instance

    if _config_instance is None:
        logger.info("Initializing global configuration...")
        _config_instance = Config(config_dir, env_file)
    else:
        logger.debug("Using existing configuration instance")

    return _config_instance


def get_config() -> Config:
    """
    Get global configuration instance

    Returns:
        Config: Configuration instance

    Raises:
        ConfigurationError: If configuration not loaded yet
    """
    if _config_instance is None:
        raise ConfigurationError("Configuration not loaded. Call load_config() first.")

    return _config_instance
