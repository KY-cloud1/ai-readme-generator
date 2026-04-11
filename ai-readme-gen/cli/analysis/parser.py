"""Language-specific parsing utilities."""

from pathlib import Path
from typing import Dict, List, Any

from .codebase import parse_python_file, parse_javascript_file


def parse_file(file_path: str) -> Dict[str, Any]:
    """Parse a file based on its language.

    Args:
        file_path: Path to the file to parse

    Returns:
        Dictionary containing parsed information for the appropriate language
    """
    ext = Path(file_path).suffix.lower()

    if ext == '.py':
        return parse_python_file(file_path)
    elif ext in {'.js', '.jsx', '.ts', '.tsx'}:
        return parse_javascript_file(file_path)
    else:
        return {
            "path": file_path,
            "language": "other",
            "extension": ext,
            "parsing": "not_supported",
        }


def extract_dependencies(file_path: str) -> List[str]:
    """Extract dependencies from a file.

    Args:
        file_path: Path to the file to extract dependencies from

    Returns:
        List of dependency names/paths imported in the file

    Raises:
        FileNotFoundError: If the file does not exist
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    ext = path.suffix.lower()

    if ext == '.py':
        # Extract Python imports
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        deps = []
        # Standard imports
        for match in re.finditer(r'^import\s+(\w+)', content, re.MULTILINE):
            deps.append(match.group(1))
        # From imports
        for match in re.finditer(r'^from\s+(\w+)\s+import', content, re.MULTILINE):
            deps.append(match.group(1))

        return deps

    elif ext in {'.js', '.jsx', '.ts', '.tsx'}:
        # Extract JS/TS imports
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        deps = []
        # ESM imports
        for match in re.finditer(r'from\s+[\'"]([^\'"]+)[\'"]', content):
            deps.append(match.group(1))
        # CommonJS require
        for match in re.finditer(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content):
            deps.append(match.group(1))

        return deps

    return []


def extract_project_dependencies(path: str) -> Dict[str, List[str]]:
    """Extract project-level dependencies.

    Args:
        path: Path to the project root

    Returns:
        Dictionary of dependency files with their dependencies
    """
    deps_by_file = {}

    # Check for common dependency files
    dep_files = {
        'pyproject.toml': 'python',
        'package.json': 'javascript',
        'requirements.txt': 'python',
        'setup.py': 'python',
    }

    path = Path(path)
    for dep_file, lang in dep_files.items():
        dep_path = path / dep_file
        if dep_path.exists():
            try:
                deps_by_file[str(dep_path)] = extract_dependencies(str(dep_path))
            except FileNotFoundError:
                # Skip files that can't be read
                pass

    return deps_by_file
