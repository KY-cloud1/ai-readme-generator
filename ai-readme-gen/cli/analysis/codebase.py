"""Codebase traversal and analysis."""

import ast
import os
import re
from pathlib import Path
from typing import Dict, Any


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


def scan_codebase(path: str) -> Dict[str, Any]:
    """
    Scan a codebase and return structured information.

    Args:
        path: Path to the codebase root directory

    Returns:
        Dictionary containing codebase information
    """
    path_obj = Path(path).resolve()

    if not path_obj.is_dir():
        raise ValueError(f"Path does not exist: {path_obj}")

    codebase_info = {
        "path": str(path),
        "files": [],
        "languages": {},
        "directories": [],
        "root_files": [],
    }

    for root, dirs, files in os.walk(path):
        # Skip hidden directories and common non-code directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                   {'node_modules', '__pycache__', 'venv', '.venv', 'env', '.env'}]

        dir_path = Path(root)
        codebase_info["directories"].append(str(dir_path.relative_to(path)))

        for file in files:
            file_path = dir_path / file
            ext = file_path.suffix.lower()

            if ext in SUPPORTED_EXTENSIONS:
                language = SUPPORTED_EXTENSIONS[ext]
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
                    codebase_info["languages"][language] = {
                        "count": 0,
                        "files": [],
                    }
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
            imports.append([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            imports.append([alias.name for alias in node.names])

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
    for imp in esm_imports:
        imports.append(f"from '{imp}'")

    commonjs_imports = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
    for imp in commonjs_imports:
        imports.append(f"require('{imp}')")

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
        "imports": imports,
        "exports": exports,
        "classes": classes,
        "functions": functions,
    }
