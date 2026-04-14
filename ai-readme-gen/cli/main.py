#!/usr/bin/env python3
"""AI README Generator CLI - Entry point."""

import os
from typing import Any, Optional

import click
from .commands.analyze import analyze_and_generate, analyze_codebase
from .commands.config import validate_config
from .commands.generate import generate_diagram, generate_api_docs, generate_setup_instructions


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
    if verbose:
        click.echo(f"Analyzing: {path}")
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
        # Output directly without nlwrap (functionality moved to analyze.py)
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
        # Generate diagram with proper agent context
        architect_result = analysis.get('agents', {}).get('Architect')
        diagram = generate_diagram(
            analysis['codebase'],
            architect_result,
            analysis.get('agents')
        )
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
        click.echo(diagram, nl=False)

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
        # Generate API docs with proper agent context
        api_docs = generate_api_docs(
            analysis.get('codebase', {}),
            analysis.get('endpoints', []),
            analysis.get('agents')
        )
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
        click.echo(api_docs, nl=False)

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


if __name__ == "__main__":
    main()
