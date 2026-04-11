"""Pattern extraction utilities."""

import json
import os
import re
import tomllib
from pathlib import Path
from typing import Dict, List, Any, Optional


def extract_project_metadata(path: str) -> Dict[str, Any]:
    """
    Extract project metadata from configuration files.

    Args:
        path: Path to the project root

    Returns:
        Dictionary containing project metadata
    """
    path_obj = Path(path)
    metadata = {
        "name": None,
        "description": None,
        "version": None,
        "author": None,
        "keywords": [],
        "license": None,
        "repository": None,
    }

    # Check pyproject.toml
    pyproject = path_obj / "pyproject.toml"
    if pyproject.exists():
        metadata.update(extract_from_pyproject(str(pyproject)))

    # Check package.json
    package_json = path_obj / "package.json"
    if package_json.exists():
        metadata.update(extract_from_package_json(str(package_json)))

    # Check README.md for project name/description
    readme = path_obj / "README.md"
    if readme.exists():
        metadata.update(extract_from_readme(str(readme)))

    return metadata


def extract_from_pyproject(path: str) -> Dict[str, Any]:
    """Extract metadata from pyproject.toml.

    Args:
        path: Path to pyproject.toml file

    Returns:
        Dictionary with extracted metadata fields
    """
    base_path = Path(path)
    with open(base_path, 'rb') as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    urls = project.get("urls", [])

    result: Dict[str, Any] = {
        "name": project.get("name"),
        "version": project.get("version"),
        "description": project.get("description"),
        "keywords": project.get("keywords", []),
        "license": project.get("license", {}).get("text") if project.get("license") else None,
        "repository": urls[0] if urls else None,
    }

    # Extract author from tool.poetry or project
    if "tool" in data and "poetry" in data["tool"]:
        authors = data["tool"]["poetry"].get("authors")
        if authors:
            result["author"] = authors[0]

    return result


def extract_from_package_json(path: str) -> Dict[str, Any]:
    """Extract metadata from package.json.

    Args:
        path: Path to package.json file

    Returns:
        Dictionary with extracted metadata fields
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    result: Dict[str, Any] = {
        "name": data.get("name"),
        "version": data.get("version"),
        "description": data.get("description"),
        "keywords": data.get("keywords", []),
        "license": data.get("license"),
        "author": data.get("author") or data.get("authors", [None])[0],
        "repository": data.get("repository", {}).get("url") if isinstance(data.get("repository"), dict) else data.get("repository"),
    }

    return result


def extract_from_readme(path: str) -> Dict[str, Any]:
    """Extract metadata from README.md.

    Args:
        path: Path to README.md file

    Returns:
        Dictionary with extracted name and/or description
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract project name from title or first heading
    title_match = re.search(r'#\s+(.+)', content)
    if title_match:
        return {"name": title_match.group(1).strip(), "description": None}

    # Extract description from text
    desc_match = re.search(r'(?:Description|About)\s*\n\s*(.+)', content)
    if desc_match:
        return {"name": None, "description": desc_match.group(1).strip()}

    return {}


def extract_api_endpoints(path: str) -> List[Dict[str, Any]]:
    """Extract API endpoint definitions from code.

    Args:
        path: Path to the project root

    Returns:
        List of API endpoint definitions
    """
    endpoints: List[Dict[str, Any]] = []

    # Look for FastAPI routes (with various parameter combinations)
    fastapi_patterns = [
        # Basic patterns
        (r'@app\.get\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'fastapi-get'),
        (r'@app\.post\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'fastapi-post'),
        (r'@app\.put\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'fastapi-put'),
        (r'@app\.delete\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'fastapi-delete'),
        # With additional parameters (tags, summary, etc.)
        (r'@app\.(get|post|put|delete)\s*\(\s*(?:[\w,=\s]+\s*)?[\'"](/[\w/_-]+[\'"])\s*\)', 'fastapi-generic'),
    ]

    # Look for Express/Fastify routes (with various patterns)
    express_patterns = [
        # Basic router patterns
        (r'router\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'express'),
        (r'fastify\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'fastify'),
        # With path parameters
        (r'router\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+/{:[\w]+}[\'"])\s*\)', 'express'),
        (r'fastify\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+/{:[\w]+}[\'"])\s*\)', 'fastify'),
        # Additional patterns for different frameworks
        (r'app\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'express-app'),
        # With additional parameters
        (r'(?:router|app|fastify)\.(get|post|put|delete|patch)\s*\(\s*(?:[\w,=\s]+\s*)?[\'"](/[\w/_-]+[\'"])\s*\)', 'express-generic'),
    ]

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(('.py', '.js', '.ts')):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding='utf-8')
                except (IOError, OSError, UnicodeDecodeError):
                    continue

                # Check for FastAPI
                for pattern, method in fastapi_patterns:
                    try:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            path_part = match.group(1)
                            if method == 'fastapi-generic':
                                http_method = match.group(2).upper()
                            else:
                                http_method = match.group(1).upper()
                            endpoints.append({
                                "method": http_method,
                                "path": path_part,
                                "source": str(file_path),
                                "type": "fastapi",
                            })
                    except re.error:
                        continue

                # Check for Express/Fastify
                for pattern, method in express_patterns:
                    try:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            path_part = match.group(1)
                            http_method = match.group(1).upper()
                            endpoints.append({
                                "method": http_method,
                                "path": path_part,
                                "source": str(file_path),
                                "type": method,
                            })
                    except re.error:
                        continue

    return endpoints


def extract_setup_instructions(path: str) -> Dict[str, Any]:
    """Extract setup/installation instructions from project.

    Args:
        path: Path to the project root

    Returns:
        Dictionary containing setup instructions
    """
    instructions: Dict[str, List[str]] = {
        "installation": [],
        "environment": [],
        "configuration": [],
        "dependencies": [],
    }

    # Check for requirements.txt
    req_file = Path(path) / "requirements.txt"
    if req_file.exists():
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    instructions["dependencies"].append(line)

    # Check for package.json
    pkg_file = Path(path) / "package.json"
    if pkg_file.exists():
        with open(pkg_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            instructions["dependencies"].append("npm install")
            if "scripts" in data:
                instructions["configuration"].append("npm run <script>")

    # Check for Dockerfile
    dockerfile = Path(path) / "Dockerfile"
    if dockerfile.exists():
        instructions["installation"].append("docker build -t your-image .")

    # Check for README.md for setup instructions
    readme = Path(path) / "README.md"
    if readme.exists():
        with open(readme, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if "pip install" in content:
                instructions["installation"].append("pip install -r requirements.txt")
            if "npm install" in content:
                instructions["installation"].append("npm install")

    return instructions
