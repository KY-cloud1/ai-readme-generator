"""Unit tests for codebase scanning functionality.

Tests the scan_codebase function from cli.analysis.codebase module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from cli.analysis.codebase import scan_codebase


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
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
description = "A simple test project for documentation generation"
version = "1.0.0"
requires-python = ">= 3.9"
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
    "name": "test-js-project",
    "version": "1.0.0",
    "dependencies": {
        "express": "^4.18.0"
    }
}
""")
    return tmp_path


@pytest.fixture(scope="function")
def empty_project(tmp_path):
    """Create an empty project for edge case testing."""
    return tmp_path


class TestScanCodebase:
    """Tests for codebase scanning functionality."""

    def test_scan_codebase_basic(self, test_project):
        """Test that scan_codebase correctly scans a codebase."""
        result = scan_codebase(str(test_project))

        assert "files" in result, "Result should contain 'files' key"
        assert "languages" in result, "Result should contain 'languages' key"
        assert "directories" in result, "Result should contain 'directories' key"
        assert "root_files" in result, "Result should contain 'root_files' key"
        assert len(result["files"]) >= 2, "Should find at least 2 files"
        assert "python" in result["languages"], "Should detect Python language"
        assert "README.md" in result["root_files"], "Should find README.md in root files"

    def test_scan_codebase_empty(self, empty_project):
        """Test scanning an empty directory."""
        result = scan_codebase(str(empty_project))

        assert result["files"] == [], "Should return empty files list"
        assert result["languages"] == {}, "Should return empty languages dict"
        # Note: scan_codebase includes '.' in directories even for empty dirs
        assert isinstance(result["directories"], list), "Directories should be a list"
        assert result["root_files"] == [], "Should return empty root files list"

    def test_scan_codebase_js_project(self, js_project):
        """Test scanning a JavaScript project."""
        result = scan_codebase(str(js_project))

        assert "javascript" in result["languages"], "Should detect JavaScript language"
        assert len(result["files"]) >= 1, "Should find at least 1 file"

    def test_scan_codebase_with_specific_language(self, test_project):
        """Test scanning with specific language filter."""
        # Scan only Python files
        result = scan_codebase(str(test_project), ["python"])

        assert "python" in result["languages"], "Should detect Python language"
        # Should not have JavaScript language when filtering for Python
        assert "javascript" not in result["languages"], "Should not detect JavaScript when filtering for Python"

    def test_scan_codebase_with_multiple_languages(self, test_project):
        """Test scanning with multiple language filters."""
        result = scan_codebase(str(test_project), ["python", "javascript"])

        assert "python" in result["languages"], "Should detect Python language"
        # Should not have JavaScript language when not in filter
        assert "javascript" not in result["languages"], "Should not detect JavaScript when not in filter"

    def test_scan_codebase_nonexistent_directory(self):
        """Test scanning a nonexistent directory."""
        with pytest.raises(ValueError):
            scan_codebase("/nonexistent/directory")

    def test_scan_codebase_returns_dict(self, test_project):
        """Test that scan_codebase returns a dictionary."""
        result = scan_codebase(str(test_project))

        assert isinstance(result, dict), "Should return a dictionary"

    def test_scan_codebase_files_is_list(self, test_project):
        """Test that files key is a list."""
        result = scan_codebase(str(test_project))

        assert isinstance(result["files"], list), "Files should be a list"

    def test_scan_codebase_languages_is_dict(self, test_project):
        """Test that languages key is a dictionary."""
        result = scan_codebase(str(test_project))

        assert isinstance(result["languages"], dict), "Languages should be a dictionary"

    def test_scan_codebase_directories_is_list(self, test_project):
        """Test that directories key is a list."""
        result = scan_codebase(str(test_project))

        assert isinstance(result["directories"], list), "Directories should be a list"

    def test_scan_codebase_root_files_is_list(self, test_project):
        """Test that root_files key is a list."""
        result = scan_codebase(str(test_project))

        assert isinstance(result["root_files"], list), "Root files should be a list"

    def test_scan_codebase_detects_python_version(self, test_project):
        """Test that Python version is detected."""
        result = scan_codebase(str(test_project), ["python"])

        assert "version" in result["languages"]["python"], "Should detect Python version"
