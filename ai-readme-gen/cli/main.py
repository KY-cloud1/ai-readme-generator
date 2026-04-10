#!/usr/bin/env python3
"""AI README Generator CLI - Entry point."""

import os
import sys
from typing import Any, Dict

import click
from .commands.analyze import analyze_and_generate, format_analysis
from .commands.config import get_config, validate_config


def set_model_option(ctx, param, value):
    """Custom option handler to set AI_MODEL environment variable."""
    if value:
        os.environ["AI_MODEL"] = value
    return value


@click.group()
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
      ANTHROPIC_API_KEY: Your Anthropic API key
      OPENAI_API_KEY: Your OpenAI API key
      AI_MODEL: Model to use (default depends on provider)
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
def analyze(path, output, format, verbose):
    """Analyze a codebase and generate documentation.

    PATH: Path to the project directory to analyze
    """
    # Validate path
    if not os.path.exists(path):
        click.echo(f"Error: Path does not exist: {path}", err=True)
        raise click.exceptions.Exit(1)

    # Run analysis
    output_content = analyze_and_generate(path, format, verbose)

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
def diagram(path, output):
    """Generate ASCII architecture diagram for a codebase.

    PATH: Path to the project directory to analyze
    """
    analysis = analyze_codebase(path)
    diagram = generate_diagram(analysis['codebase'], analysis)

    if output:
        with open(output, 'w') as f:
            f.write(diagram)
        click.echo(f"Diagram written to: {output}")
    else:
        click.echo(diagram)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def api(path, output):
    """Extract API documentation from a codebase.

    PATH: Path to the project directory to analyze
    """
    analysis = analyze_codebase(path)
    api_docs = generate_api_docs(analysis.get('endpoints'))

    if output:
        with open(output, 'w') as f:
            f.write(api_docs)
        click.echo(f"API docs written to: {output}")
    else:
        click.echo(api_docs)


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


def analyze_codebase(path: str) -> Dict[str, Any]:
    """Helper function for standalone commands."""
    from .commands.analyze import analyze_codebase as _analyze
    return _analyze(path)


def generate_diagram(codebase_info: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Helper function for standalone commands."""
    from .commands.generate import generate_diagram as _generate
    return _generate(codebase_info, analysis)


def generate_api_docs(endpoints: list) -> str:
    """Helper function for standalone commands."""
    from .commands.generate import generate_api_docs as _generate
    return _generate(endpoints)


def generate_setup_instructions(path: str) -> str:
    """Helper function for standalone commands."""
    from .commands.generate import generate_setup_instructions as _generate
    return _generate(path)


if __name__ == "__main__":
    main()
