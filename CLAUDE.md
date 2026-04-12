# Compound Engineering Workflow Rules

This repository uses a structured AI-driven engineering workflow powered by 
`/ce:*` commands.

The system operates in stages:
ideate → brainstorm → plan → work → review → compound

Each stage has strict behavioral constraints.

---

# Workspace Rules

- Root project directory:
  /workspaces/compound-engineering-testing

- All files MUST be created, modified, and read only within this directory.

- Never write to:
  - /home/vscode
  - plugin cache directories
  - system paths outside the workspace

---

# Stage Definitions

## /ce:ideate
Exploratory phase only:
- divergent thinking
- feature discovery
- no structured implementation

No file writing unless explicitly required for notes.

---

## /ce:brainstorm
Requirement generation phase:
- convert idea into structured requirements
- define system components
- outline file structure at high level

Allowed:
- pseudocode
- architecture sketches
- requirement documents

NOT allowed:
- full implementation code
- production-ready modules

---

## /ce:plan
Architecture + execution design phase:

- convert requirements into actionable engineering plan
- define modules, interfaces, and data flow
- break work into tasks suitable for `/ce:work`

Allowed outputs:
- file tree design
- step-by-step implementation plan
- task breakdown

NOT allowed:
- full feature implementation

---

## /ce:work
Implementation phase (STRICT EXECUTION MODE)

### Worktree Policy
- MUST use git worktrees for isolation
- Each feature runs in its own branch + directory
- Never modify main branch directly

### Execution rules
For each task:
1. Implement only the current task scope
2. Verify correctness
3. Stage only relevant files
4. Commit before moving to next task

### Git Commit Policy

Commits represent decisions, not progress.

#### When to commit:
- After completing each task in `/ce:plan`
- After finishing a stable feature unit
- After applying `/ce:review` fixes

#### Commit rules:
- Do NOT commit incomplete or broken states
- Do NOT commit experimental or partial work
- Do NOT mix unrelated changes in one commit
- Do NOT user uppercase letters to start the commit message or the commit 
  body message

#### Commit message format:
Use conventional commits:

- feat: new feature implementation
- fix: bug fix
- refactor: internal restructuring
- docs: documentation updates
- chore: tooling or setup changes

---

## /ce:review
Quality assurance phase:
- review implementation against plan
- detect bugs, inconsistencies, or missing parts
- propose fixes (not full rewrites unless necessary)

---

## /ce:compound
Learning + optimization phase:
- summarize what was learned
- improve future workflows
- refine architecture patterns
- optionally update CLAUDE.md rules

---

# Core Engineering Principles

- Planning before coding is mandatory
- Each stage must complete before the next begins
- Work must be traceable via git history
- Commits must represent meaningful milestones
- Prefer clarity over speed
- Prefer isolation (worktrees) over shared mutable state

---

# Git & Worktree Strategy

- Main branch = stable production state
- Each `/ce:work` session = isolated git worktree
- Each feature = separate branch
- No direct commits to main branch during active work

---

# Hard Constraints

Claude must NEVER:
- write code outside `/workspaces/compound-engineering-testing`
- skip `/ce:plan` before `/ce:work`
- commit incomplete or broken features
- bypass worktree isolation rules
- mix multiple tasks in a single commit

---

# Documented Solutions

`ai-readme-gen/docs/solutions/` — documented solutions to past problems (bugs, 
best practices, workflow patterns), organized by category with YAML frontmatter 
(module, tags, problem_type). Relevant when implementing or debugging in 
documented areas.

---

# System Goal

This repository is structured as a compound engineering system:

- predictable AI behavior
- clean separation of concerns
- reproducible workflows
- traceable git history
- safe incremental execution