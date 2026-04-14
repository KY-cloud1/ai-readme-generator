"""Configuration handling for the CLI."""

import os
from typing import Dict


def get_config() -> Dict[str, Dict[str, str]]:
    """
    Get current configuration from environment variables.

    Returns:
        Dictionary of configuration sections with their values
    """
    config = {
        "ai": {
            "provider": os.getenv("AI_PROVIDER", "anthropic").lower(),
            "model": os.getenv("AI_MODEL", "claude-3-5-sonnet-20240620"),
        },
        "api": {
            "anthropic_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "openai_key": os.getenv("OPENAI_API_KEY", ""),
        },
        "output": {
            "format": os.getenv("OUTPUT_FORMAT", "text"),
            "timeout": os.getenv("TIMEOUT", "300"),
        },
    }

    return config


def set_config(config: Dict[str, Dict[str, str]]) -> None:
    """
    Set configuration in environment variables.

    Args:
        config: Configuration dictionary
    """
    if "ai" in config:
        os.environ["AI_PROVIDER"] = config["ai"].get("provider", "anthropic")
        os.environ["AI_MODEL"] = config["ai"].get("model", "claude-3-5-sonnet-20240620")

    if "api" in config:
        os.environ["ANTHROPIC_API_KEY"] = config["api"].get("anthropic_key", "")
        os.environ["OPENAI_API_KEY"] = config["api"].get("openai_key", "")

    if "output" in config:
        os.environ["OUTPUT_FORMAT"] = config["output"].get("format", "text")
        os.environ["TIMEOUT"] = config["output"].get("timeout", "300")


def validate_config() -> bool:
    """
    Validate that required configuration is present.

    Returns:
        True if configuration is valid, False otherwise
    """
    config = get_config()
    provider = config["ai"]["provider"]

    if provider == "anthropic":
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    elif provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    elif provider == "local":
        # Local provider doesn't require API keys
        # Optional: check for OLLAMA_BASE_URL if configured
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_url:
            return bool(ollama_url)
        return True
    return True
