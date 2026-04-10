"""Analyze command for codebase analysis."""

from typing import Dict, Any, Optional

import json

from ..analysis.codebase import scan_codebase
from ..analysis.extractor import extract_project_metadata, extract_api_endpoints, extract_setup_instructions
from ..ai.client import call_ai_model, AIProvider, extract_json_response
from ..ai.prompts import (
    create_analysis_prompt,
    create_readme_prompt,
    create_diagram_prompt,
    create_api_docs_prompt,
)
from .generate import generate_readme, generate_diagram, generate_api_docs, generate_setup_instructions


def analyze_codebase(path: str) -> Dict[str, Any]:
    """
    Analyze a codebase and return structured information.

    Args:
        path: Path to the codebase root

    Returns:
        Dictionary containing analysis results
    """
    # Scan codebase
    codebase_info = scan_codebase(path)

    # Extract metadata
    metadata = extract_project_metadata(path)

    # Extract API endpoints
    endpoints = extract_api_endpoints(path)

    # Extract setup instructions
    setup = extract_setup_instructions(path)

    return {
        "codebase": codebase_info,
        "metadata": metadata,
        "endpoints": endpoints,
        "setup": setup,
    }


def format_analysis(analysis: Dict[str, Any]) -> str:
    """
    Format analysis results for display.

    Args:
        analysis: Analysis results dictionary

    Returns:
        Formatted string output
    """
    lines = [
        "=== Codebase Analysis ===",
        "",
        f"Path: {analysis['codebase']['path']}",
        f"Total Files: {len(analysis['codebase']['files'])}",
        f"Languages: {', '.join(analysis['codebase']['languages'].keys())}",
        "",
        "=== Project Metadata ===",
        "",
        f"Name: {analysis['metadata'].get('name', 'Unknown')}",
        f"Description: {analysis['metadata'].get('description', 'No description')}",
        f"Version: {analysis['metadata'].get('version', 'Unknown')}",
        "",
        "=== File Distribution ===",
        "",
    ]

    for lang, info in analysis['codebase']['languages'].items():
        lines.append(f"{lang.upper()}: {info['count']} files")

    lines.extend([
        "",
        "=== Root Files ===",
        "",
    ])

    for file in analysis['codebase']['root_files'][:10]:
        lines.append(f"- {file}")

    if len(analysis['codebase']['root_files']) > 10:
        lines.append(f"... and {len(analysis['codebase']['root_files']) - 10} more")

    lines.extend([
        "",
        "=== API Endpoints ===",
        "",
    ])

    endpoints = analysis.get('endpoints', [])
    if endpoints:
        for ep in endpoints[:10]:
            lines.append(f"- {ep.get('method', 'GET').upper()} {ep.get('path', '')}")
    else:
        lines.append("No API endpoints detected")

    lines.extend([
        "",
        "=== Analysis Complete ===",
        ""
    ])

    return "\n".join(lines)


def analyze_and_generate(path: str, output_format: str = "text", verbose: bool = False) -> str:
    """
    Analyze codebase and generate documentation.

    Args:
        path: Path to the codebase
        output_format: Output format ("text" or "json")
        verbose: Whether to show verbose output

    Returns:
        Documentation output
    """
    # Step 1: Analyze codebase
    analysis = analyze_codebase(path)

    if verbose:
        print(format_analysis(analysis))

    # Step 2: Generate README
    readme = generate_readme(
        analysis['codebase'],
        analysis['metadata'],
        analysis
    )

    # Step 3: Generate diagram
    diagram = generate_diagram(
        analysis['codebase'],
        analysis
    )

    # Step 4: Generate API docs (if endpoints exist)
    api_docs = ""
    if analysis.get('endpoints'):
        api_docs = generate_api_docs(analysis['endpoints'])

    # Step 5: Generate setup instructions
    setup = generate_setup_instructions(path)

    # Combine all outputs
    output = []

    if verbose:
        output.append("=== Generated Documentation ===")
        output.append("")

    output.append(readme)
    output.append("")
    output.append("=== Architecture Diagram ===")
    output.append("")
    output.append(diagram)
    output.append("")
    output.append("=== API Documentation ===")
    output.append("")
    output.append(api_docs)
    output.append("")
    output.append("=== Setup Instructions ===")
    output.append("")
    output.append(setup)

    if output_format == "json":
        return json.dumps({
            "readme": readme,
            "diagram": diagram,
            "api_docs": api_docs,
            "setup": setup,
        }, indent=2)

    return "\n".join(output)
