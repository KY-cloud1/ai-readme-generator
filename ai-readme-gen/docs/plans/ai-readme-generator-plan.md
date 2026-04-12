# AI README Generator - Implementation Plan

**Context:** Building an AI-powered documentation generator from scratch. The requirements document has been created and is ready. This plan outlines the implementation approach for the MVP.

---

## Context

The AI README Generator is a new project with no existing code. It needs to:
1. Analyze codebases (Python, JavaScript/TypeScript)
2. Generate high-quality README.md files
3. Create ASCII architecture diagrams
4. Extract API documentation (if applicable)
5. Provide setup/installation instructions

The project will have two interfaces:
- **CLI tool**: Python-based for direct usage
- **Web GUI**: Next.js + React dashboard

---

## Implementation Approach

### Phase 1: Project Setup & Scaffolding

**Goal**: Create the monorepo structure with both CLI and web applications.

#### 1.1 Python CLI Application
- Create `cli/` directory with Click-based CLI
- Set up project structure:
  ```
  ai-readme-gen/
  ├── cli/
  │   ├── __init__.py
  │   ├── main.py              # Entry point
  │   ├── commands/
  │   │   ├── analyze.py       # Main analysis command
  │   │   ├── generate.py      # Generation options
  │   │   └── config.py        # Configuration handling
  │   ├── analysis/
  │   │   ├── __init__.py
  │   │   ├── codebase.py      # Codebase traversal
  │   │   ├── parser.py        # Language-specific parsing
  │   │   └── extractor.py     # Pattern extraction
  │   └── ai/
  │       ├── __init__.py
  │       ├── client.py        # AI API wrapper
  │       └── prompts.py       # Prompt templates
  ├── web/                      # Next.js web app
  │   ├── src/
  │   ├── package.json
  │   └── ...
  ├── docs/
  │   └── brainstorms/
  │       └── requirements_ai_readme_generator.md
  └── pyproject.toml
  ```

#### 1.2 Next.js Web Application
- Create `web/` directory with Next.js 14+ (App Router)
- Set up basic structure:
  ```
  web/
  ├── src/
  │   ├── app/
  │   │   ├── page.tsx         # Dashboard landing
  │   │   ├── projects/
  │   │   │   └── page.tsx    # Project list
  │   │   ├── new/
  │   │   │   └── page.tsx    # New project wizard
  │   │   └── api/
  │   │       └── analyze/    # API endpoint
  │   ├── components/
  │   │   ├── Dashboard.tsx
  │   │   ├── ProjectCard.tsx
  │   │   └── Settings.tsx
  │   └── lib/
  │       ├── api.ts           # API client
  │       └── utils.ts
  ├── package.json
  └── next.config.js
  ```

### Phase 2: Core CLI Implementation

**Goal**: Build the codebase analysis engine and AI integration.

#### 2.1 Codebase Analysis Engine
- **Directory structure**: `cli/analysis/`
- **Functions to implement**:
  - `scan_codebase(path)` - Traverse directory, identify file types
  - `parse_python(path)` - Parse Python files for classes, functions, imports
  - `parse_javascript(path)` - Parse JS/TS files for modules, exports
  - `extract_dependencies(path)` - Identify project dependencies
  - `infer_architecture(codebase)` - Derive design patterns

#### 2.2 AI Integration Layer
- **Directory structure**: `cli/ai/`
- **Functions to implement**:
  - `create_analysis_prompt(codebase_info)` - Build prompt for analysis
  - `create_readme_prompt(codebase_info)` - Build prompt for README generation
  - `create_diagram_prompt(codebase_info)` - Build prompt for ASCII diagrams
  - `call_ai_model(prompt, model_type)` - Interface with AI APIs

#### 2.3 Agent Simulation
- Implement simulated agent roles:
  - `CodebaseAnalyst` - Analyzes structure and dependencies
  - `Architect` - Infers design patterns
  - `TechnicalWriter` - Writes documentation
  - `APIExtractor` - Identifies endpoints
  - `Reviewer` - Validates output

### Phase 3: Generation Pipeline

**Goal**: Implement the documentation generation workflow.

#### 3.1 README Generation
- Template-based approach with AI fill-in
- Sections:
  - Project description
  - Key features
  - Tech stack
  - Installation instructions
  - Usage examples
  - Architecture overview
  - API documentation (if applicable)

#### 3.2 ASCII Diagram Generation
- Prompt AI to generate ASCII art diagrams
- Support for:
  - Component hierarchy
  - Data flow
  - Module relationships

#### 3.3 API Documentation Extraction
- Parse OpenAPI/Swagger specs if present
- Extract endpoint definitions from code
- Generate structured API documentation

### Phase 4: Web GUI Implementation

**Goal**: Create the Next.js dashboard.

#### 4.1 Dashboard Layout
- Sidebar navigation
- Project list view
- Settings panel

#### 4.2 Project Management
- `POST /api/projects` - Create new project
- `GET /api/projects` - List all projects
- `GET /api/projects/:id` - Get project details
- `POST /api/projects/:id/analyze` - Trigger analysis
- `GET /api/projects/:id/results` - Get analysis results

#### 4.3 Analysis Interface
- Project selection
- Configuration options (AI model, timeout)
- Progress indicator
- Results display with copy/download

### Phase 5: Testing & Validation

**Goal**: Ensure quality and reliability.

#### 5.1 Unit Tests
- Test codebase analyzers
- Test prompt templates
- Test AI client error handling

#### 5.2 Integration Tests
- Test full analysis pipeline
- Test CLI command execution
- Test API endpoints

### Phase 6: Documentation & Polish

**Goal**: Complete the project with documentation and final touches.

---

## Critical Files

| File | Purpose |
|------|---------|
| `cli/main.py` | CLI entry point |
| `cli/analysis/codebase.py` | Codebase traversal logic |
| `cli/analysis/parser.py` | Language-specific parsing |
| `cli/ai/client.py` | AI API integration |
| `web/src/app/page.tsx` | Dashboard landing page |
| `web/src/app/api/analyze/route.ts` | Analysis API endpoint |
| `pyproject.toml` | Python project configuration |
| `web/package.json` | Web app dependencies |

---

## Verification Plan

1. **Setup verification**:
   - `pip install -e .` succeeds
   - `npm install` in web/ succeeds

2. **CLI verification**:
   - `ai-readme-gen --help` shows help
   - `ai-readme-gen analyze --path /path/to/repo` runs analysis

3. **Web verification**:
   - `npm run dev` starts dev server
   - Dashboard loads and shows project list

4. **End-to-end test**:
   - Create sample project in temp directory
   - Run CLI analysis
   - Verify generated README.md contains expected sections
   - Verify ASCII diagram is valid and readable

---

## Timeline Estimate

| Phase | Duration |
|-------|----------|
| Phase 1: Setup | 2-3 hours |
| Phase 2: Core CLI | 4-6 hours |
| Phase 3: Generation | 3-4 hours |
| Phase 4: Web GUI | 4-5 hours |
| Phase 5: Testing | 2-3 hours |
| Phase 6: Documentation | 1-2 hours |
| **Total** | **16-23 hours** (~2 days) |

---

## Success Criteria

- [ ] CLI tool generates README from sample Python project
- [ ] CLI tool generates ASCII architecture diagram
- [ ] Web dashboard lists projects and triggers analysis
- [ ] Generated documentation resembles senior engineer quality
- [ ] No hallucinated code or files in output
