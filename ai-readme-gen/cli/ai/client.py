"""AI API client for interacting with LLM providers."""

import json
import os
from typing import Dict, Any, Optional, Union
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


def normalize_provider(provider: Union[AIProvider, str]) -> AIProvider:
    """
    Normalize provider input to AIProvider enum.

    Accepts both enum and string (CLI/env safe).
    """
    if isinstance(provider, AIProvider):
        return provider

    if isinstance(provider, str):
        try:
            return AIProvider(provider.lower())
        except ValueError:
            raise AIError(f"Unknown provider: {provider}")

    raise AIError(f"Invalid provider type: {type(provider)}")


def get_api_key(provider: AIProvider) -> Optional[str]:
    """Get API key from environment."""
    if provider == AIProvider.ANTHROPIC:
        return os.getenv("ANTHROPIC_API_KEY")
    elif provider == AIProvider.OPENAI:
        return os.getenv("OPENAI_API_KEY")
    return None


def get_model(provider: AIProvider) -> Optional[str]:
    """Get model name from environment."""
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
    import requests

    api_key = get_api_key(AIProvider.ANTHROPIC)
    if not api_key:
        raise AuthenticationError(
            "Anthropic API key not configured. Set ANTHROPIC_API_KEY."
        )

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

        if 400 <= response.status_code < 500:
            if response.status_code == 401:
                raise AuthenticationError("API key is invalid or missing.")
            raise APIError(f"Client error: {response.status_code}")

        return response.json()

    except requests.exceptions.Timeout:
        raise APIError("Request timed out")
    except requests.exceptions.HTTPError as e:
        # Check for 401 authentication errors, but safely handle cases where response is None
        if e.response is not None and e.response.status_code == 401:
            raise AuthenticationError("API key is invalid or missing.")
        raise APIError(f"API request failed: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"API request failed: {str(e)}")


def call_openai(
    messages: list,
    model: str = "gpt-4o",
    max_tokens: int = 4096
) -> Dict[str, Any]:
    import requests

    api_key = get_api_key(AIProvider.OPENAI)
    if not api_key:
        raise AuthenticationError(
            "OpenAI API key not configured. Set OPENAI_API_KEY."
        )

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

        if 400 <= response.status_code < 500:
            if response.status_code == 401:
                raise AuthenticationError("API key is invalid or missing.")
            raise APIError(f"Client error: {response.status_code}")

        return response.json()

    except requests.exceptions.Timeout:
        raise APIError("Request timed out")
    except requests.exceptions.HTTPError as e:
        # Check for 401 authentication errors, but safely handle cases where response is None
        if e.response is not None and e.response.status_code == 401:
            raise AuthenticationError("API key is invalid or missing.")
        raise APIError(f"API request failed: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"API request failed: {str(e)}")


def call_local_model(
    messages: list,
    model_path: str = "/path/to/model"
) -> Dict[str, Any]:
    raise AIError(
        "Local model support not yet implemented. Configure OLLAMA_BASE_URL."
    )


def call_ai_model(
    messages: list,
    provider: Union[AIProvider, str] = AIProvider.ANTHROPIC,
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    Main entry point for AI calls.
    Accepts enum OR string provider.
    """
    provider = normalize_provider(provider)

    if provider == AIProvider.ANTHROPIC:
        return call_anthropic(messages, max_tokens=max_tokens)
    elif provider == AIProvider.OPENAI:
        return call_openai(messages, max_tokens=max_tokens)
    elif provider == AIProvider.LOCAL:
        return call_local_model(messages)

    # Technically unreachable now, but safe guard
    raise AIError(f"Unknown provider: {provider}")


def extract_json_response(response: Dict[str, Any]) -> Optional[Any]:
    """Extract JSON from AI response."""
    try:
        if "content" in response:
            content = response["content"]
            if isinstance(content, list) and content:
                text = content[0].get("text", "")
                return json.loads(text)

        elif "choices" in response:
            text = response["choices"][0]["message"]["content"]
            return json.loads(text)

    except json.JSONDecodeError:
        pass

    import re
    match = re.search(r"\{[\s\S]*\}", str(response.get("content", "")))
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def stream_ai_response(
    messages: list,
    provider: Union[AIProvider, str] = AIProvider.ANTHROPIC,
    max_tokens: int = 4096
):
    """Stream AI responses."""
    provider = normalize_provider(provider)

    if provider == AIProvider.ANTHROPIC:
        import requests

        api_key = get_api_key(provider)
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

        with requests.post(
            url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        for block in data.get("content", []):
                            if block.get("type") == "text":
                                yield block.get("text", "")
                    except json.JSONDecodeError:
                        continue

    elif provider == AIProvider.OPENAI:
        import requests

        api_key = get_api_key(provider)
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

        with requests.post(
            url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
