# __init__.py

"""STIR Macro Analyst Agent - Initialization."""

import logging
import os

# Configure logging
loglevel = os.getenv("STIR_AGENT_LOG_LEVEL", "INFO")
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {loglevel}")

logger = logging.getLogger(__package__)
logger.setLevel(numeric_level)

# Model configuration
MODEL = os.getenv("OPENAI_MODEL")
if not MODEL:
    MODEL = "gpt-4o-mini"

# Validate required environment variables
if not os.getenv("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY not set in environment")

if not os.getenv("BBG_HOST"):
    logger.info("BBG_HOST not set, using default 'localhost'")

if not os.getenv("BBG_PORT"):
    logger.info("BBG_PORT not set, using default '8194'")

# Import agent after MODEL is defined
from . import agent  # noqa: E402

__all__ = ['agent', 'MODEL']