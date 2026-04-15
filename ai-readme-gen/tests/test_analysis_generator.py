"""Unit tests for the documentation generation module.

These tests cover individual generator functions:
- generate_readme
- generate_diagram
- generate_api_docs
- generate_setup_instructions
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from cli.analysis.codebase import scan_codebase
from cli.analysis.extractor import extract_project_metadata
from cli.commands.generate import (
    generate_readme,
    generate_diagram,
    generate_api_docs,
    generate_setup_instructions,
)
from cli.ai.client import AuthenticationError


# =============================================================================
# Pytest Fixtures - Reusable test helpers
# =============================================================================

@pytest.fixture(scope="function")
def test_project(tmp_path):
    """Create a temporary test project with realistic structure."""
    (tmp_path / "main.py").write_text("""
def hello_world():
    print("Hello, World!")

class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

def main():
    calc = Calculator()
    print(calc.add(2, 3))
""")
    (tmp_path / "requirements.txt").write_text("""
requests>=2.28.0
flask>=2.3.0
""")
    (tmp_path / "README.md").write_text("""
# Test Project

A simple test project for documentation generation.

This project demonstrates basic Python functionality.
""")
    (tmp_path / "app.py").write_text("""
import requests
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
    # Add pyproject.toml for metadata extraction
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
description = "A simple test project for documentation generation"
version = "1.0.0"
""")
    return tmp_path


@pytest.fixture(scope="function")
def js_project(tmp_path):
    """Create a JavaScript project for JS parsing tests."""
    (tmp_path / "index.js").write_text("""
import express from 'express';
import mongoose from 'mongoose';
import * as lodash from 'lodash';

const app = express();

app.get('/api/users', (req, res) => {
    res.json({users: []});
});

module.exports = app;
""")
    (tmp_path / "package.json").write_text("""
{
  "name": "js-project",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0",
    "mongoose": "^7.0.0"
  }
}
""")
    return tmp_path


# =============================================================================
# Test Classes
# =============================================================================

class TestReadmeGeneration:
    """Tests for README generation."""

    def test_readme_generation_with_metadata(self, test_project):
        """Test README generation with full metadata."""
        codebase_info = scan_codebase(str(test_project))
        metadata = extract_project_metadata(str(test_project))

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            readme = generate_readme(codebase_info, metadata)

        assert "# " in readme, "README should have title"
        assert "Test Project" in readme, "README should contain project name"
        assert "description" in readme.lower() or "no description" in readme.lower(), \
            "README should contain description"

    def test_readme_generation_empty_codebase(self):
        """Test README generation with empty codebase."""
        codebase_info = {
            "files": [],
            "languages": {},
            "root_files": [],
            "directories": [],
        }
        metadata = {
            "name": "Empty Project",
            "description": "",
            "version": "1.0.0",
        }

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            readme = generate_readme(codebase_info, metadata)

        assert "# " in readme, "README should have title"
        assert "Empty Project" in readme, "README should contain project name"

    def test_readme_generation_with_entry_points(self, test_project):
        """Test README generation with entry points detected."""
        codebase_info = scan_codebase(str(test_project))
        metadata = extract_project_metadata(str(test_project))

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            readme = generate_readme(codebase_info, metadata)

        assert "Test Project" in readme, "README should contain project name"
        assert "# " in readme, "README should have title"


class TestDiagramGeneration:
    """Tests for diagram generation."""

    def test_diagram_generation_with_codebase(self, test_project):
        """Test diagram generation with codebase info."""
        codebase_info = scan_codebase(str(test_project))

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            diagram = generate_diagram(codebase_info)

        assert "```" in diagram, "Diagram should have code block markers"
        assert "Basic ASCII Diagram" in diagram, "Diagram should have ASCII marker"
        assert "python" in diagram.lower(), "Diagram should mention python"

    def test_diagram_generation_empty_codebase(self):
        """Test diagram generation with empty codebase."""
        codebase_info = {
            "files": [],
            "languages": {},
            "root_files": [],
            "directories": [],
        }

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            diagram = generate_diagram(codebase_info)

        assert "```" in diagram, "Diagram should have code block markers"
        assert len(diagram) > 0, "Diagram should not be empty"

    def test_diagram_generation_with_js_project(self, js_project):
        """Test diagram generation with JavaScript project."""
        codebase_info = scan_codebase(str(js_project))

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            diagram = generate_diagram(codebase_info)

        assert "```" in diagram, "Diagram should have code block markers"
        assert "javascript" in diagram.lower() or "js" in diagram.lower(), \
            "Diagram should mention javascript or js"


class TestApiDocsGeneration:
    """Tests for API documentation generation."""

    def test_api_docs_generation_with_endpoints(self):
        """Test API docs generation with actual endpoints."""
        endpoints = [
            {"method": "GET", "path": "/users"},
            {"method": "POST", "path": "/users"},
            {"method": "GET", "path": "/users/{id}"},
        ]

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            api_docs = generate_api_docs({}, endpoints)

        assert "API Reference" in api_docs, "API docs should have reference section"
        assert len(api_docs) > 0, "API docs should not be empty"
        assert "GET" in api_docs, "Should mention GET method"
        assert "POST" in api_docs, "Should mention POST method"

    def test_api_docs_generation_empty_endpoints(self):
        """Test API docs generation with no endpoints."""
        # Empty endpoints list raises ValueError
        with pytest.raises(ValueError, match="endpoints cannot be empty"):
            generate_api_docs({}, [])

    def test_api_docs_generation_with_complex_endpoints(self):
        """Test API docs generation with complex endpoint paths."""
        endpoints = [
            {"method": "GET", "path": "/api/v1/users/{user_id}/posts/{post_id}"},
            {"method": "POST", "path": "/api/v1/posts"},
            {"method": "PUT", "path": "/api/v1/posts/{post_id}"},
            {"method": "DELETE", "path": "/api/v1/posts/{post_id}"},
        ]

        with patch('cli.commands.generate.call_ai_model') as mock_call:
            mock_call.side_effect = AuthenticationError("No API key configured")
            api_docs = generate_api_docs({}, endpoints)

        assert "API Reference" in api_docs, "Should have API reference section"
        assert "GET" in api_docs, "Should mention GET method"
        assert "POST" in api_docs, "Should mention POST method"
        assert "PUT" in api_docs, "Should mention PUT method"
        assert "DELETE" in api_docs, "Should mention DELETE method"


class TestSetupInstructionsGeneration:
    """Tests for setup instructions generation."""

    def test_setup_instructions_generation_basic(self, test_project):
        """Test basic setup instructions generation."""
        codebase_info = scan_codebase(str(test_project))
        metadata = extract_project_metadata(str(test_project))

        setup = generate_setup_instructions(str(Path(test_project)))

        assert "Setup Instructions" in setup, "Should have setup instructions header"
        assert "dependencies" in setup.lower(), "Should have dependencies section"

    def test_setup_instructions_generation_with_python(self, test_project):
        """Test setup instructions generation for Python project."""
        setup = generate_setup_instructions(str(Path(test_project)))

        assert "python" in setup.lower(), "Should mention Python"
        # The implementation uses "**python:**" format
        assert "**python:**" in setup or "python:" in setup.lower(), \
            "Should mention pip install or Python"

    def test_setup_instructions_generation_with_js(self, js_project):
        """Test setup instructions generation for JavaScript project."""
        # JS projects without requirements.txt will have minimal output
        # since the setup instructions generator looks for requirements.txt
        setup = generate_setup_instructions(str(Path(js_project)))

        # Should still have a header
        assert "Setup Instructions" in setup, "Should have setup instructions header"
        # Should have some content even for empty projects
        assert len(setup) > 0, "Should not be empty"

    def test_setup_instructions_generation_empty_codebase(self):
        """Test setup instructions generation with empty codebase."""
        codebase_info = {
            "files": [],
            "languages": {},
            "root_files": [],
            "directories": [],
        }

        setup = generate_setup_instructions(str(codebase_info))

        assert "Setup Instructions" in setup, "Should have setup instructions header"
        assert len(setup) > 0, "Should not be empty"
