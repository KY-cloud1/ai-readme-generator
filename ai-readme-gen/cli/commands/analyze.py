"""Analyze command for codebase analysis."""

from typing import Dict, Any

import json

from ..analysis.codebase import scan_codebase
from ..analysis.extractor import extract_project_metadata, extract_api_endpoints
from ..analysis.agent import (
    run_agent_pipeline,
    AgentResult,
)
from .generate import generate_readme, generate_diagram, generate_api_docs


def analyze_codebase(path: str, use_agents: bool = False) -> Dict[str, Any]:
    """
    Analyze a codebase and return structured information.

    Args:
        path: Path to the codebase root
        use_agents: Whether to use agent simulation

    Returns:
        Dictionary containing analysis results

    Raises:
        FileNotFoundError: If path does not exist
    """
    from pathlib import Path

    if not Path(path).exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    # Scan codebase
    codebase_info = scan_codebase(path)

    # Extract metadata
    metadata = extract_project_metadata(path)

    # Extract API endpoints
    endpoints = extract_api_endpoints(path)

    # Run agent simulation if enabled
    agent_results = {}
    if use_agents:
        context = {
            "codebase": codebase_info,
            "metadata": metadata,
            "endpoints": endpoints,
        }
        agent_results = run_agent_pipeline(context)

    return {
        "codebase": codebase_info,
        "metadata": metadata,
        "endpoints": endpoints,
        "agents": agent_results,
    }


def format_analysis(analysis: Dict[str, Any]) -> str:
    """Format analysis results for display.

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
    if analysis.get('agents'):
        lines.extend([
            "",
            "=== Agent Simulation Results ===",
            "",
        ])
        for agent_name, result in analysis['agents'].items():
            lines.append(f"--- {agent_name} ---")

            # Handle both AgentResult objects and dict results
            if isinstance(result, AgentResult):
                if not result.success:
                    lines.append(f"Agent {agent_name} failed")
                    lines.append("")
                    continue
                meta = result.metadata
            elif isinstance(result, dict):
                if not result.get('success', True):
                    lines.append(f"Agent {agent_name} failed")
                    lines.append("")
                    continue
                meta = result
            else:
                lines.append("No metadata available")
                lines.append("")
                continue

            # Only display if there's meaningful data
            displayed = False
            patterns = meta.get('patterns')
            if patterns:
                lines.append(f"Patterns: {', '.join(patterns)}")
                displayed = True
            tech_stack = meta.get('tech_stack')
            if tech_stack:
                lines.append(f"Tech Stack: {', '.join(tech_stack)}")
                displayed = True
            file_distribution = meta.get('file_distribution')
            if file_distribution:
                lines.append("File Distribution:")
                for lang, files in file_distribution.items():
                    lines.append(f"  - {lang}: {len(files)} files")
                displayed = True
            entry_points = meta.get('entry_points')
            if entry_points:
                lines.append(f"Entry Points: {', '.join(entry_points)}")
                displayed = True
            dependencies = meta.get('dependencies')
            if dependencies:
                lines.append(f"Dependencies: {', '.join(dependencies)}")
                displayed = True

            if not displayed:
                lines.append("No detailed output")
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

    Raises:
        FileNotFoundError: If path does not exist
    """

    # Step 1: Analyze codebase
    analysis: Dict[str, Any] = analyze_codebase(path, use_agents)

    if verbose:
        print(format_analysis(analysis))

    # Step 2: Generate README (using AI or fallback)
    technicalwriter_result = analysis.get('agents', {}).get('TechnicalWriter')
    tw_metadata = None
    if technicalwriter_result and technicalwriter_result.success:
        tw_metadata = technicalwriter_result.metadata
    readme = generate_readme(
        analysis['codebase'],
        analysis['metadata'],
        tw_metadata if use_agents else analysis,
        analysis.get('agents') if use_agents else None
    )

    # Step 3: Generate diagram (using AI or fallback)
    architect_result = analysis.get('agents', {}).get('Architect')
    arch_metadata = None
    if architect_result and architect_result.success:
        arch_metadata = architect_result.metadata
    diagram = generate_diagram(
        analysis['codebase'],
        arch_metadata if use_agents else analysis,
        analysis.get('agents') if use_agents else None
    )

    # Step 4: Generate API docs (if endpoints exist)
    api_docs = ""
    if analysis.get("endpoints"):
        api_docs = generate_api_docs(
            analysis["codebase"],
            analysis["endpoints"],
            analysis.get("agents") if use_agents else None
        )

    # Step 5: Generate setup instructions (result not used - removed)

    # Combine all outputs
    output: list = []

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

    if output_format == "json":
        return json.dumps({
            "readme": readme,
            "diagram": diagram,
            "api_docs": api_docs,
            "agents": analysis.get('agents', {}),
        }, indent=2)

    return "\n".join(output)
