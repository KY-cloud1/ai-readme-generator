"""Generate command for producing documentation."""

import json
from typing import Dict, Any, Optional

from ..analysis.codebase import scan_codebase
from ..analysis.extractor import (
    extract_project_metadata,
    extract_api_endpoints,
    extract_setup_instructions,
)
from ..ai.client import call_ai_model, AIProvider, extract_json_response, AuthenticationError
from ..ai.prompts import (
    create_analysis_prompt,
    create_readme_prompt,
    create_diagram_prompt,
    create_api_docs_prompt,
    create_review_prompt,
)


def generate_readme(
    codebase_info: Dict[str, Any],
    metadata: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a README.md file.

    Args:
        codebase_info: Codebase information from scanning
        metadata: Project metadata
        analysis: Optional AI analysis results

    Returns:
        Generated README content
    """
    try:
        messages = [
            {"role": "user", "content": create_readme_prompt(codebase_info, metadata, analysis or {})},
        ]

        response = call_ai_model(messages, AIProvider.ANTHROPIC)
        result = extract_json_response(response)

        if result:
            return result.get("readme", str(result))

        return "# Project Documentation\n\n" + str(result)
    except AuthenticationError:
        # Generate a basic README when AI is not available
        return generate_basic_readme(codebase_info, metadata)


def generate_basic_readme(codebase_info: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """
    Generate a basic README without AI.

    Args:
        codebase_info: Codebase information from scanning
        metadata: Project metadata

    Returns:
        Basic README content
    """
    lines = [
        f"# {metadata.get('name', 'Project') or 'Project'}",
        "",
        metadata.get("description", "No description available.") or "No description available.",
        "",
        "## Project Structure",
        "",
    ]

    for lang, info in codebase_info.get("languages", {}).items():
        lines.append(f"- **{lang.upper()}**: {info['count']} files")

    lines.extend([
        "",
        "## Files",
        "",
    ])

    for file in codebase_info.get("files", [])[:20]:
        lines.append(f"- `{file['path']}`")

    lines.extend([
        "",
        "## Setup",
        "",
        "See the setup instructions section below for detailed installation steps.",
        "",
    ])

    return "\n".join(lines)


def generate_diagram(
    codebase_info: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate ASCII architecture diagram.

    Args:
        codebase_info: Codebase information from scanning
        analysis: Optional AI analysis results

    Returns:
        ASCII diagram content
    """
    try:
        messages = [
            {"role": "user", "content": create_diagram_prompt(codebase_info, analysis or {})},
        ]

        response = call_ai_model(messages, AIProvider.ANTHROPIC)
        content = response.get("content", response.get("choices", [{}])[0].get("message", {}).get("content", ""))

        return content
    except AuthenticationError:
        return generate_basic_diagram(codebase_info)


def generate_basic_diagram(codebase_info: Dict[str, Any]) -> str:
    """
    Generate a basic ASCII diagram without AI.

    Args:
        codebase_info: Codebase information from scanning

    Returns:
        Basic ASCII diagram
    """
    lines = [
        "```",
        "",
        "    [Project Root]",
        "    ├── [src/]",
        "    │   └── [main modules]",
        "    ├── [tests/]",
        "    │   └── [test files]",
        "    ├── [docs/]",
        "    │   └── [documentation]",
        "    └── [config/]",
        "        └── [configuration files]",
        "",
        "```",
        "",
        "# Basic ASCII Diagram",
        "",
        "This is a basic diagram. For detailed architecture diagrams,",
        "please set up an AI API key (Anthropic or OpenAI).",
        "",
    ]

    return "\n".join(lines)


def generate_api_docs(
    endpoints: Optional[list] = None
) -> str:
    """
    Generate API documentation.

    Args:
        endpoints: Optional list of API endpoints

    Returns:
        API documentation content
    """
    if not endpoints:
        return "No API endpoints found.\n\n## API Reference\n\nAPI documentation not available for this project."

    try:
        messages = [
            {"role": "user", "content": create_api_docs_prompt({}, endpoints)},
        ]

        response = call_ai_model(messages, AIProvider.ANTHROPIC)
        content = response.get("content", response.get("choices", [{}])[0].get("message", {}).get("content", ""))

        return content
    except AuthenticationError:
        return generate_basic_api_docs(endpoints)


def generate_basic_api_docs(endpoints: list) -> str:
    """
    Generate basic API docs without AI.

    Args:
        endpoints: List of API endpoints

    Returns:
        Basic API documentation
    """
    lines = [
        "## API Reference",
        "",
        "### Endpoints",
        "",
    ]

    for ep in endpoints[:10]:
        lines.append(f"#### {ep.get('method', 'GET').upper()} {ep.get('path', '')}")
        lines.append("")
        lines.append(f"- **Source**: {ep.get('source', 'Unknown')}")
        lines.append("")

    lines.extend([
        "",
        "### Notes",
        "",
        "This is a basic API documentation.",
        "For detailed API documentation, please set up an AI API key.",
        "",
    ])

    return "\n".join(lines)


def generate_setup_instructions(
    path: str
) -> str:
    """
    Generate setup instructions.

    Args:
        path: Path to the project

    Returns:
        Setup instructions content
    """
    instructions = extract_setup_instructions(path)

    lines = [
        "## Setup Instructions",
        "",
    ]

    if instructions.get("installation"):
        lines.append("### Installation")
        lines.append("")
        for inst in instructions["installation"]:
            lines.append(f"- {inst}")
        lines.append("")

    if instructions.get("dependencies"):
        lines.append("### Dependencies")
        lines.append("")
        lines.append("**Python:**")
        for dep in instructions["dependencies"]:
            if "pip" in dep:
                lines.append(f"- {dep}")
        lines.append("")

    lines.append("### Environment Variables")
    lines.append("")
    if instructions.get("environment"):
        for env in instructions["environment"]:
            lines.append(f"- {env}")
    else:
        lines.append("(None detected)")

    return "\n".join(lines)
