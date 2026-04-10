# AI README Generator

AI-powered documentation generator that creates high-quality README files, architecture diagrams, and API documentation from codebases.

## Features

- **CLI Tool**: Command-line interface for analyzing codebases
- **Web Dashboard**: Manage projects through a web interface
- **Multi-language Support**: Python and JavaScript/TypeScript
- **ASCII Diagrams**: Architecture diagrams in ASCII art
- **API Documentation**: Extract and document API endpoints
- **Setup Instructions**: Generate installation and configuration guides

## Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- API key (Anthropic or OpenAI)

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/example/ai-readme-gen
cd ai-readme-gen
```

2. **Install Python dependencies**

```bash
pip install -e ".[dev,web]"
```

3. **Install web dependencies**

```bash
cd web
npm install
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

### Web Dashboard

```bash
# Start backend (Python)
ai-readme-gen --config

# Start web server
cd web
npm run dev
```

Visit `http://localhost:3000` to access the dashboard.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | AI provider (anthropic, openai, local) | anthropic |
| `AI_MODEL` | Model to use | claude-3-5-sonnet-20240620 |
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

### Web

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

## Architecture

```
ai-readme-gen/
├── cli/                    # Python CLI application
│   ├── analysis/          # Codebase analysis
│   ├── ai/                # AI integration
│   └── commands/          # CLI commands
├── web/                   # Next.js web application
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   └── public/
└── docs/                  # Documentation
```

## License

MIT License

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## Roadmap

- [ ] Support more languages (Go, Rust, Java)
- [ ] Interactive documentation editor
- [ ] Real-time updates as code changes
- [ ] Export to multiple formats (Markdown, HTML, PDF)
- [ ] GitHub integration
