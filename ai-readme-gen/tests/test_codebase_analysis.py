"""Tests for codebase analysis functionality."""

import pytest
import tempfile
from pathlib import Path

from cli.analysis.codebase import scan_codebase, parse_python_file
from cli.analysis.extractor import extract_project_metadata, extract_api_endpoints


def create_test_project():
    """Create a temporary test project."""
    tmpdir = tempfile.mkdtemp()
    tmpdir = Path(tmpdir)

    # Create Python files
    (tmpdir / "main.py").write_text("""
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

    # Create requirements.txt
    (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
flask>=2.3.0
""")

    # Create simple README
    (tmpdir / "README.md").write_text("""
# Test Project

A simple test project for documentation generation.
""")

    return tmpdir


def test_scan_codebase():
    """Test codebase scanning."""
    project_path = create_test_project()
    try:
        result = scan_codebase(str(project_path))

        assert "files" in result
        assert "languages" in result
        assert "python" in result["languages"]
        assert len(result["languages"]["python"]["files"]) >= 1
        assert "directories" in result
        assert "root_files" in result
        assert "README.md" in result["root_files"]
    finally:
        import shutil
        shutil.rmtree(project_path)


def test_parse_python_file():
    """Test Python file parsing."""
    project_path = create_test_project()
    py_file = project_path / "main.py"
    try:
        result = parse_python_file(str(py_file))

        assert "functions" in result
        assert "classes" in result
        assert "hello_world" in [f["name"] for f in result["functions"]]
        assert len([c for c in result["classes"] if c["name"] == "Calculator"]) == 1
    finally:
        import shutil
        shutil.rmtree(project_path)


def test_extract_project_metadata():
    """Test project metadata extraction."""
    project_path = create_test_project()
    try:
        metadata = extract_project_metadata(str(project_path))

        # Note: metadata extraction reads README for name/description
        # but pyproject.toml is not found, so name comes from README
        assert metadata.get("name") is not None or metadata.get("description") is not None
    finally:
        import shutil
        shutil.rmtree(project_path)


def test_extract_api_endpoints():
    """Test API endpoint extraction."""
    tmpdir = tempfile.mkdtemp()
    try:
        tmpdir = Path(tmpdir)

        # Create a FastAPI app
        (tmpdir / "app.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return {"users": []}

@app.post("/users")
def create_user(user_data):
    return {"status": "created"}
""")

        endpoints = extract_api_endpoints(str(tmpdir))

        assert len(endpoints) >= 2
        paths = [ep["path"].strip('"\'') for ep in endpoints]
        assert "/users" in paths
    finally:
        import shutil
        shutil.rmtree(tmpdir)
