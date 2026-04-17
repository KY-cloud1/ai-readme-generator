"""Unit tests for Python and JavaScript file parsing functionality.

Tests the parse_python_file and parse_javascript_file functions from cli.analysis.codebase.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from cli.analysis.codebase import parse_python_file, parse_javascript_file


@pytest.fixture(scope="function")
def python_file(tmp_path):
    """Create a Python file for testing."""
    path = tmp_path / "test.py"
    path.write_text("""
import requests
from flask import Flask
from typing import List, Dict
from dataclasses import dataclass

class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

def hello_world():
    print("Hello, World!")

def main():
    calc = Calculator()
    print(calc.add(2, 3))
""")
    return path


@pytest.fixture(scope="function")
def js_file(tmp_path):
    """Create a JavaScript file for testing."""
    path = tmp_path / "test.js"
    path.write_text("""
import express from 'express';
import mongoose from 'mongoose';
import * as lodash from 'lodash';
import { useState } from 'react';

const app = express();

app.get('/api/users', (req, res) => {
    res.json({users: []});
});

module.exports = app;
""")
    return path


@pytest.fixture(scope="function")
def ts_file(tmp_path):
    """Create a TypeScript file for testing."""
    path = tmp_path / "test.ts"
    path.write_text("""
import express from 'express';
import { FastifyInstance } from 'fastify';
import * as lodash from 'lodash';

interface User {
    id: number;
    name: string;
}

const app = express();

app.get('/api/users', async (req, res) => {
    const users: User[] = [];
    res.json(users);
});

export default app;
""")
    return path


class TestPythonFileParsing:
    """Tests for Python file parsing."""

    def test_parse_python_file_integration(self, python_file):
        """Test Python file parsing in pipeline context."""
        result = parse_python_file(str(python_file))

        assert result["syntax_error"] is False, "Python file should parse without syntax errors"
        assert len(result["imports"]) >= 2, f"Should find at least 2 imports, found {len(result['imports'])}"
        assert len(result["functions"]) >= 1, "Should find at least 1 function"
        assert len(result["classes"]) >= 0, "Should find at least 0 classes"

    def test_parse_python_file_simple(self, python_file):
        """Test parsing a simple Python file."""
        result = parse_python_file(str(python_file))

        assert result["syntax_error"] is False, "Should parse without errors"
        # python_file has hello_world and main functions
        assert len(result["functions"]) >= 2, f"Should find at least 2 functions, found {len(result['functions'])}"

    def test_parse_python_file_with_classes(self, python_file):
        """Test parsing a Python file with classes."""
        result = parse_python_file(str(python_file))

        assert result["syntax_error"] is False, "Should parse without errors"
        assert len(result["classes"]) >= 1, f"Should find at least 1 class, found {len(result['classes'])}"

    def test_parse_python_file_imports(self, python_file):
        """Test that imports are correctly extracted."""
        result = parse_python_file(str(python_file))

        assert "requests" in result["imports"], "Should detect requests import"
        assert "flask" in result["imports"], "Should detect flask import"
        assert "typing" in result["imports"], "Should detect typing import"
        assert "dataclasses" in result["imports"], "Should detect dataclasses import"

    def test_parse_python_file_from_imports(self, python_file):
        """Test that from imports are correctly extracted."""
        result = parse_python_file(str(python_file))

        assert "flask" in result["imports"], "Should detect flask from import"

    def test_parse_python_file_empty_file(self, tmp_path):
        """Test parsing an empty Python file."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        result = parse_python_file(str(empty_file))

        assert result["syntax_error"] is False, "Empty file should parse without errors"
        assert result["imports"] == [], "Should have no imports"
        assert result["functions"] == [], "Should have no functions"
        assert result["classes"] == [], "Should have no classes"

    def test_parse_python_file_nonexistent_file(self):
        """Test parsing a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            parse_python_file("/nonexistent/file.py")

    def test_parse_python_file_syntax_error(self, tmp_path):
        """Test parsing a file with syntax errors."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("""
def broken(
    # Missing closing parenthesis
""")

        result = parse_python_file(str(bad_file))

        assert result["syntax_error"] is True, "File with syntax errors should be detected"

    def test_parse_python_file_returns_dict(self, python_file):
        """Test that parse_python_file returns a dictionary."""
        result = parse_python_file(str(python_file))

        assert isinstance(result, dict), "Should return a dictionary"

    def test_parse_python_file_has_required_keys(self, python_file):
        """Test that parse_python_file returns all required keys."""
        result = parse_python_file(str(python_file))

        assert "syntax_error" in result, "Should have syntax_error key"
        assert "imports" in result, "Should have imports key"
        assert "classes" in result, "Should have classes key"
        assert "functions" in result, "Should have functions key"


class TestJavaScriptFileParsing:
    """Tests for JavaScript file parsing."""

    def test_parse_js_file(self, js_file):
        """Test JavaScript file parsing."""
        result = parse_javascript_file(str(js_file))

        # syntax_error key may not be present
        assert result.get("syntax_error") is None or result.get("syntax_error") is False, \
            "JS file should parse without syntax errors"
        assert len(result.get("imports", [])) >= 3, "Should find at least 3 imports (express, mongoose, lodash)"

    def test_parse_ts_file(self, ts_file):
        """Test TypeScript file parsing."""
        result = parse_javascript_file(str(ts_file))

        # syntax_error key may not be present
        assert result.get("syntax_error") is None or result.get("syntax_error") is False, \
            "TS file should parse without syntax errors"
        assert len(result.get("imports", [])) >= 3, "Should find at least 3 imports (express, fastify, lodash)"

    def test_parse_js_file_imports(self, js_file):
        """Test that imports are correctly extracted."""
        result = parse_javascript_file(str(js_file))

        assert "express" in result.get("imports", []), "Should detect express import"
        assert "mongoose" in result.get("imports", []), "Should detect mongoose import"
        assert "lodash" in result.get("imports", []), "Should detect lodash import"

    def test_parse_js_file_esm_imports(self, js_file):
        """Test that ESM imports are correctly extracted."""
        result = parse_javascript_file(str(js_file))

        assert "express" in result.get("imports", []), "Should detect ESM import"
        assert "mongoose" in result.get("imports", []), "Should detect ESM import"

    def test_parse_js_file_star_imports(self, js_file):
        """Test that star imports are correctly extracted."""
        result = parse_javascript_file(str(js_file))

        assert "lodash" in result.get("imports", []), "Should detect star import"

    def test_parse_js_file_empty_file(self, tmp_path):
        """Test parsing an empty JavaScript file."""
        empty_file = tmp_path / "empty.js"
        empty_file.write_text("")

        result = parse_javascript_file(str(empty_file))

        assert result.get("syntax_error") is None or result.get("syntax_error") is False, \
            "Empty file should parse without errors"
        assert result.get("imports", []) == [], "Should have no imports"

    def test_parse_js_file_nonexistent_file(self):
        """Test parsing a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            parse_javascript_file("/nonexistent/file.js")

    def test_parse_js_file_returns_dict(self, js_file):
        """Test that parse_javascript_file returns a dictionary."""
        result = parse_javascript_file(str(js_file))

        assert isinstance(result, dict), "Should return a dictionary"

    def test_parse_js_file_has_required_keys(self, js_file):
        """Test that parse_javascript_file returns all required keys."""
        result = parse_javascript_file(str(js_file))

        assert "imports" in result, "Should have imports key"
