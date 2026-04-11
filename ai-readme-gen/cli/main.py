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


@main.group()
@click.version_option(version="0.1.0", prog_name="ai-readme-gen")
@click.option("--model", "-m", envvar="AI_MODEL", help="AI model to use")
def main(model):
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
    """
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
        raise click.exceptions.Exit(1)

    # Run analysis
    output_content = analyze_and_generate(path, format, verbose, use_agents)
    if not output_content:
        click.echo("Error: Failed to generate documentation", err=True)
        raise click.exceptions.Exit(1)

    # Write output if specified
    if output:
        with open(output, 'w') as f:
            f.write(output_content)
        click.echo(f"Documentation written to: {output}")
    else:
        click.echo(output_content)


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
            raise click.exceptions.Exit(1)
        diagram = generate_diagram(analysis['codebase'], analysis.get('agents', {}).get('Architect') or analysis)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.exceptions.Exit(1)

    if not diagram:
        click.echo("Error: Failed to generate diagram", err=True)
        raise click.exceptions.Exit(1)

    if output:
        with open(output, 'w') as f:
            f.write(diagram)
        click.echo(f"Diagram written to: {output}")
    else:
        if verbose:
            # Use nlwrap for proper terminal wrapping and escaping
            from nlwrap import nlwrap
            click.echo("".join(nlwrap(diagram)))
        else:
            click.echo(f"Diagram generated: {len(diagram)} characters")


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
            raise click.exceptions.Exit(1)
        api_docs = generate_api_docs(analysis.get('endpoints', []))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.exceptions.Exit(1)

    if not api_docs:
        click.echo("Error: Failed to generate API documentation", err=True)
        raise click.exceptions.Exit(1)

    if output:
        with open(output, 'w') as f:
            f.write(api_docs)
        click.echo(f"API docs written to: {output}")
    else:
        if verbose:
            # Use nlwrap for proper terminal wrapping and escaping
            from nlwrap import nlwrap
            click.echo("".join(nlwrap(api_docs)))
        else:
            click.echo(f"API docs generated: {len(api_docs)} characters")


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def setup(path, output):
    """Generate setup instructions for a codebase.

    PATH: Path to the project directory to analyze
    """
    setup = generate_setup_instructions(path)

    if output:
        with open(output, 'w') as f:
            f.write(setup)
        click.echo(f"Setup instructions written to: {output}")
    else:
        click.echo(setup)


def analyze_codebase(path: str, use_agents: bool = False) -> Dict[str, Any]:
    """Helper function for standalone commands.

    Args:
        path: Path to the project directory
        use_agents: Whether to use agent simulation for analysis

    Returns:
        Dictionary with codebase analysis results
    """
    from .commands.analyze import analyze_codebase as _analyze
    return _analyze(path, use_agents)


def generate_diagram(codebase_info: Dict[str, Any], analysis: Any) -> str:
    """Helper function for standalone commands.

    Args:
        codebase_info: Codebase information from scanning
        analysis: Optional analysis results

    Returns:
        Generated ASCII diagram
    """
    from .commands.generate import generate_diagram as _generate
    return _generate(codebase_info, analysis)


def generate_api_docs(endpoints: List[Dict[str, Any]]) -> str:
    """Helper function for standalone commands.

    Args:
        endpoints: List of API endpoints

    Returns:
        Generated API documentation
    """
    from .commands.generate import generate_api_docs as _generate
    return _generate(endpoints)


def generate_setup_instructions(path: str) -> str:
    """Helper function for standalone commands.

    Args:
        path: Path to the project

    Returns:
        Generated setup instructions
    """
    from .commands.generate import generate_setup_instructions as _generate
    return _generate(path)


if __name__ == "__main__":
    main()
