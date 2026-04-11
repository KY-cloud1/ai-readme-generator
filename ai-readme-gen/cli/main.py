#!/usr/bin/env python3
"""AI README Generator CLI - Entry point."""

import os
from typing import Any, Dict, Optional

import click
from .commands.analyze import analyze_and_generate, format_analysis
from .commands.config import get_config, validate_config


def set_model_option(ctx: Any, param: Any, value: Optional[str]) -> Optional[str]:
    """Custom option handler to set AI_MODEL environment variable."""
    if value:
        os.environ["AI_MODEL"] = value
    return value


@click.group()
@click.version_option(version="0.1.0", prog_name="ai-readme-gen")
@click.option("--model", "-m", envvar="AI_MODEL", help="AI model to use")
@click.option("--help", "-h", "show_help", is_flag=True, help="Show help and exit")
def main(model, show_help):
    """AI-powered README generator for codebases.

    Analyzes Python and JavaScript/TypeScript projects to generate:
    - Comprehensive README.md files
    - ASCII architecture diagrams
    - API documentation
    - Setup instructions

    Environment variables:
      AI_PROVIDER: anthropic | openai | local (default: anthropic)
      ANTHROPIC_API_KEY: Your Anthropic API key (required for Anthropic provider)
      OPENAI_API_KEY: Your OpenAI API key (required for OpenAI provider)
      AI_MODEL: Model to use (default depends on provider)
      USE_AGENTS: Use agent simulation for analysis (default: false)

    Exit codes:
      0: Success
      1: Configuration error or missing API key
      2: Invalid arguments or usage error
    """
    # Show help if requested
    if show_help:
        help_text = """
Usage: ai-readme-gen [OPTIONS] COMMAND [ARGS]...

AI-powered README generator for codebases.

Commands:
  analyze   Analyze a codebase and generate documentation
  diagram   Generate ASCII architecture diagram
  api       Extract API documentation
  setup     Generate setup instructions
  --help    Show this message and exit.

Environment Variables:
  AI_PROVIDER          AI provider to use (anthropic, openai, local)
  ANTHROPIC_API_KEY   Anthropic API key (required for Anthropic provider)
  OPENAI_API_KEY      OpenAI API key (required for OpenAI provider)
  AI_MODEL             AI model to use
  USE_AGENTS           Use agent simulation for analysis (default: false)

Examples:
  ai-readme-gen analyze /path/to/project
  ai-readme-gen analyze /path/to/project --output README.md
  ai-readme-gen diagram /path/to/project --verbose
  ai-readme-gen api /path/to/project --use-agents
"""
        click.echo(help_text)
        raise click.exceptions.Exit(0)

    # Validate configuration
    if not validate_config():
        click.echo(
            "Error: No API key configured. "
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.",
            err=True
        )
        click.echo(
            "\nExample: export ANTHROPIC_API_KEY=your_api_key",
            err=True
        )
        raise click.exceptions.Exit(1)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text",
              help="Output format (default: text)")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
@click.option("--use-agents", is_flag=True, help="Use agent simulation for analysis")
def analyze(path, output, format, verbose, use_agents):
    """Analyze a codebase and generate documentation.

    PATH: Path to the project directory to analyze
    """
    # Validate path
    if not os.path.exists(path):
        click.echo(f"Error: Path does not exist: {path}", err=True)
        return 1

    # Run analysis
    output_content = analyze_and_generate(path, format, verbose, use_agents)
    if not output_content:
        click.echo("Error: Failed to generate documentation", err=True)
        return 1

    # Write output if specified
    if output:
        with open(output, 'w') as f:
            f.write(output_content)
        click.echo(f"Documentation written to: {output}")
    else:
        # Escape output for safe terminal display
        click.echo(output_content, nl=False)

    return 0


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
@click.option("--use-agents", is_flag=True, help="Use agent simulation for analysis")
def diagram(path, output, verbose, use_agents):
    """Generate ASCII architecture diagram for a codebase.

    PATH: Path to the project directory to analyze
    """
    try:
        analysis = analyze_codebase(path, use_agents=use_agents)
        if not analysis:
            click.echo("Error: Failed to analyze codebase", err=True)
            return 1
        diagram = generate_diagram(analysis['codebase'], analysis.get('agents', {}).get('Architect') or analysis)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        return 2
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1

    if not diagram:
        click.echo("Error: Failed to generate diagram", err=True)
        return 1

    if output:
        with open(output, 'w') as f:
            f.write(diagram)
        click.echo(f"Diagram written to: {output}")
    else:
        if verbose:
            # Use nlwrap for proper terminal wrapping and escaping
            from nlwrap import nlwrap
            click.echo("".join(nlwrap(diagram)), nl=False)
        else:
            click.echo(f"Diagram generated: {len(diagram)} characters", nl=False)

    return 0


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
@click.option("--use-agents", is_flag=True, help="Use agent simulation for analysis")
def api(path, output, verbose, use_agents):
    """Extract API documentation from a codebase.

    PATH: Path to the project directory to analyze
    """
    try:
        analysis = analyze_codebase(path, use_agents=use_agents)
        if not analysis:
            click.echo("Error: Failed to analyze codebase", err=True)
            return 1
        api_docs = generate_api_docs(analysis.get('endpoints', []))
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        return 2
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 2
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1

    if not api_docs:
        click.echo("Error: Failed to generate API documentation", err=True)
        return 1

    if output:
        with open(output, 'w') as f:
            f.write(api_docs)
        click.echo(f"API docs written to: {output}")
    else:
        if verbose:
            # Use nlwrap for proper terminal wrapping and escaping
            from nlwrap import nlwrap
            click.echo("".join(nlwrap(api_docs)), nl=False)
        else:
            click.echo(f"API docs generated: {len(api_docs)} characters", nl=False)

    return 0


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def setup(path, output):
    """Generate setup instructions for a codebase.

    PATH: Path to the project directory to analyze
    """
    try:
        setup = generate_setup_instructions(path)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        return 2
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1

    if output:
        with open(output, 'w') as f:
            f.write(setup)
        click.echo(f"Setup instructions written to: {output}")
    else:
        click.echo(setup, nl=False)

    return 0


def analyze_codebase(path: str, use_agents: bool = False) -> Dict[str, Any]:
    """Analyze a codebase and return structured information.

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

    return {"codebase": codebase_info, "metadata": metadata, "endpoints": endpoints, "agents": agent_results}


def generate_diagram(codebase_info: Dict[str, Any], analysis: Any) -> str:
    """Generate an ASCII architecture diagram.

    Args:
        codebase_info: Codebase information from scanning
        analysis: Optional analysis results

    Returns:
        Generated ASCII diagram

    Raises:
        ValueError: If codebase_info is empty or invalid
    """
    from .commands.generate import generate_diagram as _generate

    if not codebase_info:
        raise ValueError("codebase_info cannot be empty")

    return _generate(codebase_info, analysis)


def generate_api_docs(endpoints: Optional[List[Dict[str, Any]]]) -> str:
    """Generate API documentation from endpoints.

    Args:
        endpoints: List of API endpoints

    Returns:
        Generated API documentation

    Raises:
        ValueError: If endpoints is None or empty
    """
    from .commands.generate import generate_api_docs as _generate

    if endpoints is None or len(endpoints) == 0:
        raise ValueError("endpoints cannot be empty")

    return _generate(endpoints)


def generate_setup_instructions(path: str) -> str:
    """Generate setup instructions for a project.

    Args:
        path: Path to the project

    Returns:
        Generated setup instructions

    Raises:
        FileNotFoundError: If the path does not exist
    """
    from .commands.generate import generate_setup_instructions as _generate

    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    return _generate(path)


if __name__ == "__main__":
    main()
