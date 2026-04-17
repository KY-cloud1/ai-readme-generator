"""Pattern extraction utilities."""

import json
import os
import re
import tomllib
from pathlib import Path
from typing import Dict, List, Any


def extract_project_metadata(path: str) -> Dict[str, Any]:
    """
    Extract project metadata from configuration files.

    Args:
        path: Path to the project root

    Returns:
        Dictionary containing project metadata including scripts and entry_points
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Path does not exist: {path_obj}")

    metadata = {
        "name": None,
        "description": None,
        "version": None,
        "author": None,
        "authors": [],
        "keywords": [],
        "license": None,
        "repository": None,
        "scripts": None,
        "entry_points": None,
        "dependencies": [],
        "classifiers": [],
    }

    # Check README.md for project name/description (lowest precedence)
    readme = path_obj / "README.md"
    if readme.exists():
        metadata.update(extract_from_readme(str(readme)))

    # Check package.json
    package_json = path_obj / "package.json"
    if package_json.exists():
        metadata.update(extract_from_package_json(str(package_json)))

    # Check pyproject.toml (highest precedence)
    pyproject = path_obj / "pyproject.toml"
    if pyproject.exists():
        metadata.update(extract_from_pyproject(str(pyproject)))

    return metadata


def extract_from_pyproject(path: str) -> Dict[str, Any]:
    """Extract metadata from pyproject.toml.

    Args:
        path: Path to pyproject.toml file

    Returns:
        Dictionary with extracted metadata fields
    """
    base_path = Path(path)
    try:
        with open(base_path, 'rb') as f:
            data = tomllib.load(f)
    except (IOError, OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return {}

    project = data.get("project", {})

    # Safely get URLs - can be a list or dict
    urls = project.get("urls")
    # Handle both list format and dict format
    if isinstance(urls, list):
        # List format: ["https://example.com", ...]
        repository = urls[0] if urls else None
        urls_dict = {}
    elif isinstance(urls, dict):
        # Dict format: {"Homepage": "...", "Repository": "..."}
        repository = None  # Will be set from dict keys
        urls_dict = urls
    else:
        repository = None
        urls_dict = {}

    result: Dict[str, Any] = {
        "name": project.get("name"),
        "version": project.get("version"),
        "description": project.get("description"),
        "keywords": project.get("keywords", []) if isinstance(project.get("keywords"), list) else [],  # noqa: E501
        "license": project.get("license", {}).get("text") if isinstance(project.get("license"), dict) else None,  # noqa: E501
        "repository": repository,
        "classifiers": project.get("classifiers", []) if isinstance(project.get("classifiers"), list) else [],  # noqa: E501
        "scripts": project.get("scripts", {}) if isinstance(project.get("scripts"), dict) else None,
        # Handle both "entry-points" (PEP 621) and "entry_points" (hyphenated)
        "entry_points": project.get("entry_points") or project.get("entry-points", {}) if isinstance(project.get("entry_points") or project.get("entry-points"), dict) else None,  # noqa: E501
        "dependencies": project.get("dependencies", []) if isinstance(project.get("dependencies"), list) else [],
        "authors": project.get("authors", []),
    }

    # Extract URLs
    if urls_dict:
        # Filter out empty values and preserve original case
        filtered_urls = {k: v for k, v in urls_dict.items() if k and v}
        if filtered_urls:
            result["urls"] = filtered_urls

    # Extract author from tool.poetry or project
    # Handle Poetry format: authors = ["Author <email>"]
    if "tool" in data and "poetry" in data["tool"]:
        poetry = data["tool"]["poetry"]
        # Extract Poetry metadata
        result["name"] = poetry.get("name")
        result["version"] = poetry.get("version")
        result["description"] = poetry.get("description")
        result["license"] = poetry.get("license")
        authors = poetry.get("authors")
        if authors and isinstance(authors, list) and len(authors) > 0:
            result["author"] = authors[0]
    # Handle PEP 621 format: authors = [{"name": "...", "email": "..."}]
    elif "project" in data and data["project"].get("authors"):
        authors = data["project"]["authors"]
        if isinstance(authors, list) and len(authors) > 0:
            author = authors[0]
            if isinstance(author, dict):
                result["author"] = f"{author.get('name', '')} <{author.get('email', '')}>"
            else:
                result["author"] = author

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
        "repository": data.get("repository", {}).get("url") if isinstance(data.get("repository"), dict) else data.get("repository"),  # noqa: E501
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
    name = title_match.group(1).strip() if title_match else None

    # Extract description: first non-empty paragraph after the title
    description = None
    lines = content.strip().split('\n')
    found_title = False
    for line in lines:
        stripped = line.strip()
        if not found_title:
            if stripped.startswith('#'):
                found_title = True
            continue
        if stripped and not stripped.startswith('#'):
            description = stripped
            break

    result: Dict[str, Any] = {}
    if name:
        result["name"] = name
    if description:
        result["description"] = description

    return result


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
        (r'@app\.(get|post|put|delete)\s*\(\s*(?:[\w,=\s]+\s*)?[\'"](/[\w/_-]+[\'"])\s*\)', 'fastapi-generic'),  # noqa: E501
    ]

    # Look for Flask routes (@app.route)
    flask_patterns = [
        (r'@app\.route\s*\(\s*[\'"](/[\w/_-]*)[\'"]\s*(?:,\s*methods\s*=\s*\[([^\]]*)\])?\s*\)', 'flask'),  # noqa: E501
    ]

    # Look for Express/Fastify routes (with various patterns)
    express_patterns = [
        # Basic router patterns
        (r'router\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'express'),
        (r'fastify\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'fastify'),
        # With path parameters
        (r'router\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+/{:[\w]+}[\'"])\s*\)', 'express'),  # noqa: E501
        (r'fastify\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+/{:[\w]+}[\'"])\s*\)', 'fastify'),  # noqa: E501
        # Additional patterns for different frameworks
        (r'app\.(get|post|put|delete|patch)\s*\(\s*[\'"](/[\w/_-]+[\'"])\s*\)', 'express-app'),
        # With additional parameters
        (r'(?:router|app|fastify)\.(get|post|put|delete|patch)\s*\(\s*(?:[\w,=\s]+\s*)?[\'"](/[\w/_-]+[\'"])\s*\)', 'express-generic'),  # noqa: E501
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

                # Check for Flask
                for pattern, method in flask_patterns:
                    try:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            path_part = match.group(1)
                            methods_str = match.group(2)
                            if methods_str:
                                # Parse methods list: "['GET', 'POST']" -> ['GET', 'POST']
                                http_methods = [m.strip().strip("'\"") for m in methods_str.split(',')]
                            else:
                                # Default to GET
                                http_methods = ['GET']
                            for http_method in http_methods:
                                endpoints.append({
                                    "method": http_method.upper(),
                                    "path": path_part,
                                    "source": str(file_path),
                                    "type": "flask",
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
    instructions: Dict[str, Any] = {
        "installation": [],
        "environment": [],
        "configuration": [],
        "dependencies": [],
    }

    dep_lines: List[str] = []

    # Check for requirements.txt
    req_file = Path(path) / "requirements.txt"
    if req_file.exists():
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    dep_lines.append(line)

    # Check for package.json
    pkg_file = Path(path) / "package.json"
    if pkg_file.exists():
        with open(pkg_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            dep_lines.append("npm install")
            if "scripts" in data:
                instructions["configuration"].append("npm run <script>")

    # Check for pyproject.toml dependencies
    pyproject_file = Path(path) / "pyproject.toml"
    if pyproject_file.exists():
        try:
            with open(pyproject_file, 'rb') as f:
                pdata = tomllib.load(f)
            deps = pdata.get("project", {}).get("dependencies", [])
            if isinstance(deps, list):
                for dep in deps:
                    # Extract package name from "package>=version" format
                    name_match = re.match(r'([a-zA-Z0-9_-]+)', dep)
                    if name_match:
                        dep_lines.append(name_match.group(1))
        except Exception:
            pass

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

    # Return dependencies as a list
    instructions["dependencies"] = dep_lines if dep_lines else []

    return instructions
