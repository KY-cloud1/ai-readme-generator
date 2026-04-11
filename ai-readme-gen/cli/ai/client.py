"""AI API client for interacting with LLM providers."""

import os
from typing import Dict, Any, Optional
from enum import Enum


class AIModel(Enum):
    """Supported AI models."""
    ANTHROPIC_CLAUDE_3_5 = "claude-3-5-sonnet-20240620"
    ANTHROPIC_CLAUDE_3 = "claude-3-sonnet-20240229"
    OPENAI_GPT_4O = "gpt-4o"
    OPENAI_GPT_4O_MINI = "gpt-4o-mini"
    LOCAL = "local"


class AIProvider(Enum):
    """Supported AI providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"


class AIError(Exception):
    """Base exception for AI errors."""
    pass


class APIError(AIError):
    """Exception for API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(AIError):
    """Exception for rate limit errors."""
    pass


class AuthenticationError(AIError):
    """Exception for authentication errors."""
    pass


def get_api_key(provider: AIProvider) -> Optional[str]:
    """
    Get API key for a provider from environment variables.

    Args:
        provider: The AI provider

    Returns:
        API key string or None if not configured
    """
    if provider == AIProvider.ANTHROPIC:
        return os.getenv("ANTHROPIC_API_KEY")
    elif provider == AIProvider.OPENAI:
        return os.getenv("OPENAI_API_KEY")
    return None


def get_model(provider: AIProvider) -> Optional[str]:
    """
    Get model name for a provider from environment variables.

    Args:
        provider: The AI provider

    Returns:
        Model name string or None if not configured
    """
    if provider == AIProvider.ANTHROPIC:
        return os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-20240620"
    elif provider == AIProvider.OPENAI:
        return os.getenv("OPENAI_MODEL") or "gpt-4o"
    return None


def call_anthropic(
    messages: list,
    model: str = "claude-3-5-sonnet-20240620",
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    Call Anthropic API.

    Args:
        messages: List of message dictionaries
        model: Model to use
        max_tokens: Maximum tokens to generate

    Returns:
        Response dictionary

    Raises:
        APIError: If API call fails
        AuthenticationError: If API key is missing
    """
    import requests
    import json

    api_key = get_api_key(AIProvider.ANTHROPIC)
    if not api_key:
        raise AuthenticationError("Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        # Check for 4xx client errors before calling raise_for_status()
        if response.status_code >= 400 and response.status_code < 500:
            if response.status_code == 401:
                raise AuthenticationError("API key is invalid or missing. Please check your API key configuration.")
            raise APIError(f"Client error: {response.status_code} - {response.text}")

        return response.json()
    except requests.exceptions.Timeout:
        raise APIError("Request timed out")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            raise AuthenticationError("API key is invalid or missing. Please check your API key configuration.")
        raise APIError(f"API request failed: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"API request failed: {str(e)}")


def call_openai(
    messages: list,
    model: str = "gpt-4o",
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    Call OpenAI API.

    Args:
        messages: List of message dictionaries
        model: Model to use
        max_tokens: Maximum tokens to generate

    Returns:
        Response dictionary

    Raises:
        APIError: If API call fails
        AuthenticationError: If API key is missing
    """
    import requests
    import json

    api_key = get_api_key(AIProvider.OPENAI)
    if not api_key:
        raise AuthenticationError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        # Check for 4xx client errors before calling raise_for_status()
        if response.status_code >= 400 and response.status_code < 500:
            if response.status_code == 401:
                raise AuthenticationError("API key is invalid or missing. Please check your API key configuration.")
            raise APIError(f"Client error: {response.status_code} - {response.text}")

        return response.json()
    except requests.exceptions.Timeout:
        raise APIError("Request timed out")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            raise AuthenticationError("API key is invalid or missing. Please check your API key configuration.")
        raise APIError(f"API request failed: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"API request failed: {str(e)}")


def call_local_model(
    messages: list,
    model_path: str = "/path/to/model"
) -> Dict[str, Any]:
    """
    Call a local model (placeholder for local model integration).

    Args:
        messages: List of message dictionaries
        model_path: Path to the local model

    Returns:
        Response dictionary (placeholder implementation)

    Raises:
        AIError: If local model is not configured
    """
    raise AIError("Local model support not yet implemented. Configure OLLAMA_BASE_URL for local models.")


def call_ai_model(
    messages: list,
    provider: AIProvider = AIProvider.ANTHROPIC,
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    Call an AI model based on provider configuration.

    Args:
        messages: List of message dictionaries
        provider: AI provider to use
        max_tokens: Maximum tokens to generate

    Returns:
        Response dictionary

    Raises:
        AIError: If provider is not configured or call fails
    """
    if provider == AIProvider.ANTHROPIC:
        return call_anthropic(messages, max_tokens=max_tokens)
    elif provider == AIProvider.OPENAI:
        return call_openai(messages, max_tokens=max_tokens)
    elif provider == AIProvider.LOCAL:
        return call_local_model(messages)
    else:
        raise AIError(f"Unknown provider: {provider}")


def extract_json_response(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract JSON response from AI response.

    Args:
        response: AI API response

    Returns:
        Parsed JSON dictionary or None if extraction fails
    """
    try:
        if "content" in response:
            content = response["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                return json.loads(text)
        elif "choices" in response:
            choice = response["choices"][0]
            text = choice.get("message", {}).get("content", "")
            return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the text
    import re
    json_match = re.search(r'\{[\s\S]*\}', response.get("content", "") or "")
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


def stream_ai_response(
    messages: list,
    provider: AIProvider = AIProvider.ANTHROPIC,
    max_tokens: int = 4096
):
    """
    Stream AI response token by token.

    Args:
        messages: List of message dictionaries
        provider: AI provider to use
        max_tokens: Maximum tokens to generate

    Yields:
        Individual tokens or chunks of text
    """
    if provider == AIProvider.ANTHROPIC:
        import requests

        api_key = get_api_key(AIProvider.ANTHROPIC)
        if not api_key:
            raise AuthenticationError("Anthropic API key not configured.")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": max_tokens,
            "messages": messages,
            "stream": True,
        }

        with requests.post(url, json=payload, headers=headers, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue  # Skip malformed JSON lines
                    if "content" in data:
                        for block in data["content"]:
                            if block.get("type") == "text":
                                yield block.get("text", "")

    elif provider == AIProvider.OPENAI:
        import requests

        api_key = get_api_key(AIProvider.OPENAI)
        if not api_key:
            raise AuthenticationError("OpenAI API key not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": True,
        }

        with requests.post(url, json=payload, headers=headers, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "choices" in data and data["choices"]:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
