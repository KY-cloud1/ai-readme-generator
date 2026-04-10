"""Pattern extraction utilities."""

import re
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
    path = Path(path)
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
    pyproject = path / "pyproject.toml"
    if pyproject.exists():
        metadata.update(extract_from_pyproject(pyproject))

    # Check package.json
    package_json = path / "package.json"
    if package_json.exists():
        metadata.update(extract_from_package_json(package_json))

    # Check README.md for project name/description
    readme = path / "README.md"
    if readme.exists():
        metadata.update(extract_from_readme(readme))

    return metadata


def extract_from_pyproject(path: str) -> Dict[str, Any]:
    """Extract metadata from pyproject.toml."""
    import tomllib

    with open(path, 'rb') as f:
        data = tomllib.load(f)

    result = {
        "name": data.get("project", {}).get("name"),
        "version": data.get("project", {}).get("version"),
        "description": data.get("project", {}).get("description"),
        "keywords": data.get("project", {}).get("keywords", []),
        "license": data.get("project", {}).get("license", {}).get("text"),
        "repository": data.get("project", {}).get("urls", [None])[0] if data.get("project", {}).get("urls") else None,
    }

    # Extract author from tool.poetry or project
    author = None
    if "tool" in data and "poetry" in data["tool"]:
        author = data["tool"]["poetry"].get("authors", [None])[0]
    result["author"] = author

    return result


def extract_from_package_json(path: str) -> Dict[str, Any]:
    """Extract metadata from package.json."""
    import json

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return {
        "name": data.get("name"),
        "version": data.get("version"),
        "description": data.get("description"),
        "keywords": data.get("keywords", []),
        "license": data.get("license"),
        "author": data.get("author") or data.get("authors", [None])[0],
        "repository": data.get("repository", {}).get("url") if isinstance(data.get("repository"), dict) else data.get("repository"),
    }


def extract_from_readme(path: str) -> Dict[str, Any]:
    """Extract metadata from README.md."""
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract project name from title or first heading
    title_match = re.search(r'#\s+([A-Za-z0-9_\s\-]+)', content)
    if title_match:
        return {
            "name": title_match.group(1).strip(),
            "description": None,
        }

    # Extract description from text
    desc_match = re.search(r'(?:Description|About)\s*\n\s*(.+)', content)
    if desc_match:
        return {
            "name": None,
            "description": desc_match.group(1).strip(),
        }

    return {}


def extract_api_endpoints(path: str) -> List[Dict[str, Any]]:
    """
    Extract API endpoint definitions from code.

    Args:
        path: Path to the project root

    Returns:
        List of API endpoint definitions
    """
    endpoints = []

    # Look for FastAPI routes
    fastapi_patterns = [
        (r'@app\.get\s*\(\s*[\'"](/[\w/_]+[\'"])\s*\)', 'fastapi-get'),
        (r'@app\.post\s*\(\s*[\'"](/[\w/_]+[\'"])\s*\)', 'fastapi-post'),
        (r'@app\.put\s*\(\s*[\'"](/[\w/_]+[\'"])\s*\)', 'fastapi-put'),
        (r'@app\.delete\s*\(\s*[\'"](/[\w/_]+[\'"])\s*\)', 'fastapi-delete'),
    ]

    # Look for Express routes
    express_patterns = [
        (r'router\.(get|post|put|delete)\s*\(\s*[\'"](/[\w/_]+[\'"])\s*\)', 'express'),
        (r'app\.(get|post|put|delete)\s*\(\s*[\'"](/[\w/_]+[\'"])\s*\)', 'express'),
    ]

    for root, dirs, files in __import__('os').walk(path):
        for file in files:
            if file.endswith(('.py', '.js', '.ts')):
                file_path = Path(root) / file
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                # Check for FastAPI
                for pattern, method in fastapi_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        path_part = match.group(1)
                        endpoints.append({
                            "method": "GET" if method == 'fastapi-get' else
                                    "POST" if method == 'fastapi-post' else
                                    "PUT" if method == 'fastapi-put' else
                                    "DELETE",
                            "path": path_part,
                            "source": str(file_path),
                            "type": "fastapi",
                        })

                # Check for Express
                for pattern, method in express_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        path_part = match.group(1)
                        http_method = match.group(2)
                        endpoints.append({
                            "method": http_method.upper(),
                            "path": path_part,
                            "source": str(file_path),
                            "type": "express",
                        })

    return endpoints


def extract_setup_instructions(path: str) -> Dict[str, Any]:
    """
    Extract setup/installation instructions from project.

    Args:
        path: Path to the project root

    Returns:
        Dictionary containing setup instructions
    """
    instructions = {
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
        import json
        with open(pkg_file, 'r') as f:
            data = json.load(f)
            instructions["dependencies"].append(f"npm install")
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
