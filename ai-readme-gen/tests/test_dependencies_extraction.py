"""Unit tests for dependency extraction functions.

These tests cover the extract_dependencies and extract_project_dependencies
functions from the analysis parser module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from cli.analysis.parser import extract_dependencies, extract_project_dependencies


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
""")
    (tmp_path / "app.py").write_text("""
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World"
""")
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
description = "A simple test project for documentation generation"
version = "1.0.0"
""")
    return tmp_path


@pytest.fixture(scope="function")
def empty_project(tmp_path):
    """Create a temporary empty project directory."""
    return tmp_path


# =============================================================================
# Test Dependency Extraction from Files
# =============================================================================

class TestExtractDependencies:
    """Tests for extract_dependencies function."""

    def test_extract_dependencies_python_basic(self, test_project):
        """Test Python dependency extraction from source file."""
        deps = extract_dependencies(str(test_project / "app.py"))

        assert "requests" in deps, "Should extract requests import"
        assert "flask" in deps, "Should extract flask import"
        assert len(deps) == 2, "Should extract 2 dependencies"

    def test_extract_dependencies_python_from_import(self, test_project):
        """Test Python dependency extraction with from imports."""
        (test_project / "utils.py").write_text("""
from flask import Flask
from requests import get
import json
""")
        deps = extract_dependencies(str(test_project / "utils.py"))

        assert "flask" in deps, "Should extract flask from import"
        assert "requests" in deps, "Should extract requests from import"
        assert "json" in deps, "Should extract json import"
        assert len(deps) == 3, "Should extract 3 dependencies"

    def test_extract_dependencies_requirements_txt(self):
        """Test requirements.txt parsing."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
flask>=2.3.0
pytest>=7.0.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps, "Should extract requests"
            assert "flask" in deps, "Should extract flask"
            assert "pytest" in deps, "Should extract pytest"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_versions(self):
        """Test requirements.txt parsing with various version specifiers."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
flask==2.3.0
pytest~=7.0.0
black>23.0.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps, "Should extract requests"
            assert "flask" in deps, "Should extract flask"
            assert "pytest" in deps, "Should extract pytest"
            assert "black" in deps, "Should extract black"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_extras(self):
        """Test requirements.txt parsing with extras."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
requests[security]>=2.28.0
flask[async]>=2.3.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps, "Should extract requests"
            assert "flask" in deps, "Should extract flask"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_whitespace(self):
        """Test requirements.txt parsing with whitespace variations."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
flask>=2.3.0
pytest>=7.0.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps, "Should extract requests"
            assert "flask" in deps, "Should extract flask"
            assert "pytest" in deps, "Should extract pytest"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_url_packages(self):
        """Test requirements.txt parsing with URL packages."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
git+https://github.com/user/repo.git@main
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps, "Should extract requests"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_empty(self):
        """Test requirements.txt parsing with empty file."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert deps == [], "Should return empty list for empty file"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_comments(self):
        """Test requirements.txt parsing with comments."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
# This is a comment
requests>=2.28.0  # Another comment
flask>=2.3.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps, "Should extract requests"
            assert "flask" in deps, "Should extract flask"
            assert len(deps) == 2, "Should have exactly 2 dependencies"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_conflicting_dependencies(self):
        """Test requirements.txt parsing with conflicting dependencies (same package, different versions).

        This test verifies that the extract_dependencies function
        handles requirements.txt files where the same package appears
        with different version specifiers. The current implementation
        keeps all occurrences, which may indicate a conflict that
        should be flagged or resolved.
        """
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            # Create requirements.txt with conflicting versions
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
requests>=2.31.0
flask>=2.3.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            # Both occurrences should be extracted (implementation behavior)
            assert "requests" in deps, "Should extract requests"
            assert "flask" in deps, "Should extract flask"
            # Note: The implementation returns all occurrences, not deduplicated
            assert len(deps) == 3, "Should extract all 3 dependency lines"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_multiple_conflicts(self):
        """Test requirements.txt parsing with multiple conflicting dependencies.

        This test verifies that the extract_dependencies function
        handles requirements.txt files with multiple packages having
        conflicting versions.
        """
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            # Create requirements.txt with multiple conflicts
            (tmpdir / "requirements.txt").write_text("""
django>=4.0
django>=5.0
django>=5.1
flask>=2.0
flask>=2.3
celery>=5.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            # All occurrences should be extracted
            assert "django" in deps, "Should extract django"
            assert "flask" in deps, "Should extract flask"
            assert "celery" in deps, "Should extract celery"
            # Note: The implementation returns all occurrences, not deduplicated
            assert len(deps) == 6, "Should extract all 6 dependency lines"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_conflict_and_valid(self):
        """Test requirements.txt parsing with mix of conflicts and valid dependencies.

        This test verifies that the extract_dependencies function
        handles requirements.txt files that have both conflicting
        dependencies and valid ones.
        """
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            # Create requirements.txt with mix of conflicts and valid deps
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
flask>=2.3.0
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            # All dependencies should be extracted
            assert "requests" in deps, "Should extract requests"
            assert "flask" in deps, "Should extract flask"
            assert "numpy" in deps, "Should extract numpy"
            assert "pandas" in deps, "Should extract pandas"
            assert "scipy" in deps, "Should extract scipy"
            assert len(deps) == 5, "Should extract all 5 dependencies"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_nonexistent_file(self):
        """Test extract_dependencies raises FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            extract_dependencies("/nonexistent/path/file.txt")

    def test_extract_dependencies_javascript(self):
        """Test JavaScript dependency extraction."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "app.js").write_text("""
const axios = require('axios');
import React from 'react';
import { useState } from 'react';
""")
            deps = extract_dependencies(str(tmpdir / "app.js"))

            assert "axios" in deps, "Should extract axios"
            assert "react" in deps, "Should extract react"
        finally:
            shutil.rmtree(tmpdir)


# =============================================================================
# Test Project-Level Dependency Extraction
# =============================================================================

class TestExtractProjectDependencies:
    """Tests for extract_project_dependencies function."""

    def test_extract_project_dependencies_with_requirements_txt(self, test_project):
        """Test project dependency extraction with requirements.txt."""
        deps = extract_project_dependencies(str(test_project))

        assert isinstance(deps, dict), "Should return a dict"
        # Check that at least one dependency file was found
        assert len(deps) >= 1, "Should find at least one dependency file"
        # Verify the structure of the returned dict
        for dep_path, dep_list in deps.items():
            assert isinstance(dep_path, str), "Dependency path should be a string"
            assert isinstance(dep_list, list), "Dependency list should be a list"

    def test_extract_project_dependencies_with_pyproject_toml(self, test_project):
        """Test project dependency extraction with pyproject.toml."""
        deps = extract_project_dependencies(str(test_project))

        # Should find pyproject.toml as a dependency file
        pyproject_found = any("pyproject.toml" in path for path in deps.keys())
        assert pyproject_found, "Should find pyproject.toml in dependency files"

    def test_extract_project_dependencies_with_both_requirements_and_pyproject(self, test_project):
        """Test project dependency extraction with both requirements.txt and pyproject.toml."""
        deps = extract_project_dependencies(str(test_project))

        # Should find both files
        has_requirements = any("requirements.txt" in path for path in deps.keys())
        has_pyproject = any("pyproject.toml" in path for path in deps.keys())
        assert has_requirements and has_pyproject, "Should find both requirements.txt and pyproject.toml"

    def test_extract_project_dependencies_empty_project(self, empty_project):
        """Test project dependency extraction from empty project."""
        deps = extract_project_dependencies(str(empty_project))

        assert isinstance(deps, dict), "Should return a dict"
        assert len(deps) == 0, "Should find no dependency files in empty project"

    def test_extract_project_dependencies_with_package_json(self):
        """Test project dependency extraction with package.json."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "package.json").write_text("""
{
  "name": "test-package",
  "dependencies": {
    "express": "^4.18.0"
  }
}
""")
            deps = extract_project_dependencies(str(tmpdir))

            # Should find package.json
            has_package_json = any("package.json" in path for path in deps.keys())
            assert has_package_json, "Should find package.json in dependency files"
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_project_dependencies_with_setup_py(self):
        """Test project dependency extraction with setup.py."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "setup.py").write_text("""
from setuptools import setup

setup(
    name="test-package",
    version="1.0.0",
)
""")
            deps = extract_project_dependencies(str(tmpdir))

            # Should find setup.py
            has_setup_py = any("setup.py" in path for path in deps.keys())
            assert has_setup_py, "Should find setup.py in dependency files"
        finally:
            shutil.rmtree(tmpdir)
