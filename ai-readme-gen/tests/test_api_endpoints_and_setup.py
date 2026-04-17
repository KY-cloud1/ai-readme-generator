"""Unit tests for API endpoint and setup instructions extraction.

Tests the extract_api_endpoints and extract_setup_instructions functions from cli.analysis.extractor.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from cli.analysis.extractor import extract_api_endpoints, extract_setup_instructions


@pytest.fixture(scope="function")
def fastapi_project(tmp_path):
    """Create a FastAPI project for API endpoint testing."""
    (tmp_path / "app.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    return [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]

@app.post("/users")
async def create_user(user: dict):
    return {"status": "created"}

@app.get("/items")
async def get_items():
    return [{"id": 1, "name": "Item 1"}]
""")
    (tmp_path / "requirements.txt").write_text("""
fastapi>=0.100.0
uvicorn>=0.23.0
""")
    (tmp_path / "README.md").write_text("""
# FastAPI Project

A FastAPI project for API development.
""")
    return tmp_path


@pytest.fixture(scope="function")
def flask_project(tmp_path):
    """Create a Flask project for API endpoint testing."""
    (tmp_path / "app.py").write_text("""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World"

@app.route('/api/users')
def get_users():
    return {"users": []}

@app.route('/api/users', methods=['POST'])
def create_user():
    return {"status": "created"}
""")
    (tmp_path / "requirements.txt").write_text("""
flask>=2.3.0
requests>=2.28.0
""")
    (tmp_path / "README.md").write_text("""
# Flask Project

A Flask project for web development.
""")
    return tmp_path


@pytest.fixture(scope="function")
def empty_project(tmp_path):
    """Create an empty project for edge case testing."""
    return tmp_path


class TestExtractApiEndpoints:
    """Tests for API endpoint extraction."""

    def test_extract_api_endpoints_fastapi(self, fastapi_project):
        """Test API endpoint extraction from FastAPI project."""
        endpoints = extract_api_endpoints(str(fastapi_project))

        assert len(endpoints) >= 4, "Should extract at least 4 endpoints"
        paths = [ep["path"].strip('"\'') for ep in endpoints]
        assert "/users" in paths, "Should extract /users endpoint"
        assert "/items" in paths, "Should extract /items endpoint"

    def test_extract_api_endpoints_flask(self, flask_project):
        """Test API endpoint extraction from Flask project."""
        endpoints = extract_api_endpoints(str(flask_project))

        assert len(endpoints) >= 3, "Should extract at least 3 endpoints"
        paths = [ep["path"].strip('"\'') for ep in endpoints]
        assert "/" in paths, "Should extract root endpoint"
        assert "/api/users" in paths, "Should extract /api/users endpoint"

    def test_extract_api_endpoints_empty(self, empty_project):
        """Test API endpoint extraction from project without endpoints."""
        endpoints = extract_api_endpoints(str(empty_project))

        assert len(endpoints) == 0, "Should extract no endpoints from non-Flask project"

    def test_extract_api_endpoints_returns_list(self, fastapi_project):
        """Test that extract_api_endpoints returns a list."""
        endpoints = extract_api_endpoints(str(fastapi_project))
        assert isinstance(endpoints, list), "Should return a list"

    def test_extract_api_endpoints_endpoint_structure(self, fastapi_project):
        """Test that extracted endpoints have correct structure."""
        endpoints = extract_api_endpoints(str(fastapi_project))

        for endpoint in endpoints:
            assert "path" in endpoint, "Endpoint should have path"
            assert "method" in endpoint, "Endpoint should have method"
            assert isinstance(endpoint["path"], str), "Path should be a string"
            assert isinstance(endpoint["method"], str), "Method should be a string"

    def test_extract_api_endpoints_method_values(self, flask_project):
        """Test that extracted endpoint methods are correct."""
        endpoints = extract_api_endpoints(str(flask_project))

        methods = [ep["method"] for ep in endpoints]
        assert "GET" in methods, "Should have GET method"
        assert "POST" in methods, "Should have POST method"

    def test_extract_api_endpoints_path_values(self, flask_project):
        """Test that extracted endpoint paths are correct."""
        endpoints = extract_api_endpoints(str(flask_project))

        paths = [ep["path"] for ep in endpoints]
        assert any("/" in path for path in paths), "Should have paths with /"


class TestExtractSetupInstructions:
    """Tests for setup instructions extraction."""

    def test_extract_setup_instructions_basic(self, flask_project):
        """Test basic setup instructions extraction."""
        instructions = extract_setup_instructions(str(flask_project))

        assert "installation" in instructions, "Should contain installation instructions"
        assert "dependencies" in instructions, "Should contain dependencies section"
        # Should have extracted from requirements.txt
        # The implementation returns the full version strings like "requests>=2.28.0"
        assert "requests>=2.28.0" in instructions["dependencies"] or "flask>=2.3.0" in instructions["dependencies"]

    def test_extract_setup_instructions_empty(self, empty_project):
        """Test setup instructions extraction from empty project."""
        instructions = extract_setup_instructions(str(empty_project))

        assert "installation" in instructions, "Should still have installation section"
        # Should have default dependencies when none found
        assert "dependencies" in instructions, "Should have dependencies section"

    def test_extract_setup_instructions_returns_dict(self, flask_project):
        """Test that extract_setup_instructions returns a dictionary."""
        instructions = extract_setup_instructions(str(flask_project))
        assert isinstance(instructions, dict), "Should return a dictionary"

    def test_extract_setup_instructions_has_required_sections(self, flask_project):
        """Test that extract_setup_instructions returns all required sections."""
        instructions = extract_setup_instructions(str(flask_project))

        assert "installation" in instructions, "Should have installation section"
        assert "dependencies" in instructions, "Should have dependencies section"

    def test_extract_setup_instructions_dependencies_extracted(self, flask_project):
        """Test that dependencies are correctly extracted."""
        instructions = extract_setup_instructions(str(flask_project))

        deps = instructions["dependencies"]
        assert isinstance(deps, list), "Dependencies should be a list"
        # Check if any dependency contains flask or requests (handles version specifiers)
        assert any("flask" in d.lower() for d in deps) or any("requests" in d.lower() for d in deps), \
            "Should contain flask or requests in dependencies"

    def test_extract_setup_instructions_empty_project_has_defaults(self, empty_project):
        """Test that empty projects have default setup instructions."""
        instructions = extract_setup_instructions(str(empty_project))

        # Should still provide helpful installation instructions
        assert "installation" in instructions, "Should provide installation instructions"
        assert "dependencies" in instructions, "Should have dependencies section"

    def test_extract_setup_instructions_with_pyproject_toml(self, tmp_path):
        """Test setup instructions extraction with pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
dependencies = ["requests", "flask"]
""")
        (tmp_path / "README.md").write_text("""
# Test Project

A test project.
""")

        instructions = extract_setup_instructions(str(tmp_path))

        assert "installation" in instructions, "Should contain installation instructions"
        assert "dependencies" in instructions, "Should contain dependencies section"
