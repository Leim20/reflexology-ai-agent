"""
Centralized Logging Configuration
Provides comprehensive debug and error logging for the entire application
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class AgentLogger:
    """
    Centralized logger for the chat agent application

    Features:
    - Console logging (INFO and above)
    - File logging (DEBUG and above) with rotation
    - Error-only logging for quick troubleshooting
    - Structured log formatting
    - Per-module logger instances
    """

    _loggers = {}
    _initialized = False
    _log_dir = 'logs'
    _log_level = logging.DEBUG

    @classmethod
    def setup(cls, log_dir='logs', log_level=logging.DEBUG, agent_name='ChatAgent'):
        """
        Initialize the logging system

        Args:
            log_dir (str): Directory for log files
            log_level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            agent_name (str): Agent name for log file naming
        """
        if cls._initialized:
            return

        cls._log_dir = log_dir
        cls._log_level = log_level

        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Generate log file names with date
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'{agent_name}_{date_str}.log')
        error_log_file = os.path.join(log_dir, f'{agent_name}_errors_{date_str}.log')

        # File handler formatter (detailed)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler formatter (concise)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )

        # File handler - All logs (DEBUG and above) with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        # Error file handler - Only errors
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)

        # Console handler - INFO and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)

        cls._initialized = True

        # Log initialization message
        root_logger.info("=" * 80)
        root_logger.info(f"{agent_name.upper()} - LOGGING SYSTEM INITIALIZED")
        root_logger.info("=" * 80)
        root_logger.info(f"Log Directory: {os.path.abspath(log_dir)}")
        root_logger.info(f"Main Log File: {log_file}")
        root_logger.info(f"Error Log File: {error_log_file}")
        root_logger.info(f"Log Level: {logging.getLevelName(log_level)}")
        root_logger.info("=" * 80)

    @classmethod
    def get_logger(cls, name):
        """
        Get a logger instance for a specific module

        Args:
            name (str): Module name (usually __name__)

        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._initialized:
            cls.setup()

        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger

        return cls._loggers[name]

    @classmethod
    def set_level(cls, level):
        """
        Change logging level at runtime

        Args:
            level (int): New logging level
        """
        cls._log_level = level
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(max(logging.INFO, level))


def get_logger(name):
    """
    Convenience function to get a logger instance

    Args:
        name (str): Module name (use __name__)

    Returns:
        logging.Logger: Configured logger instance

    Example:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.debug("Debug message")
        logger.info("Info message")
        logger.error("Error message")
    """
    return AgentLogger.get_logger(name)


def setup_logging(log_dir='logs', log_level=logging.DEBUG, agent_name='ChatAgent'):
    """
    Convenience function to setup logging

    Args:
        log_dir (str): Directory for log files
        log_level (int): Logging level
        agent_name (str): Agent name for log file naming
    """
    AgentLogger.setup(log_dir, log_level, agent_name)
