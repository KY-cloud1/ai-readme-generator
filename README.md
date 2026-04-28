# Notes about Development
This project was created using Claude Code with the Compound Engineering plugin by Every and powered locally via Qwen3.5-9b-4bit (hosted with llama.cpp using llama-server and a GGUF from unSloth).

The development highlights structured LLM development practices that focus on proper coding standards, file organization, and conventional commit practices. It also utilized Tailscale, tmux, and Termius to allow on-the-go interaction while Claude Code was running with the local LLM.

The LLM was run on a 2022 16-inch MacBook Pro (M2 Pro, 32GB RAM, 1TB storage). The MacBook was consistently running at 100% GPU utilization, with constant ~27GB of RAM in use and several gigabytes of SSD swap active. This highlights that more powerful hardware is required for serious local LLM development on anything more than very small context and repository sizes.

Reasoning time was not an issue after Qwen3.5-9B was adjusted using Unsloth’s recommended sampling parameters for coding tasks. Average token generation speed for small prompts was approximately ~23 tokens/sec (slow, but usable). However, Metal backend consistenty failed as the context length approached ~100,000 tokens for a single prompt, requiring for llama-server to be restart and for the current Claude Code prompt to be cleared.

It's likely that any cloud-hosted frontier LLM model could have completed this project in a fraction of the time, effort, and prompting spent on this one. However, I hope this project will serve as a useful reference to me showing how far local LLMs will grow and  how far I'll be able to push my current hardware within the comming years. As of Spring 2026, I can confidently say that using Qwen3.5-9b-4bit for this project pushed my Macbook to its limit. I hope that even 2-3 years from now I can look back with far better local LLM models and hardware and reminisce to when I was only getting started. 

# AI README Generator

AI-powered documentation generator that creates high-quality README files, architecture diagrams, and API documentation from codebases.

## Features

- **CLI Tool**: Command-line interface for analyzing codebases
- **Multi-language Support**: Python and JavaScript/TypeScript
- **ASCII Diagrams**: Architecture diagrams in ASCII art
- **API Documentation**: Extract and document API endpoints
- **Setup Instructions**: Generate installation and configuration guides

## Installation

### Prerequisites

- Python 3.9+
- API key (Anthropic or OpenAI)

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/example/ai-readme-gen
cd ai-readme-gen
```

2. **Create and activate a Python virtual environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install Python dependencies**

```bash
pip install -e ".[dev,web]"
```

4. **Set up API keys**

```bash
# For Anthropic
export ANTHROPIC_API_KEY=your_api_key

# For OpenAI
export OPENAI_API_KEY=your_api_key
```

## Usage

### CLI

```bash
# Analyze a codebase
ai-readme-gen analyze /path/to/project

# Save output to file
ai-readme-gen analyze /path/to/project -o readme.md

# Show verbose output
ai-readme-gen analyze /path/to/project -v

# Generate diagram only
ai-readme-gen diagram /path/to/project -o diagram.txt

# Extract API docs
ai-readme-gen api /path/to/project -o api.md

# Generate setup instructions
ai-readme-gen setup /path/to/project -o setup.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | AI provider (anthropic, openai, local) | - |
| `AI_MODEL` | Model to use | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OUTPUT_FORMAT` | Output format (text, json) | text |
| `TIMEOUT` | Request timeout in seconds | 300 |

### Output Formats

- **Text**: Human-readable documentation (default)
- **JSON**: Structured data for programmatic use

## Development

### Python

```bash
# Run tests
pytest

# Format code
black .

# Type check
mypy cli
```

## Architecture

```
ai-readme-gen/
├── cli/                          # Python CLI application
│   ├── __init__.py
│   ├── main.py                   # CLI entry point
│   ├── analysis/                 # Codebase analysis logic
│   │   ├── __init__.py
│   │   ├── agent.py              # AI agent for analysis
│   │   ├── codebase.py           # Codebase traversal and analysis
│   │   ├── extractor.py          # Content extraction utilities
│   │   └── parser.py             # Document parsing logic
│   ├── ai/                       # AI client integration
│   │   ├── __init__.py
│   │   ├── client.py             # AI API client
│   │   └── prompts.py            # Prompt templates
│   └── commands/                 # CLI command implementations
│       ├── __init__.py
│       ├── analyze.py            # Analyze command
│       ├── config.py             # Config command
│       └── generate.py           # Generate command
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_codebase_analysis.py              # Extended codebase analysis tests
│   ├── test_codebase_analysis_extended.py     # Additional analysis tests
│   ├── test_analysis_pipeline_integration.py  # Pipeline integration tests
│   ├── test_api_endpoints.py     # API endpoint tests
│   ├── test_agents.py            # Agent tests
│   └── test_error_logging.py     # Error logging tests
├── docs/                         # Documentation
│   ├── brainstorms/              # Brainstorming session notes
│   │   └── requirements_ai_readme_generator.md
│   ├── plans/                    # Implementation plans
│   │   └── ai-readme-generator-cli-plan.md
│   └── solutions/                # Documented solutions
│       ├── python/               # Python-specific solutions
│       └── development-workflow/ # Development workflow solutions
└── pyproject.toml                # Python project configuration
```
