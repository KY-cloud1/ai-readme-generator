"""Analyze command for codebase analysis."""

from typing import Dict, Any, Optional

import json

from ..analysis.codebase import scan_codebase
from ..analysis.extractor import extract_project_metadata, extract_api_endpoints, extract_setup_instructions
from ..analysis.agent import (
    create_agent_pipeline,
    run_agent_pipeline,
    AgentResult,
    Agent,
    CodebaseAnalyst,
    Architect,
    TechnicalWriter,
    APIExtractor as AgentAPIExtractor,
    Reviewer,
)
from ..ai.client import call_ai_model, AIProvider, extract_json_response, AuthenticationError
from ..ai.prompts import (
    create_analysis_prompt,
    create_readme_prompt,
    create_diagram_prompt,
    create_api_docs_prompt,
)
from .generate import generate_readme, generate_diagram, generate_api_docs, generate_setup_instructions


def analyze_codebase(path: str, use_agents: bool = False) -> Dict[str, Any]:
    """
    Analyze a codebase and return structured information.

    Args:
        path: Path to the codebase root
        use_agents: Whether to use agent simulation

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

    # Run agent simulation if enabled
    agent_results = {}
    if use_agents:
        context = {
            "codebase": codebase_info,
            "metadata": metadata,
            "endpoints": endpoints,
            "setup": setup,
        }
        agent_results = run_agent_pipeline(context)

    return {
        "codebase": codebase_info,
        "metadata": metadata,
        "endpoints": endpoints,
        "setup": setup,
        "agents": agent_results,
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

    # Include agent results if available
    if 'agents' in analysis:
        lines.extend([
            "",
            "=== Agent Simulation Results ===",
            "",
        ])
        for agent_name, result in analysis['agents'].items():
            lines.append(f"--- {agent_name} ---")
            if hasattr(result, 'metadata'):
                meta = result.metadata
                if meta.get('patterns'):
                    lines.append(f"Patterns: {', '.join(meta['patterns'])}")
                if meta.get('tech_stack'):
                    lines.append(f"Tech Stack: {', '.join(meta['tech_stack'])}")
                if meta.get('file_distribution'):
                    lines.append("File Distribution:")
                    for lang, files in meta['file_distribution'].items():
                        lines.append(f"  - {lang}: {len(files)} files")
                if meta.get('entry_points'):
                    lines.append(f"Entry Points: {', '.join(meta['entry_points'])}")
                if meta.get('dependencies'):
                    lines.append(f"Dependencies: {', '.join(meta['dependencies'])}")
            lines.append("")

    lines.extend([
        "",
        "=== Analysis Complete ===",
        ""
    ])

    return "\n".join(lines)


def analyze_and_generate(
    path: str,
    output_format: str = "text",
    verbose: bool = False,
    use_agents: bool = False
) -> str:
    """
    Analyze codebase and generate documentation.

    Args:
        path: Path to the codebase
        output_format: Output format ("text" or "json")
        verbose: Whether to show verbose output
        use_agents: Whether to use agent simulation

    Returns:
        Documentation output
    """
    # Step 1: Analyze codebase
    analysis = analyze_codebase(path, use_agents)

    if verbose:
        print(format_analysis(analysis))

    # Step 2: Generate README (using AI or fallback)
    readme = generate_readme(
        analysis['codebase'],
        analysis['metadata'],
        analysis.get('agents', {}).get('TechnicalWriter', {}).metadata if use_agents else analysis
    )

    # Step 3: Generate diagram (using AI or fallback)
    diagram = generate_diagram(
        analysis['codebase'],
        analysis.get('agents', {}).get('Architect', {}).metadata if use_agents else analysis
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
            "agents": analysis.get('agents', {}),
        }, indent=2)

    return "\n".join(output)
