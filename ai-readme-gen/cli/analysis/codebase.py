"""Codebase traversal and analysis."""

import ast
import os
import re
import tomllib
from pathlib import Path
from typing import Any, Dict


SUPPORTED_EXTENSIONS = {
    # Python
    ".py": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    # Other
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".env": "env",
    ".sh": "shell",
    ".bash": "shell",
}


def scan_codebase(path: str, languages: list[str] | None = None) -> Dict[str, Any]:
    """
    Scan a codebase and return structured information.

    Args:
        path: Path to the codebase root directory
        languages: Optional list of language names to filter by (e.g. ["python"])

    Returns:
        Dictionary containing codebase information
    """
    path_obj = Path(path).resolve()

    if not path_obj.exists():
        raise ValueError(f"Path does not exist: {path_obj}")

    codebase_info = {
        "path": str(path),
        "files": [],
        "languages": {},
        "directories": [],
        "root_files": [],
    }

    # Build extension-to-language lookup for filtering
    ext_to_lang = {ext: lang for ext, lang in SUPPORTED_EXTENSIONS.items()}
    lang_to_ext = {}
    for ext, lang in SUPPORTED_EXTENSIONS.items():
        lang_to_ext.setdefault(lang, set()).add(ext)

    # Detect Python version from pyproject.toml or requirements.txt
    detected_versions: Dict[str, str] = {}
    pyproject = path_obj / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject, 'rb') as f:
                pdata = tomllib.load(f)
            # Check tool.poetry.python
            python_req = pdata.get("tool", {}).get("poetry", {}).get("python")
            if python_req:
                detected_versions["python"] = python_req
            # Check project.requires-python
            requires_python = pdata.get("project", {}).get("requires-python")
            if requires_python:
                detected_versions["python"] = requires_python
        except Exception:
            pass
    # Check setup.cfg
    setup_cfg = path_obj / "setup.cfg"
    if "python" not in detected_versions and setup_cfg.exists():
        content = setup_cfg.read_text(errors='ignore')
        version_match = re.search(r'python_requires\s*=\s*(.+)', content)
        if version_match:
            detected_versions["python"] = version_match.group(1).strip()

    for root, dirs, files in os.walk(path):
        # Skip hidden directories and common non-code directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                   {'node_modules', '__pycache__', 'venv', '.venv', 'env', '.env'}]

        dir_path = Path(root)
        codebase_info["directories"].append(str(dir_path.relative_to(path)))

        for file in files:
            file_path = dir_path / file
            ext = file_path.suffix.lower()

            if ext in ext_to_lang:
                language = ext_to_lang[ext]

                # Filter by languages if specified
                if languages is not None and language not in languages:
                    continue

                relative_path = str(file_path.relative_to(path))

                file_info = {
                    "path": relative_path,
                    "extension": ext,
                    "language": language,
                    "size": file_path.stat().st_size,
                }
                codebase_info["files"].append(file_info)

                # Track language distribution
                if language not in codebase_info["languages"]:
                    lang_info: Dict[str, Any] = {
                        "count": 0,
                        "files": [],
                    }
                    # Add detected version if available
                    if language in detected_versions:
                        lang_info["version"] = detected_versions[language]
                    codebase_info["languages"][language] = lang_info
                codebase_info["languages"][language]["count"] += 1
                codebase_info["languages"][language]["files"].append(relative_path)

                # Track root-level files (files directly in the project root)
                if file_path.parent == path_obj:
                    codebase_info["root_files"].append(relative_path)

    return codebase_info


def parse_python_file(file_path: str) -> Dict[str, Any]:
    """Parse a Python file for structure information.

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary containing parsed information including imports, classes, and functions
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return {
                "path": file_path,
                "language": "python",
                "parsing": "failed",
                "syntax_error": True,
                "imports": [],
                "classes": [],
                "functions": [],
            }

    imports = []
    classes = []
    functions = []

    for node in ast.walk(tree):
        # Collect imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

        # Collect classes
        if isinstance(node, ast.ClassDef):
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
            classes.append({
                "name": node.name,
                "bases": bases,
                "methods": [],
            })

        # Collect methods in classes
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    classes[-1]["methods"].append(item.name)

        # Collect top-level functions
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "returns": None,
            })

    return {
        "path": file_path,
        "language": "python",
        "parsing": "success",
        "syntax_error": False,
        "imports": imports,
        "classes": classes,
        "functions": functions,
    }


def parse_javascript_file(file_path: str) -> Dict[str, Any]:
    """Parse a JavaScript/TypeScript file for structure information.

    Args:
        file_path: Path to the JavaScript/TypeScript file

    Returns:
        Dictionary containing parsed information including imports, exports, classes, and functions
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    imports = []
    exports = []
    classes = []
    functions = []

    # Simple regex-based parsing for JS/TS
    # This is a basic implementation; a full parser would use acorn or similar

    # Find imports (ESM and CommonJS)
    esm_imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
    imports.extend(esm_imports)

    commonjs_imports = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
    imports.extend(commonjs_imports)

    # Find exports
    _ = re.findall(r'export\s+(?:default\s+)?(?:function|class|const|let|var|async\s+function)\s+(\w+)', content)  # noqa: E501
    esm_named_exports = re.findall(r'export\s+\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]', content)
    _ = re.findall(r'module\.exports\s*=\s*(\w+)', content)

    if esm_named_exports:
        exports.extend(esm_named_exports)

    # Find classes
    class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{[^}]*\}'
    for match in re.finditer(class_pattern, content, re.DOTALL):
        classes.append({
            "name": match.group(1),
            "extends": match.group(2),
        })

    # Find functions
    func_pattern = r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'
    for match in re.finditer(func_pattern, content):
        functions.append({
            "name": match.group(1),
        })

    return {
        "path": file_path,
        "language": "javascript",
        "parsing": "success",
        "imports": imports,
        "exports": exports,
        "classes": classes,
        "functions": functions,
    }
