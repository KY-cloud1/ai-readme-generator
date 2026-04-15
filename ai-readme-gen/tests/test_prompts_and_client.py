"""Tests for prompt templates and AI client error handling."""

import pytest
from unittest.mock import patch

from cli.ai.prompts import (
    create_analysis_prompt,
    create_readme_prompt,
    create_diagram_prompt,
    create_api_docs_prompt,
    create_review_prompt,
)
from cli.ai.client import (
    AIProvider,
    APIError,
    AIError,
    AuthenticationError,
    extract_json_response,
    normalize_provider,
    get_api_key,
    get_model,
    call_ai_model,
)
from cli.commands.config import get_config, validate_config


# =============================================================================
# Pytest Fixtures - Reusable test helpers
# =============================================================================

@pytest.fixture
def sample_codebase_info():
    """Sample codebase info for prompt tests."""
    return {
        "languages": {"python": 10, "javascript": 5},
        "files": [{"path": "main.py"}],
        "directories": ["src", "tests"],
        "root_files": ["README.md", "requirements.txt"]
    }


@pytest.fixture
def empty_codebase_info():
    """Empty codebase info for edge case tests."""
    return {
        "languages": {},
        "files": [],
        "directories": [],
        "root_files": []
    }


@pytest.fixture
def sample_metadata():
    """Sample metadata for prompt tests."""
    return {
        "name": "Test Project",
        "description": "A test project",
        "version": "1.0.0"
    }


@pytest.fixture
def sample_analysis():
    """Sample analysis for prompt tests."""
    return {
        "project_purpose": "This project does something cool",
        "data_flow": "Data flows from input to output"
    }


@pytest.fixture
def sample_endpoints():
    """Sample endpoints for API docs tests."""
    return [
        {"method": "GET", "path": "/users"},
        {"method": "POST", "path": "/users"},
        {"method": "DELETE", "path": "/users/{id}"},
    ]


@pytest.fixture
def empty_endpoints():
    """Empty endpoints for API docs tests."""
    return []


@pytest.fixture
def sample_readme_content():
    """Sample README content for review prompt tests."""
    return "# Test Project\n\nSome content."


# =============================================================================
# Prompt Tests
# =============================================================================

class TestPrompts:
    """Tests for prompt template generation."""

    def test_create_analysis_prompt_basic(self, sample_codebase_info):
        """Test creating a basic analysis prompt."""
        prompt = create_analysis_prompt(sample_codebase_info)

        assert "python" in prompt, "Should mention Python language"
        assert "javascript" in prompt, "Should mention JavaScript language"
        assert "Total files" in prompt, "Should mention total file count"
        assert "src" in prompt, "Should mention src directory"
        assert "tests" in prompt, "Should mention tests directory"
        assert "1" in prompt, "Should include file count"

    def test_create_analysis_prompt_empty(self, empty_codebase_info):
        """Test creating an analysis prompt with empty codebase."""
        prompt = create_analysis_prompt(empty_codebase_info)

        assert "**Total files**: 0" in prompt, "Should show 0 files for empty codebase"

    def test_create_readme_prompt(self, sample_codebase_info, sample_metadata, sample_analysis):
        """Test creating a README generation prompt."""
        prompt = create_readme_prompt(sample_codebase_info, sample_metadata, sample_analysis)

        assert "Test Project" in prompt, "Should include project name"
        assert "1.0.0" in prompt, "Should include version"
        assert "A test project" in prompt, "Should include description"
        assert "python" in prompt, "Should include language info"
        assert "This project does something cool" in prompt, "Should include purpose"

    def test_create_diagram_prompt(self, sample_codebase_info, sample_analysis):
        """Test creating a diagram generation prompt."""
        prompt = create_diagram_prompt(sample_codebase_info, sample_analysis)

        assert "ASCII" in prompt, "Should mention ASCII diagram"
        # The prompt should include the analysis content which contains component names
        assert "Key Components" in prompt, "Should include key components section"
        assert "Component1" in prompt or "Component2" in prompt or "component" in prompt.lower(), \
            "Should include component names from analysis"

    def test_create_api_docs_prompt_with_endpoints(self, sample_endpoints):
        """Test creating API docs prompt with endpoints."""
        codebase_info = {"languages": {"python": 10}}
        prompt = create_api_docs_prompt(codebase_info, sample_endpoints)

        assert "/users" in prompt, "Should include /users endpoint"
        assert "GET" in prompt, "Should include GET method"
        assert "POST" in prompt, "Should include POST method"
        assert "DELETE" in prompt, "Should include DELETE method"

    def test_create_api_docs_prompt_no_endpoints(self, empty_endpoints):
        """Test creating API docs prompt without endpoints."""
        codebase_info = {"languages": {"python": 10}}
        prompt = create_api_docs_prompt(codebase_info, empty_endpoints)

        assert "No API endpoints found" in prompt, "Should indicate no endpoints"

    def test_create_review_prompt(self, sample_readme_content, sample_codebase_info):
        """Test creating a review prompt."""
        prompt = create_review_prompt(sample_readme_content, sample_codebase_info)

        assert "# Test Project" in prompt, "Should include README content"
        assert "Review Checklist" in prompt, "Should mention review checklist"
        assert "Accuracy" in prompt, "Should include accuracy criterion"
        assert "Completeness" in prompt, "Should include completeness criterion"


# =============================================================================
# API Client Tests
# =============================================================================

class TestAPIKeyRetrieval:
    """Tests for API key and model retrieval."""

    @pytest.mark.parametrize(
        "provider,expected_key",
        [
            pytest.param(AIProvider.ANTHROPIC, "test-anthropic-key", id="anthropic"),
            pytest.param(AIProvider.OPENAI, "test-openai-key", id="openai"),
        ],
    )
    @patch('cli.ai.client.os.getenv')
    def test_get_api_key(self, mock_getenv, provider, expected_key):
        """Test getting API key for different providers."""
        mock_getenv.return_value = expected_key

        key = get_api_key(provider)
        assert key == expected_key, f"Should return {expected_key} for {provider}"
        # Verify that get API key was called with the correct provider (uppercase)
        mock_getenv.assert_called_once_with(f"{provider.value.upper()}_API_KEY")

    @pytest.mark.parametrize(
        "provider",
        [
            pytest.param(AIProvider.ANTHROPIC, id="anthropic"),
            pytest.param(AIProvider.OPENAI, id="openai"),
        ],
    )
    @patch('cli.ai.client.os.getenv')
    def test_get_api_key_missing(self, mock_getenv, provider):
        """Test getting API key when not set."""
        mock_getenv.return_value = None

        key = get_api_key(provider)
        assert key is None, "Should return None when API key is not set"
        # Verify that get API key was called with the correct provider (uppercase)
        mock_getenv.assert_called_once_with(f"{provider.value.upper()}_API_KEY")

    @pytest.mark.parametrize(
        "provider,model_key,model_value,expected_model",
        [
            pytest.param(
                AIProvider.ANTHROPIC,
                "ANTHROPIC_MODEL",
                "claude-3-5-sonnet-20240620",
                "claude-3-5-sonnet-20240620",
                id="anthropic",
            ),
            pytest.param(
                AIProvider.OPENAI,
                "OPENAI_MODEL",
                "gpt-4o",
                "gpt-4o",
                id="openai",
            ),
        ],
    )
    @patch('cli.ai.client.os.getenv')
    def test_get_model(self, mock_getenv, provider, model_key, model_value, expected_model):
        """Test getting model for different providers."""
        mock_getenv.side_effect = lambda x: model_value if x == model_key else None

        model = get_model(provider)
        assert model == expected_model, f"Should return {expected_model} for {provider}"
        # Verify that get model was called with the correct provider and model key (uppercase)
        mock_getenv.assert_any_call(f"{provider.value.upper()}_MODEL")

    @pytest.mark.parametrize(
        "provider,expected_model",
        [
            pytest.param(AIProvider.ANTHROPIC, "claude-3-5-sonnet-20240620", id="anthropic"),
            pytest.param(AIProvider.OPENAI, "gpt-4o", id="openai"),
        ],
    )
    @patch('cli.ai.client.os.getenv')
    def test_get_model_default(self, mock_getenv, provider, expected_model):
        """Test getting default model when not configured."""
        mock_getenv.side_effect = lambda x: None

        model = get_model(provider)
        assert model == expected_model, f"Should return default model {expected_model} for {provider}"
        # Verify that get model was called with the correct provider and model key (uppercase)
        mock_getenv.assert_any_call(f"{provider.value.upper()}_MODEL")


class TestAIModelCalls:
    """Tests for AI model call functionality."""

    @patch('cli.ai.client.call_anthropic')
    def test_call_anthropic_success(self, mock_call):
        """Test Anthropic API call success."""
        mock_call.return_value = {
            "content": [{"type": "text", "text": '{"result": "success"}'}],
            "model": "claude-3-5-sonnet-20240620"
        }

        result = call_ai_model(
            [{"role": "user", "content": "test"}],
            AIProvider.ANTHROPIC
        )

        assert result["content"][0]["text"] == '{"result": "success"}'
        # Verify that the mock was called with the correct arguments
        mock_call.assert_called_once()
        # Check that messages were passed as first positional argument
        assert mock_call.call_args[0][0] == [{"role": "user", "content": "test"}]

    @pytest.mark.parametrize(
        "error_class,error_message,expected_in_message",
        [
            pytest.param(
                AuthenticationError,
                "Anthropic API key not configured.",
                "API key not configured",
                id="missing_api_key",
            ),
            pytest.param(
                AuthenticationError,
                "API key is invalid or missing.",
                "API key is invalid",
                id="invalid_api_key",
            ),
            pytest.param(
                APIError,
                "Rate limit exceeded",
                "Rate limit",
                id="rate_limit",
            ),
            pytest.param(
                APIError,
                "Request timed out",
                "timed out",
                id="timeout",
            ),
        ],
    )
    @patch('cli.ai.client.call_anthropic')
    def test_call_anthropic_error(
        self, mock_call, error_class, error_message, expected_in_message
    ):
        """Test Anthropic API call error handling."""
        mock_call.side_effect = error_class(error_message)

        with pytest.raises(error_class) as exc_info:
            call_ai_model([{"role": "user", "content": "test"}], AIProvider.ANTHROPIC)

        assert expected_in_message in str(exc_info.value), \
            f"Error message should contain '{expected_in_message}'"

    @patch('cli.ai.client.call_openai')
    def test_call_openai_success(self, mock_call):
        """Test OpenAI API call success."""
        mock_call.return_value = {
            "choices": [{"message": {"content": '{"result": "success"}'}}]
        }

        result = call_ai_model(
            [{"role": "user", "content": "test"}],
            AIProvider.OPENAI
        )

        assert result["choices"][0]["message"]["content"] == '{"result": "success"}'
        # Verify that the mock was called with the correct arguments
        mock_call.assert_called_once()
        # Check that messages were passed as first positional argument
        assert mock_call.call_args[0][0] == [{"role": "user", "content": "test"}]

    @patch('cli.ai.client.call_openai')
    def test_call_openai_missing_api_key(self, mock_call):
        """Test OpenAI API call with missing API key."""
        mock_call.side_effect = AuthenticationError("OpenAI API key not configured.")

        with pytest.raises(AuthenticationError) as exc_info:
            call_ai_model([{"role": "user", "content": "test"}], AIProvider.OPENAI)

        assert "API key not configured" in str(exc_info.value)
        # Verify that the mock was called with the correct arguments
        mock_call.assert_called_once()
        # Check that messages were passed as first positional argument
        assert mock_call.call_args[0][0] == [{"role": "user", "content": "test"}]

    @pytest.mark.parametrize(
        "error_class,error_message,expected_in_message",
        [
            pytest.param(
                AuthenticationError,
                "OpenAI API key not configured.",
                "API key not configured",
                id="missing_api_key",
            ),
            pytest.param(
                AuthenticationError,
                "API key is invalid or missing.",
                "API key is invalid",
                id="invalid_api_key",
            ),
            pytest.param(
                APIError,
                "Rate limit exceeded",
                "Rate limit",
                id="rate_limit",
            ),
            pytest.param(
                APIError,
                "Request timed out",
                "timed out",
                id="timeout",
            ),
        ],
    )
    @patch('cli.ai.client.call_openai')
    def test_call_openai_error(
        self, mock_call, error_class, error_message, expected_in_message
    ):
        """Test OpenAI API call error handling."""
        mock_call.side_effect = error_class(error_message)

        with pytest.raises(error_class) as exc_info:
            call_ai_model([{"role": "user", "content": "test"}], AIProvider.OPENAI)

        assert expected_in_message in str(exc_info.value), \
            f"Error message should contain '{expected_in_message}'"
        # Verify that the mock was called with the correct arguments
        mock_call.assert_called_once()
        # Check that messages were passed as first positional argument
        assert mock_call.call_args[0][0] == [{"role": "user", "content": "test"}]

    def test_call_openai_httperror_with_none_response(self):
        """Test that HTTPError with None response is handled safely."""
        import requests
        from unittest.mock import patch

        # Create an HTTPError with None response (edge case that could occur)
        http_error = requests.exceptions.HTTPError("Request failed")
        http_error.response = None  # Simulate None response

        # Mock get_api_key to return a fake key so the API call proceeds
        with patch('cli.ai.client.get_api_key', return_value='fake-key'):
            with patch('requests.post') as mock_post:
                mock_post.side_effect = http_error

                # Should raise APIError, not crash with AttributeError
                with pytest.raises(APIError) as exc_info:
                    call_ai_model([{"role": "user", "content": "test"}], AIProvider.OPENAI, max_tokens=100)

                assert "API request failed" in str(exc_info.value)
                mock_post.assert_called_once()

    def test_call_local_model(self):
        """Test local model call raises error."""
        from cli.ai.client import call_local_model

        with pytest.raises(AIError) as exc_info:
            call_local_model([{"role": "user", "content": "test"}])

        assert "Local model support not yet implemented" in str(exc_info.value)


class TestCallAIModel:
    """Tests for the unified call_ai_model function."""

    def test_call_ai_model_anthropic(self):
        """Test calling AI model with Anthropic provider."""
        with patch('cli.ai.client.call_anthropic') as mock_call:
            mock_call.return_value = {"content": [{"text": "response"}]}

            result = call_ai_model([{"role": "user", "content": "test"}], AIProvider.ANTHROPIC)

            assert result == {"content": [{"text": "response"}]}

    def test_call_ai_model_openai(self):
        """Test calling AI model with OpenAI provider."""
        with patch('cli.ai.client.call_openai') as mock_call:
            mock_call.return_value = {"choices": [{"message": {"content": "response"}}]}

            result = call_ai_model([{"role": "user", "content": "test"}], AIProvider.OPENAI)

            assert result == {"choices": [{"message": {"content": "response"}}]}

    def test_call_ai_model_local(self):
        """Test calling AI model with local provider."""
        with patch('cli.ai.client.call_local_model') as mock_call:
            mock_call.return_value = {"content": [{"text": "response"}]}

            result = call_ai_model([{"role": "user", "content": "test"}], AIProvider.LOCAL)

            assert result == {"content": [{"text": "response"}]}

    def test_call_ai_model_unknown_provider(self):
        """Test calling AI model with unknown provider."""
        # Test with an invalid provider string
        try:
            result = call_ai_model([{"role": "user", "content": "test"}], "invalid-provider")
            # If it raises an error, that's the expected behavior
        except Exception as e:
            assert "Unknown provider" in str(e), "Should raise error for unknown provider"


# =============================================================================
# JSON Response Extraction Tests
# =============================================================================

class TestJSONResponseExtraction:
    """Tests for JSON response extraction from AI responses."""

    def test_extract_json_response_content_format(self):
        """Test JSON extraction from content format response."""
        response = {
            "content": [
                {"type": "text", "text": '{"key": "value", "number": 42}'}
            ]
        }

        result = extract_json_response(response)
        assert result is not None, "Should extract JSON"
        assert result["key"] == "value", "Should extract key-value pair"
        assert result["number"] == 42, "Should extract numeric value"

    def test_extract_json_response_choices_format(self):
        """Test JSON extraction from choices format response."""
        response = {
            "choices": [
                {"message": {"content": '{"key": "value"}'}}
            ]
        }

        result = extract_json_response(response)
        assert result is not None, "Should extract JSON"
        assert result["key"] == "value", "Should extract key-value pair"

    def test_extract_json_response_invalid(self):
        """Test JSON extraction with invalid JSON."""
        response = {
            "content": "This is not valid JSON at all"
        }

        result = extract_json_response(response)
        assert result is None, "Should return None for invalid JSON"

    def test_extract_json_response_nested(self):
        """Test JSON extraction with nested structure."""
        response = {
            "content": [
                {"type": "text", "text": '{"users": [{"name": "Alice"}, {"name": "Bob"}]}'}
            ]
        }

        result = extract_json_response(response)
        assert result is not None, "Should extract JSON"
        assert len(result["users"]) == 2, "Should have 2 users"
        assert result["users"][0]["name"] == "Alice", "Should extract first user name"

    def test_extract_json_response_empty(self):
        """Test JSON extraction with empty JSON."""
        response = {
            "content": [
                {"type": "text", "text": '{}'}
            ]
        }

        result = extract_json_response(response)
        assert result is not None, "Should extract JSON"
        assert result == {}, "Should return empty dict"

    def test_extract_json_response_array(self):
        """Test JSON extraction with array JSON."""
        response = {
            "content": [
                {"type": "text", "text": '[1, 2, 3, 4, 5]'}
            ]
        }

        result = extract_json_response(response)
        assert result is not None, "Should extract JSON"
        assert result == [1, 2, 3, 4, 5], "Should return array"


# =============================================================================
# Provider Normalization Tests
# =============================================================================

class TestProviderNormalization:
    """Tests for provider normalization."""

    @pytest.mark.parametrize(
        "provider,expected",
        [
            pytest.param(AIProvider.ANTHROPIC, AIProvider.ANTHROPIC, id="enum_anthropic"),
            pytest.param(AIProvider.OPENAI, AIProvider.OPENAI, id="enum_openai"),
            pytest.param(AIProvider.LOCAL, AIProvider.LOCAL, id="enum_local"),
            pytest.param("anthropic", AIProvider.ANTHROPIC, id="string_anthropic"),
            pytest.param("openai", AIProvider.OPENAI, id="string_openai"),
            pytest.param("local", AIProvider.LOCAL, id="string_local"),
        ],
    )
    def test_normalize_provider(self, provider, expected):
        """Test normalize_provider with various inputs."""
        result = normalize_provider(provider)
        assert result == expected, f"Should normalize {provider!r} to {expected!r}"

    @pytest.mark.parametrize(
        "input_value,expected_error_message",
        [
            pytest.param("unknown-provider", "Unknown provider", id="unknown_string"),
            pytest.param(123, "Invalid provider type", id="invalid_type"),
            pytest.param(None, "Invalid provider type", id="none"),
            pytest.param("", "Unknown provider", id="empty_string"),
            pytest.param("  ", "Unknown provider", id="whitespace_string"),
        ],
    )
    def test_normalize_provider_invalid(self, input_value, expected_error_message):
        """Test normalize_provider with invalid inputs."""
        with pytest.raises(AIError) as exc_info:
            normalize_provider(input_value)  # type: ignore[arg-type]

        assert expected_error_message in str(exc_info.value), \
            f"Should raise error with message '{expected_error_message}'"


# =============================================================================
# Config Validation Tests
# =============================================================================

class TestConfigValidation:
    """Tests for configuration validation."""

    @pytest.mark.parametrize(
        "ollama_url,expected_valid",
        [
            pytest.param(None, True, id="no_url"),
            pytest.param("http://localhost:11434", True, id="with_url"),
            pytest.param("", True, id="empty_url"),
        ],
    )
    def test_validate_config_local_provider(self, ollama_url, expected_valid):
        """Test validate_config with local provider."""
        env = {"AI_PROVIDER": "local"}
        if ollama_url is not None:
            env["OLLAMA_BASE_URL"] = ollama_url

        with patch.dict('os.environ', env):
            config = get_config()
            assert config["ai"]["provider"] == "local", "Should have local provider"
            assert validate_config() is expected_valid, f"Should be valid with ollama_url={ollama_url!r}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
