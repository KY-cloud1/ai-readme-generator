# AI README Generator - Requirements Document

**Date**: 2026-04-10
**Status**: Draft

---

## Overview

An AI-powered documentation generator that creates high-quality README files, architecture diagrams, and API documentation from either:
1. A local code repository folder
2. A high-level project description

---

## Goals

### Primary Goals
- Generate high-quality README.md files
- Create text-based architecture diagrams
- Produce setup and installation instructions
- Extract and document APIs (if applicable)
- Explain core modules and their relationships

### User Experience Goals
- Behave like a senior engineer writing documentation
- No hallucination of non-existent files/code
- Clear, consistent, and concise output
- Think like a senior engineer writing documentation for onboarding

---

## Core Workflow

### Analysis Pipeline
1. **Analyze Input** - Process codebase or description
2. **Infer Architecture** - Derive system design patterns
3. **Extract Components** - Identify key modules and dependencies
4. **Generate Artifacts** - Create documentation outputs

### Agent Roles (Simulated)
See [`AgentPipeline`](../cli/analysis/agent.py#L741) for implementation details and [`run_agent_pipeline`](../cli/analysis/agent.py#L836) for execution flow.

| Role | Responsibility |
|------|---------------|
| Codebase Analyst | Understands structure and dependencies. See [`CodebaseAnalyst`](../cli/analysis/agent.py#L53) for implementation. |
| Architect | Infers system design patterns. See [`Architect`](../cli/analysis/agent.py#L207) for implementation. |
| Technical Writer | Writes README and documentation. See [`TechnicalWriter`](../cli/analysis/agent.py#L268) for implementation. |
| API Extractor | Identifies endpoints/interfaces. See [`APIExtractor`](../cli/analysis/agent.py#L378) for implementation. |
| Reviewer | Validates correctness and clarity. See [`Reviewer`](../cli/analysis/agent.py#L486) for implementation. |

**Implementation Patterns**: 
- All agents follow the [Agent](../cli/analysis/agent.py#L48) ABC pattern with `run()` method returning [`AgentResult`](../cli/analysis/agent.py#L29)
- State propagation uses [_propagate_to_context](../cli/analysis/agent.py#L902) methods for inter-agent communication
- Full pipeline execution via [run_agent_pipeline](../cli/analysis/agent.py#L836) with deep-copy isolation

---

## Output Standards

### README.md Requirements
- What the project does
- Key features
- Tech stack
- How to run it

### Architecture Diagram Requirements
- Text-based (Mermaid.js or ASCII)
- Hierarchical and clear
- Reflects real module boundaries

### API Documentation Requirements
- Only generated if backend exists
- Structured by endpoint

### Setup Instructions
- Installation steps
- Configuration options
- Environment variables (if any)

---

## Technical Requirements

### Invocation
- CLI command interface (Python + click/typer)
- Web GUI interface (Next.js + React)
- Single binary or service for both

### Codebase Analysis
- **Hybrid approach**: Read/Glob tools + Explore agent
- **Full analysis**: Read and understand code logic
- File-based parsing for structure understanding
- Agent-based exploration for context

### Language Support (v1)
- Multi-language detection and handling
- Focus on Python, JavaScript/TypeScript

### Diagram Format
- ASCII art as primary format
- Simple, no dependencies, works everywhere

### Non-Goals (v1)
- Interactive editing of generated docs
- Real-time updates as code changes
- Complex diagram types (flowcharts, sequence diagrams)

---

## Success Criteria

### Functional
- [ ] Can analyze a code repository and generate README
- [ ] Can generate architecture diagrams
- [ ] Can extract API endpoints when applicable
- [ ] Can produce setup instructions

### Quality
- [ ] Output resembles senior engineer documentation
- [ ] No hallucinated files or code
- [ ] Clear and consistent formatting
- [ ] Concise but complete explanations

---

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI Framework | Python (click/typer) | Great for AI/ML tooling, easy prototyping |
| Web GUI | Next.js + React | Modern, great for AI apps |
| Web GUI Approach | Standalone web app | Separate Next.js app that calls CLI as backend |
| Analysis Depth | Full analysis | Read and understand code logic |
| Target Users | Developers | Technical users documenting projects |
| Success Metric | User satisfaction | Quality over speed |
| Diagram Format | ASCII art | Simple, no dependencies |
| Language Support | Multi-language | Python, JS/TS for v1 |
| Test Project | Create sample repo | Have a test codebase to experiment with |
| Timeline | Quick prototype (1-2 days) | MVP with core features only |

## Remaining Questions

1. **Deployment Strategy**: How to deploy CLI + web GUI together?
2. **Analysis Timeout**: What's the max repo size for processing?
3. **Customization**: Can users override generated sections?

## Decisions Made (Final)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Analysis Method | Hybrid | AI extracts patterns, rules ensure accuracy |
| Diagram Generation | AI-generated | AI creates diagrams from scratch |
| AI Backend | Support both APIs + local models | Support Anthropic, OpenAI, and local-compatible APIs |
| Error Handling | User-configurable | Let users choose strictness level |
| Output Format | Raw text output | Print to stdout for easy copying |
| Authentication | API keys in config | Store keys in environment/config |
| Web UI | Dashboard | Project list, history, settings |
| Project Structure | Monorepo | Single repo with CLI + web apps |
| Documentation Priority | Balanced | Equal focus on both code and docs |
| MVP Features | Full | CLI + Web + diagrams + API docs |
| Configuration | Environment only | Keep it simple, env vars only |
| Testing | Unit tests | Test individual components |

---

## Brainstorm Summary

**Goal**: Build an AI-powered README generator that analyzes codebases and generates comprehensive documentation.

**Key Features**:
- CLI tool (Python + click/typer)
- Web GUI (Next.js + React with dashboard)
- Multi-language support (Python, JS/TS)
- ASCII architecture diagrams
- API documentation extraction
- Setup instructions generation

**Analysis Approach**:
- Hybrid: code analysis + AI for writing
- Full analysis depth (read and understand code)
- Support Anthropic, OpenAI, and local-compatible APIs

**Success Criteria**:
- User satisfaction (quality over speed)
- No hallucination of non-existent code
- Senior engineer quality documentation

---

## Next Steps

1. Create sample test project
2. Design implementation approach with `/ce:plan`
3. Build MVP with full feature set

## Solution Patterns and References

The implementation follows these established patterns:

### Agent Architecture Patterns

1. **Agent-First Architecture**: Each agent implements the [Agent](../cli/analysis/agent.py#L48) ABC with `run()` returning [AgentResult](../cli/analysis/agent.py#L29)
   - Pattern ensures consistent interface across all agents
   - [AgentResult](../cli/analysis/agent.py#L29) dataclass provides structured success/error reporting
   - See [CodebaseAnalyst](../cli/analysis/agent.py#L53) for base implementation example

2. **State Isolation via Deep Copy**: `run_agent_pipeline` uses `copy.deepcopy()` to prevent unsafe shared dict mutation
   - Each agent receives an isolated context view
   - Prevents cross-agent state contamination
   - See [run_agent_pipeline](../cli/analysis/agent.py#L732) for full implementation

3. **Sequential State Dependency**: Agents run sequentially with results passed via context propagation
   - Each agent's `_propagate_to_context()` method updates context for dependent agents
   - Context accumulation is safe due to deep-copy isolation
   - See [CodebaseAnalyst._propagate_to_context](../cli/analysis/agent.py#L85) for example

### Error Handling Patterns

4. **Graceful Degradation**: Each agent catches exceptions and returns [AgentResult](../cli/analysis/agent.py#L29) with `success=False`
   - Prevents pipeline failure from single agent error
   - Allows downstream agents to handle specific error cases
   - See [run_agent_pipeline](../cli/analysis/agent.py#L732) for error handling flow

5. **Validation Pipeline**: Reviewer validates completeness and accuracy against codebase
   - [Reviewer._check_completeness](../cli/analysis/agent.py#L478) checks for missing documentation sections
   - [Reviewer._check_accuracy](../cli/analysis/agent.py#L509) validates against actual codebase
   - [Reviewer._validate_against_codebase](../cli/analysis/agent.py#L574) adds additional validation layer

### Codebase Analysis Patterns

6. **Hybrid Analysis Approach**: Combines file scanning with AI-powered extraction
   - [scan_codebase](../cli/analysis/codebase.py) uses Glob for file discovery
   - [CodebaseAnalyst._extract_python_imports](../cli/analysis/agent.py#L142) parses actual import statements
   - [CodebaseAnalyst._extract_js_imports](../cli/analysis/agent.py#L170) handles JavaScript/TypeScript imports

7. **Dependency Detection**: Agents infer dependencies from actual file imports
   - Avoids hallucinated dependencies
   - See [CodebaseAnalyst._find_dependencies](../cli/analysis/agent.py#L115) for implementation

### Documentation Generation Patterns

8. **AI-Assisted Content Generation**: AI models generate documentation content
   - [call_ai_model](../cli/ai/client.py) handles provider-specific API calls
   - [extract_json_response](../cli/ai/client.py) parses AI responses safely
   - Fallback to [generate_basic_readme](../cli/commands/generate.py#L55) when AI unavailable

9. **ASCII Diagram Generation**: Text-based architecture diagrams
   - [generate_diagram](../cli/commands/generate.py#L98) creates ASCII art from codebase structure
   - `nlwrap` ensures proper terminal escaping for special characters
   - See [main.py:diagram command](../cli/main.py#L84) for CLI integration

10. **API Documentation Extraction**: Automatically extracts API endpoints
    - [extract_api_endpoints](../cli/analysis/extractor.py) scans code for endpoint definitions
    - [APIExtractor](../cli/analysis/agent.py#L336) groups endpoints by HTTP method
    - [generate_api_docs](../cli/commands/generate.py#L166) formats for documentation

**Key Implementation Files**:
- [agent.py](../cli/analysis/agent.py) - Agent implementations and pipeline (lines 1-871)
- [codebase.py](../cli/analysis/codebase.py) - Codebase scanning and analysis
- [extractor.py](../cli/analysis/extractor.py) - Metadata and endpoint extraction
- [prompts.py](../cli/ai/prompts.py) - AI prompt templates
- [client.py](../cli/ai/client.py) - AI API client and response parsing
- [generate.py](../cli/commands/generate.py) - Documentation generation functions
- [main.py](../cli/main.py) - CLI entry point with commands

**Related Solution Patterns in Codebase**:
- [main.py:121](../cli/main.py#L121) - Analyze command output escaping with `nlwrap` for ASCII safety
- [agent.py:451](../cli/analysis/agent.py#L451) - APIExtractor._propagate_to_context with validation
- [agent.py:711](../cli/analysis/agent.py#L711) - Reviewer._propagate_to_context with validation
- [agent.py:836](../cli/analysis/agent.py#L836) - run_agent_pipeline with deep-copy isolation
