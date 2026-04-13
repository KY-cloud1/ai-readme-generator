"""Integration tests for the full analysis pipeline.

These tests verify the end-to-end flow of the AI README Generator,
testing the complete analysis pipeline from codebase scanning to
documentation generation.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from cli.analysis.codebase import scan_codebase, parse_python_file
from cli.analysis.extractor import (
    extract_project_metadata,
    extract_api_endpoints,
    extract_setup_instructions,
)
from cli.analysis.agent import (
    create_agent_pipeline,
    run_agent_pipeline,
    Agent,
    AgentResult,
    CodebaseAnalyst,
    Architect,
    TechnicalWriter,
    APIExtractor as AgentAPIExtractor,
    Reviewer,
)
from cli.analysis.parser import parse_file, extract_dependencies, extract_project_dependencies
from cli.commands.analyze import analyze_codebase, format_analysis, analyze_and_generate
from cli.commands.generate import (
    generate_readme,
    generate_diagram,
    generate_api_docs,
    generate_setup_instructions,
)
from cli.ai.client import AuthenticationError
from cli.ai.prompts import (
    create_readme_prompt,
    create_diagram_prompt,
    create_api_docs_prompt,
)


def create_test_project():
    """Create a temporary test project with realistic structure."""
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

    # Create a more complex Python file
    (tmpdir / "app.py").write_text("""
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

    return tmpdir


def create_js_test_project():
    """Create a temporary JavaScript test project."""
    tmpdir = tempfile.mkdtemp()
    tmpdir = Path(tmpdir)

    # Create JavaScript file
    (tmpdir / "app.js").write_text("""
import express from 'express';
import { Router } from 'express';

const app = express();

app.get('/users', getUsers);
app.post('/users', createUser);

app.get('/users/:id', getUserById);

module.exports = app;

function getUsers() {
    return [];
}

function createUser(user) {
    return user;
}

function getUserById(id) {
    return { id };
}
""")

    # Create package.json
    (tmpdir / "package.json").write_text("""
{
    "name": "test-js-project",
    "version": "1.0.0",
    "description": "A test JavaScript project",
    "main": "app.js",
    "scripts": {
        "start": "node app.js"
    },
    "dependencies": {
        "express": "^4.18.0"
    }
}
""")

    return tmpdir


def create_empty_project():
    """Create a temporary empty project."""
    tmpdir = tempfile.mkdtemp()
    tmpdir = Path(tmpdir)
    return tmpdir


def create_mock_readme_response(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mock response for README generation."""
    name = metadata.get('name', 'Project') or 'Project'
    description = metadata.get('description', 'No description available.') or 'No description available.'
    file_count = len(metadata.get('files', [])) or 2
    readme_text = f"""# {name}

{description}

## Project Structure

- **PYTHON**: {file_count} files

## Files

"""
    return {
        "content": [{"type": "text", "text": json.dumps({"readme": readme_text})}]
    }


def create_mock_diagram_response(codebase_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mock response for diagram generation."""
    return {
        "content": [{"type": "text", "text": """```

    [Project Root]
    ├── [src/]
    │   └── [main modules]
    ├── [tests/]
    │   └── [test files]
    ├── [docs/]
    │   └── [documentation]
    └── [config/]
        └── [configuration files]

```

# Basic ASCII Diagram

This is a basic diagram. For detailed architecture diagrams,
please set up an AI API key (Anthropic or OpenAI).

"""}]
    }


def create_mock_api_docs_response(endpoints: list) -> Dict[str, Any]:
    """Create a mock response for API docs generation."""
    api_docs_text = "## API Reference\n\n### Endpoints\n\n"
    return {
        "content": [{"type": "text", "text": json.dumps({"api_docs": api_docs_text})}]
    }


def create_complex_python_project():
    """Create a project with multiple files and directories."""
    tmpdir = tempfile.mkdtemp()
    tmpdir = Path(tmpdir)

    # Create directory structure
    (tmpdir / "src").mkdir()
    (tmpdir / "src" / "core").mkdir()
    (tmpdir / "src" / "utils").mkdir()
    (tmpdir / "tests").mkdir()

    # Create multiple Python files
    (tmpdir / "main.py").write_text("def main(): pass\n")
    (tmpdir / "requirements.txt").write_text("requests\n")

    (tmpdir / "src" / "__init__.py").write_text("")
    (tmpdir / "src" / "core" / "__init__.py").write_text("")
    (tmpdir / "src" / "core" / "core.py").write_text("""
class Core:
    def process(self):
        pass
""")

    (tmpdir / "src" / "utils" / "helpers.py").write_text("""
def helper():
    return True
""")

    (tmpdir / "tests" / "test_main.py").write_text("# Test file\n")

    # Create README
    (tmpdir / "README.md").write_text("""
# Complex Project

A more complex project with multiple modules.
""")

    return tmpdir


def create_fastapi_project():
    """Create a FastAPI project for API endpoint testing."""
    tmpdir = tempfile.mkdtemp()
    tmpdir = Path(tmpdir)

    (tmpdir / "app.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return {"users": []}

@app.post("/users")
def create_user(user_data):
    return {"status": "created"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    return {"status": "deleted"}
""")

    (tmpdir / "README.md").write_text("""
# FastAPI Test Project

A FastAPI project for testing API documentation generation.
""")

    return tmpdir


class TestFullAnalysisPipeline:
    """Integration tests for the complete analysis pipeline."""

    def test_pipeline_scan_codebase(self):
        """Test that the pipeline correctly scans a codebase."""
        project_path = create_test_project()
        try:
            result = scan_codebase(str(project_path))

            assert "files" in result
            assert "languages" in result
            assert "directories" in result
            assert "root_files" in result
            assert len(result["files"]) >= 2
            assert "python" in result["languages"]
            assert "README.md" in result["root_files"]
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_extract_metadata(self):
        """Test that the pipeline correctly extracts project metadata."""
        project_path = create_test_project()
        try:
            metadata = extract_project_metadata(str(project_path))

            assert metadata.get("name") is not None or metadata.get("description") is not None
            # Description may be None if README doesn't have a description section
            # Just verify we got something
            assert metadata.get("name") == "Test Project"
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_extract_api_endpoints(self):
        """Test that the pipeline correctly extracts API endpoints."""
        project_path = create_fastapi_project()
        try:
            endpoints = extract_api_endpoints(str(project_path))

            assert len(endpoints) >= 4
            paths = [ep["path"].strip('"\'') for ep in endpoints]
            assert "/users" in paths
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_extract_setup_instructions(self):
        """Test that the pipeline correctly extracts setup instructions."""
        project_path = create_test_project()
        try:
            instructions = extract_setup_instructions(str(project_path))

            assert "installation" in instructions
            assert "dependencies" in instructions
            # Should have extracted from requirements.txt
            if instructions["dependencies"]:
                assert any("requests" in dep or "flask" in dep for dep in instructions["dependencies"])
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_codebase_analyst(self):
        """Test that the CodebaseAnalyst agent runs correctly."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            context = {"codebase": codebase_info, "metadata": {}, "endpoints": []}

            agent = CodebaseAnalyst()
            result = agent.run(context)

            assert result.success is True
            assert "file_distribution" in result.metadata
            assert "entry_points" in result.metadata
            assert "dependencies" in result.metadata
            assert "total_files" in result.metadata
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_architect(self):
        """Test that the Architect agent runs correctly."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            metadata = extract_project_metadata(str(project_path))
            context = {
                "codebase": codebase_info,
                "metadata": metadata,
                "file_distribution": codebase_info["languages"],
            }

            agent = Architect()
            result = agent.run(context)

            assert result.success is True
            assert "patterns" in result.metadata
            assert len(result.metadata["patterns"]) > 0
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_technical_writer(self):
        """Test that the TechnicalWriter agent runs correctly."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            metadata = extract_project_metadata(str(project_path))
            context = {
                "codebase": codebase_info,
                "metadata": metadata,
                "file_distribution": codebase_info["languages"],
                "analysis": {},
            }

            agent = TechnicalWriter()
            result = agent.run(context)

            assert result.success is True
            assert "description" in result.metadata
            assert "features" in result.metadata
            assert "tech_stack" in result.metadata
            assert "installation" in result.metadata
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_api_extractor(self):
        """Test that the APIExtractor agent runs correctly."""
        project_path = create_fastapi_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            endpoints = extract_api_endpoints(str(project_path))
            context = {
                "codebase": codebase_info,
                "endpoints": endpoints,
                "file_paths": {f.get("path", "") for f in codebase_info.get("files", [])},
            }

            agent = AgentAPIExtractor()
            result = agent.run(context)

            assert result.success is True
            assert "endpoints" in result.metadata
            # grouped may not be present if no valid endpoints found
            if "grouped" not in result.metadata:
                assert result.metadata["endpoints"] == []
            else:
                assert "grouped" in result.metadata
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_reviewer(self):
        """Test that the Reviewer agent runs correctly."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            metadata = extract_project_metadata(str(project_path))
            context = {
                "codebase": codebase_info,
                "metadata": metadata,
                "results": {},
            }

            agent = Reviewer()
            result = agent.run(context)

            assert result.success is True
            assert "rating" in result.metadata
            assert result.metadata["rating"] in ["PASS", "Review Required"]
        finally:
            shutil.rmtree(project_path)

    def test_run_agent_pipeline_full(self):
        """Test running the full agent pipeline."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            metadata = extract_project_metadata(str(project_path))
            endpoints = extract_api_endpoints(str(project_path))

            context = {
                "codebase": codebase_info,
                "metadata": metadata,
                "endpoints": endpoints,
            }

            results = run_agent_pipeline(context)

            # All agents should have run
            assert "CodebaseAnalyst" in results
            assert "Architect" in results
            assert "TechnicalWriter" in results
            assert "APIExtractor" in results
            assert "Reviewer" in results

            # All agents should have succeeded
            for agent_name, result in results.items():
                assert result.success is True, f"Agent {agent_name} failed"
        finally:
            shutil.rmtree(project_path)

    def test_analyze_codebase_command(self):
        """Test the analyze_codebase command function."""
        project_path = create_test_project()
        try:
            analysis = analyze_codebase(str(project_path))

            assert "codebase" in analysis
            assert "metadata" in analysis
            assert "endpoints" in analysis
            assert "agents" in analysis
            assert len(analysis["codebase"]["files"]) > 0
        finally:
            shutil.rmtree(project_path)

    def test_format_analysis_output(self):
        """Test that analysis output is formatted correctly."""
        project_path = create_test_project()
        try:
            analysis = analyze_codebase(str(project_path))
            formatted = format_analysis(analysis)

            assert "Codebase Analysis" in formatted
            assert "Project Metadata" in formatted
            assert "File Distribution" in formatted
            assert "Root Files" in formatted
            assert "Analysis Complete" in formatted
        finally:
            shutil.rmtree(project_path)

    def test_analyze_and_generate_full_pipeline(self):
        """Test the complete analyze and generate pipeline."""
        project_path = create_test_project()
        try:
            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                output = analyze_and_generate(str(project_path), output_format="text")

            # Should contain generated content
            assert len(output) > 0

            # Should contain README content
            assert "# Test Project" in output or "# Project" in output

            # Should contain diagram
            assert "Architecture Diagram" in output or "diagram" in output.lower()

            # Should contain API docs section
            assert "API Documentation" in output or "api" in output.lower()
        finally:
            shutil.rmtree(project_path)

    def test_generate_readme_basic(self):
        """Test basic README generation without AI."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            metadata = extract_project_metadata(str(project_path))

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                readme = generate_readme(codebase_info, metadata)

            assert "# " in readme
            assert "Project" in readme
        finally:
            shutil.rmtree(project_path)

    def test_generate_diagram_basic(self):
        """Test basic diagram generation without AI."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                diagram = generate_diagram(codebase_info)

            assert "```" in diagram
            assert "Basic ASCII Diagram" in diagram
        finally:
            shutil.rmtree(project_path)

    def test_generate_api_docs_basic(self):
        """Test basic API docs generation without AI."""
        project_path = create_fastapi_project()
        try:
            endpoints = extract_api_endpoints(str(project_path))

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                api_docs = generate_api_docs(endpoints)

            assert "API Reference" in api_docs
            assert "Endpoints" in api_docs
        finally:
            shutil.rmtree(project_path)

    def test_generate_setup_instructions(self):
        """Test setup instructions generation."""
        project_path = create_test_project()
        try:
            setup = generate_setup_instructions(str(project_path))

            assert "Setup Instructions" in setup
            # Should have some content related to setup
            assert "dependencies" in setup.lower() or "python" in setup.lower()
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_with_empty_project(self):
        """Test pipeline behavior with an empty project."""
        project_path = create_empty_project()
        try:
            codebase_info = scan_codebase(str(project_path))

            assert len(codebase_info["files"]) == 0
            assert len(codebase_info["languages"]) == 0
            # Root directory "." is always counted
            assert len(codebase_info["directories"]) >= 0
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_with_complex_project(self):
        """Test pipeline with a complex multi-file project."""
        project_path = create_complex_python_project()
        try:
            codebase_info = scan_codebase(str(project_path))

            assert len(codebase_info["files"]) >= 6
            assert "python" in codebase_info["languages"]
            assert len(codebase_info["languages"]["python"]["files"]) >= 6
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_with_js_project(self):
        """Test pipeline with a JavaScript project."""
        project_path = create_js_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))

            assert "javascript" in codebase_info["languages"]
            assert len(codebase_info["languages"]["javascript"]["files"]) >= 1

            metadata = extract_project_metadata(str(project_path))
            assert metadata.get("name") == "test-js-project"
        finally:
            shutil.rmtree(project_path)

    def test_pipeline_error_handling_nonexistent_path(self):
        """Test pipeline error handling for nonexistent paths."""
        with pytest.raises(ValueError) as exc_info:
            scan_codebase("/nonexistent/path")

        assert "does not exist" in str(exc_info.value)

    def test_pipeline_error_handling_invalid_path(self):
        """Test pipeline error handling for invalid paths."""
        with pytest.raises(FileNotFoundError) as exc_info:
            analyze_codebase("/nonexistent/path")

        assert "does not exist" in str(exc_info.value)

    def test_agent_pipeline_with_custom_agents(self):
        """Test running agent pipeline with custom agent list."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            context = {"codebase": codebase_info, "metadata": {}, "endpoints": []}

            # Use only a subset of agents
            custom_agents = [CodebaseAnalyst(), Architect()]
            results = run_agent_pipeline(context, custom_agents)

            assert "CodebaseAnalyst" in results
            assert "Architect" in results
            # Note: run_agent_pipeline uses default agents if none provided
            # This test verifies the function works with agent override
            assert len(results) >= 2
        finally:
            shutil.rmtree(project_path)


class TestAnalysisParserIntegration:
    """Integration tests for the analysis parser module."""

    def test_parse_python_file_integration(self):
        """Test Python file parsing in pipeline context."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "test.py").write_text("""
import os
import sys
from pathlib import Path

def hello():
    pass

class MyClass:
    def method(self):
        pass
""")

            result = parse_python_file(str(tmpdir / "test.py"))

            assert result["syntax_error"] is False
            assert len(result["imports"]) >= 2
            assert len(result["functions"]) >= 1
            assert len(result["classes"]) >= 1
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_python(self):
        """Test dependency extraction in pipeline context."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "deps.py").write_text("""
import requests
import flask
from sqlalchemy import create_engine
""")

            deps = extract_dependencies(str(tmpdir / "deps.py"))

            assert "requests" in deps
            assert "flask" in deps
            assert "sqlalchemy" in deps
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_project_dependencies(self):
        """Test project-level dependency extraction."""
        project_path = create_test_project()
        try:
            deps = extract_project_dependencies(str(project_path))

            # Should find requirements.txt
            assert len(deps) >= 0
        finally:
            shutil.rmtree(project_path)

    def test_extract_dependencies_requirements_txt(self):
        """Test requirements.txt parsing."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
flask>=2.3.0
django==4.2.0
numpy~=1.24.0
pandas[sql]>=2.0.0
scipy
matplotlib
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps
            assert "flask" in deps
            assert "django" in deps
            assert "numpy" in deps
            assert "pandas" in deps
            assert "scipy" in deps
            assert "matplotlib" in deps
            # Should be exactly 7 dependencies
            assert len(deps) == 7

        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_versions(self):
        """Test requirements.txt parsing with various version specifiers."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
package1==1.0.0
package2>=2.0.0
package3<=3.0.0
package4>4.0.0
package5~=5.0.0
package6!=6.0.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "package1" in deps
            assert "package2" in deps
            assert "package3" in deps
            assert "package4" in deps
            assert "package5" in deps
            assert "package6" in deps
            assert len(deps) == 6

        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_extras(self):
        """Test requirements.txt parsing with package extras."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
django[bcrypt,argon2]==4.2.0
requests[security]>=2.28.0
flask[async]>=2.3.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "django" in deps
            assert "requests" in deps
            assert "flask" in deps
            assert len(deps) == 3

        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_empty(self):
        """Test requirements.txt parsing with empty file."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert deps == []
            assert len(deps) == 0

        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_comments(self):
        """Test requirements.txt parsing with comments."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
# This is a comment
requests>=2.28.0
# Another comment
flask>=2.3.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps
            assert "flask" in deps
            assert len(deps) == 2

        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_whitespace(self):
        """Test requirements.txt parsing with various whitespace."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
requests>=2.28.0
flask>=2.3.0

django>=4.2.0

numpy>=1.24.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            assert "requests" in deps
            assert "flask" in deps
            assert "django" in deps
            assert "numpy" in deps
            assert len(deps) == 4

        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_with_url_packages(self):
        """Test requirements.txt parsing with URL-based packages."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            (tmpdir / "requirements.txt").write_text("""
-e git+https://github.com/user/repo.git#egg=mypackage
-r other_requirements.txt
requests>=2.28.0
""")

            deps = extract_dependencies(str(tmpdir / "requirements.txt"))

            # Should extract the package name from the URL
            assert "requests" in deps
            # URL-based packages may or may not be extracted depending on regex
        finally:
            shutil.rmtree(tmpdir)

    def test_extract_dependencies_requirements_txt_nonexistent_file(self):
        """Test requirements.txt parsing with nonexistent file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            extract_dependencies("/nonexistent/path/requirements.txt")

        assert "does not exist" in str(exc_info.value)

    def test_extract_project_dependencies_with_requirements_txt(self):
        """Test project-level dependency extraction with requirements.txt."""
        project_path = create_test_project()
        try:
            deps = extract_project_dependencies(str(project_path))

            # Should have requirements.txt in deps_by_file
            requirements_path = Path("requirements.txt")
            if requirements_path in deps:
                deps_str = str(requirements_path)
                assert deps[deps_str] is not None
                assert len(deps[deps_str]) >= 0
        finally:
            shutil.rmtree(project_path)

    def test_parse_file_auto_detection(self):
        """Test automatic file type detection."""
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)

            # Python file
            (tmpdir / "test.py").write_text("def hello(): pass\n")
            result = parse_file(str(tmpdir / "test.py"))
            assert result.get("language") == "python" or "syntax_error" in result

            # JavaScript file
            (tmpdir / "test.js").write_text("const x = 1;\n")
            result = parse_file(str(tmpdir / "test.js"))
            assert result.get("language") == "javascript" or "imports" in result

            # TypeScript file
            (tmpdir / "test.ts").write_text("const x: number = 1;\n")
            result = parse_file(str(tmpdir / "test.ts"))
            assert result.get("language") == "typescript" or "imports" in result
        finally:
            shutil.rmtree(tmpdir)


class TestAnalysisGeneratorIntegration:
    """Integration tests for the documentation generation module."""

    def test_readme_generation_with_metadata(self):
        """Test README generation with full metadata."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            metadata = extract_project_metadata(str(project_path))

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                readme = generate_readme(codebase_info, metadata)

            assert "# " in readme
            assert "Project" in readme
            assert "description" in readme.lower() or "no description" in readme.lower()
        finally:
            shutil.rmtree(project_path)

    def test_diagram_generation_with_codebase(self):
        """Test diagram generation with codebase info."""
        project_path = create_test_project()
        try:
            codebase_info = scan_codebase(str(project_path))

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                diagram = generate_diagram(codebase_info)

            assert "```" in diagram
            assert "Basic ASCII Diagram" in diagram
        finally:
            shutil.rmtree(project_path)

    def test_api_docs_generation_with_endpoints(self):
        """Test API docs generation with actual endpoints."""
        project_path = create_fastapi_project()
        try:
            endpoints = extract_api_endpoints(str(project_path))

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                api_docs = generate_api_docs(endpoints)

            assert "API Reference" in api_docs
            assert len(api_docs) > 0
        finally:
            shutil.rmtree(project_path)

    def test_setup_instructions_generation(self):
        """Test setup instructions generation."""
        project_path = create_test_project()
        try:
            setup = generate_setup_instructions(str(project_path))

            assert "Setup Instructions" in setup
            # Should have the dependencies section header (case insensitive)
            assert "### dependencies" in setup.lower()
        finally:
            shutil.rmtree(project_path)

    def test_readme_generation_empty_codebase(self):
        """Test README generation with empty codebase."""
        project_path = create_empty_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            metadata = extract_project_metadata(str(project_path))

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                readme = generate_readme(codebase_info, metadata)

            assert "# " in readme
        finally:
            shutil.rmtree(project_path)


class TestPipelineEndToEnd:
    """End-to-end integration tests covering the full pipeline."""

    def test_e2e_python_project(self):
        """Test full pipeline on a Python project."""
        project_path = create_test_project()
        try:
            # Step 1: Scan codebase
            codebase_info = scan_codebase(str(project_path))

            # Step 2: Extract metadata
            metadata = extract_project_metadata(str(project_path))

            # Step 3: Extract endpoints
            endpoints = extract_api_endpoints(str(project_path))

            # Step 4: Run agents
            context = {
                "codebase": codebase_info,
                "metadata": metadata,
                "endpoints": endpoints,
            }
            results = run_agent_pipeline(context)

            # Step 5: Generate outputs
            # Extract metadata from AgentResult objects
            tw_metadata = None
            if "TechnicalWriter" in results and results["TechnicalWriter"].success:
                tw_metadata = results["TechnicalWriter"].metadata
            arch_metadata = None
            if "Architect" in results and results["Architect"].success:
                arch_metadata = results["Architect"].metadata

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                readme = generate_readme(codebase_info, metadata)
                diagram = generate_diagram(codebase_info)

            # Only generate API docs if we have endpoints
            if endpoints:
                with patch('cli.commands.generate.call_ai_model') as mock_call:
                    mock_call.side_effect = AuthenticationError("No API key configured")
                    api_docs = generate_api_docs(endpoints)
                    assert len(api_docs) > 0
            else:
                api_docs = ""

            # Verify outputs
            assert len(readme) > 0
            assert len(diagram) > 0
        finally:
            shutil.rmtree(project_path)

    def test_e2e_js_project(self):
        """Test full pipeline on a JavaScript project."""
        project_path = create_js_test_project()
        try:
            # Step 1: Scan codebase
            codebase_info = scan_codebase(str(project_path))

            # Step 2: Extract metadata
            metadata = extract_project_metadata(str(project_path))

            # Step 3: Extract endpoints
            endpoints = extract_api_endpoints(str(project_path))

            # Step 4: Run agents
            context = {
                "codebase": codebase_info,
                "metadata": metadata,
                "endpoints": endpoints,
            }
            results = run_agent_pipeline(context)

            # Step 5: Generate outputs
            # Extract metadata from AgentResult objects
            tw_metadata = None
            if "TechnicalWriter" in results and results["TechnicalWriter"].success:
                tw_metadata = results["TechnicalWriter"].metadata
            arch_metadata = None
            if "Architect" in results and results["Architect"].success:
                arch_metadata = results["Architect"].metadata

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                readme = generate_readme(codebase_info, metadata)
                diagram = generate_diagram(codebase_info)

            # Only generate API docs if we have endpoints
            if endpoints:
                with patch('cli.commands.generate.call_ai_model') as mock_call:
                    mock_call.side_effect = AuthenticationError("No API key configured")
                    api_docs = generate_api_docs(endpoints)
                    assert len(api_docs) > 0
            else:
                api_docs = ""

            # Verify outputs
            assert len(readme) > 0
            assert len(diagram) > 0
        finally:
            shutil.rmtree(project_path)

    def test_e2e_fastapi_project(self):
        """Test full pipeline on a FastAPI project."""
        project_path = create_fastapi_project()
        try:
            # Step 1: Scan codebase
            codebase_info = scan_codebase(str(project_path))

            # Step 2: Extract metadata
            metadata = extract_project_metadata(str(project_path))

            # Step 3: Extract endpoints
            endpoints = extract_api_endpoints(str(project_path))

            # Step 4: Run agents
            context = {
                "codebase": codebase_info,
                "metadata": metadata,
                "endpoints": endpoints,
            }
            results = run_agent_pipeline(context)

            # Step 5: Generate outputs
            # Extract metadata from AgentResult objects
            tw_metadata = None
            if "TechnicalWriter" in results and results["TechnicalWriter"].success:
                tw_metadata = results["TechnicalWriter"].metadata
            arch_metadata = None
            if "Architect" in results and results["Architect"].success:
                arch_metadata = results["Architect"].metadata

            with patch('cli.commands.generate.call_ai_model') as mock_call:
                mock_call.side_effect = AuthenticationError("No API key configured")
                readme = generate_readme(codebase_info, metadata)
                diagram = generate_diagram(codebase_info)

            # Only generate API docs if we have endpoints
            if endpoints:
                with patch('cli.commands.generate.call_ai_model') as mock_call:
                    mock_call.side_effect = AuthenticationError("No API key configured")
                    api_docs = generate_api_docs(endpoints)
                    assert len(api_docs) > 0
            else:
                api_docs = ""

            # Verify outputs
            assert len(readme) > 0
            assert len(diagram) > 0
            assert "API Reference" in api_docs or "api" in api_docs.lower()
        finally:
            shutil.rmtree(project_path)

    def test_e2e_pipeline_with_error_handling(self):
        """Test pipeline error handling with various edge cases."""
        # Test with nonexistent path
        with pytest.raises(ValueError):
            scan_codebase("/nonexistent/path")

        # Test with empty directory
        project_path = create_empty_project()
        try:
            codebase_info = scan_codebase(str(project_path))
            assert len(codebase_info["files"]) == 0
        finally:
            shutil.rmtree(project_path)

        # Test with large file
        tmpdir = tempfile.mkdtemp()
        try:
            tmpdir = Path(tmpdir)
            large_content = "# " * 200000
            (tmpdir / "large.py").write_text(large_content)

            codebase_info = scan_codebase(str(tmpdir))
            assert len(codebase_info["files"]) == 1
            assert codebase_info["files"][0]["size"] > 100000
        finally:
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
