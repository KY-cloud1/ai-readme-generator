"""Generate command for producing documentation."""

from typing import Dict, Any, Optional

from ..analysis.extractor import (
    extract_setup_instructions,
)
from ..ai.client import call_ai_model, AIProvider, extract_json_response, AuthenticationError
from ..ai.prompts import (
    create_readme_prompt,
    create_diagram_prompt,
    create_api_docs_prompt,
)
from ..analysis.agent import AgentResult


def generate_readme(
    codebase_info: Dict[str, Any],
    metadata: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:
    """
    Generate a README.md file.

    Args:
        codebase_info: Codebase information from scanning
        metadata: Project metadata
        analysis: Optional AI analysis results
        agent_context: Optional dictionary of agent results for enhanced context

    Returns:
        Generated README content

    Raises:
        ValueError: If codebase_info or metadata is empty
    """
    if not codebase_info or not metadata:
        raise ValueError("codebase_info and metadata cannot be empty")
    try:
        messages = [
            {"role": "user", "content": create_readme_prompt(
                codebase_info,
                metadata,
                analysis or {}
            )},
        ]

        response = call_ai_model(messages, AIProvider.ANTHROPIC)
        result = extract_json_response(response)

        if result is None:
            return generate_basic_readme(codebase_info, metadata)

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
        Basic README content with project structure and file listing
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
    analysis: Optional[Dict[str, Any]] = None,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:
    """
    Generate ASCII architecture diagram.

    Args:
        codebase_info: Codebase information from scanning
        analysis: Optional AI analysis results with patterns and entry points
        agent_context: Optional dictionary of agent results for enhanced context

    Returns:
        ASCII diagram content with proper escaping

    Raises:
        AuthenticationError: If authentication fails
        ValueError: If codebase_info is empty or invalid
    """
    if not codebase_info:
        raise ValueError("codebase_info cannot be empty")
    try:
        messages = [
            {"role": "user", "content": create_diagram_prompt(codebase_info, analysis or {})},
        ]

        response = call_ai_model(messages, AIProvider.ANTHROPIC)
        # Handle long response extraction
        choices = response.get("choices", [{}])
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content", "") if message else ""

        # Escape special characters for terminal output
        escaped_content = content.replace("`", " ` ")

        return escaped_content
    except AuthenticationError:
        return generate_basic_diagram(codebase_info, agent_context)
    except Exception:
        # Log error and return basic diagram on any other error
        return generate_basic_diagram(codebase_info, agent_context)


def generate_basic_diagram(
    codebase_info: Dict[str, Any],
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:
    """
        Generate a basic ASCII diagram without AI.

        Args:
            codebase_info: Codebase information from scanning
            agent_context: Optional dictionary of agent results for enhanced
                context with patterns and entry points

        Returns:
            Basic ASCII diagram with actual codebase structure
    """
    lines = [
        "```",
        "",
        "    [Project Root]",
    ]

    # Add actual file counts from codebase_info
    for lang, info in codebase_info.get("languages", {}).items():
        lines.append(f"    ├── [{lang.upper()}/]")
        lines.append(f"    │   └── {info.get('count', 0)} files")

    # Add entry points from agent_context if available
    # agent_context is Dict[str, AgentResult], extract metadata from CodebaseAnalyst result
    if agent_context:
        # Look for entry_points in any AgentResult's metadata
        entry_points = []
        for result in agent_context.values():
            if result.success and result.metadata:
                entry_points = result.metadata.get("entry_points", [])
                break
        if entry_points:
            lines.append("")
            lines.append("    Entry Points:")
            for ep in entry_points[:5]:
                lines.append(f"    ├── [⚡ {ep}]")

    # Add top-level files if available
    for file in codebase_info.get("files", [])[:5]:
        lines.append(f"    ├── [{file.get('path', 'file')}]")

    lines.extend([
        "",
        "```",
        "",
        "# Basic ASCII Diagram",
        "",
        "This is a basic diagram. For detailed architecture diagrams,",
        "please set up an AI API key (Anthropic or OpenAI).",
        "",
    ])

    return "\n".join(lines)


def generate_api_docs(
    codebase_info: Dict[str, Any],
    endpoints: Optional[list] = None,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:
    """
    Generate API documentation.

    Args:
        codebase_info: Codebase information from scanning
        endpoints: Optional list of API endpoints
        agent_context: Optional dictionary of agent results for enhanced context

    Returns:
        API documentation content

    Raises:
        ValueError: If endpoints is None or empty
    """
    if endpoints is None or len(endpoints) == 0:
        raise ValueError("endpoints cannot be empty")

    try:
        messages = [
            {"role": "user", "content": create_api_docs_prompt(codebase_info, endpoints)},
        ]

        response = call_ai_model(messages, AIProvider.ANTHROPIC)
        # Handle long response extraction
        choices = response.get("choices", [{}])
        message = choices[0].get("message", {}) if choices else {}
        content = message.get("content", "") if message else ""

        return content
    except AuthenticationError:
        return generate_basic_api_docs(endpoints, agent_context)


def generate_basic_api_docs(
    endpoints: list,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:
    """
        Generate basic API docs without AI.

        Args:
            endpoints: List of API endpoints
            agent_context: Optional dictionary of agent results for enhanced
                context with patterns and metadata

        Returns:
        Basic API documentation with endpoint listing
    """
    lines = [
        "## API Reference",
        "",
        "### Endpoints",
        "",
    ]

    # Add summary from agent_context if available
    # agent_context is Dict[str, AgentResult], extract metadata from APIExtractor result
    if agent_context:
        metadata = {}
        for result in agent_context.values():
            if result.success and result.metadata:
                metadata = result.metadata
                break
        if metadata:
            lines.append("")
            lines.append("### Summary")
            lines.append("")
            for key, value in metadata.items():
                if key not in ["endpoints", "grouped"]:
                    lines.append(f"- **{key}**: {value}")
            lines.append("")

    for ep in endpoints[:10]:
        lines.append(f"#### {ep.get('method', 'GET').upper()} {ep.get('path', '')}")
        lines.append("")
        lines.append(f"- **Source**: {ep.get('source', 'Unknown')}")
        lines.append(f"- **Description**: {ep.get('description', 'No description')}")
        lines.append(f"- **Params**: {ep.get('params', [])}")
        lines.append(f"- **Response**: {ep.get('response', 'No response schema')}")
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
