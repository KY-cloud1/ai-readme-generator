---
title: Fix function signature mismatch in generate_api_docs and agent_context handling
type: bug
problem_type: function_signature_mismatch
status: resolved
date: 2026-04-13
last_updated: 2026-04-13
module: ai-readme-gen/cli/commands,ai-readme-gen/cli/main
files:
  - ai-readme-gen/cli/commands/analyze.py
  - ai-readme-gen/cli/commands/generate.py
  - ai-readme-gen/cli/main.py
tags:
  - function-signature
  - parameter-mismatch
  - agent-context
  - codebase-info
  - python
  - cli
category: python
---

# Problem

Function parameter mismatches between CLI invocations and function definitions in `generate.py` caused:
- Architecture diagrams to lack actual codebase file counts and entry point annotations
- API documentation to show only basic placeholders without endpoint descriptions, parameters, or response schemas

Additionally, `agent_context` (a dictionary of `AgentResult` objects) was not being properly passed through the call chain, preventing extraction of entry points and metadata from agent results.

## Symptoms

```python
# In main.py - incorrect function calls
diagram = generate_diagram(analysis['codebase'], analysis.get('agents', {}).get('Architect') or analysis)
api_docs = generate_api_docs(analysis.get('endpoints', []))

# Expected signatures (but functions defined differently)
def generate_diagram(codebase_info, analysis, agent_context)
def generate_api_docs(endpoints)  # missing codebase_info and agent_context
```

**Observable issues:**
- Diagrams showed hardcoded templates instead of actual file counts
- No entry points displayed in diagrams (should show ⚡ markers from CodebaseAnalyst)
- API docs lacked endpoint descriptions, parameters, and response schemas
- `generate_basic_api_docs` received only `endpoints` instead of `codebase_info` for fallback generation

## What Didn't Work

### Initial Investigation Assumption

The initial assumption was that the issue was with `agent_context` not being populated. However, tracing through the code revealed the root cause was actually **parameter name mismatches** and **missing parameters** in function signatures.

### Incorrect Fix Attempt 1

**What was attempted:** Only add `agent_context` parameter to functions without updating call sites.

**Why it failed:** The CLI in `main.py` was calling functions with incorrect parameter names (`analysis` instead of `codebase_info`, `agents` instead of `agent_context`). Adding parameters to functions doesn't fix the caller-side issues.

### Incorrect Fix Attempt 2

**What was attempted:** Pass `analysis` dict directly as `agent_context`.

**Why it failed:** The `analysis` dict has structure `{'codebase': {...}, 'endpoints': [...], 'agents': {...}}`, while `agent_context` should be `{agent_name: AgentResult}`. Passing the wrong structure meant no metadata could be extracted.

## Solution

### Fix 1: Update `generate.py` function signatures

**File:** `ai-readme-gen/cli/commands/generate.py`

**Before:**
```python
def generate_diagram(codebase_info: Dict[str, Any], analysis: Optional[Dict[str, Any]] = None) -> str:
def generate_basic_diagram(codebase_info: Dict[str, Any]) -> str:
def generate_api_docs(endpoints: list) -> str:
def generate_basic_api_docs(endpoints: list) -> str:
```

**After:**
```python
def generate_diagram(
    codebase_info: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:

def generate_basic_diagram(
    codebase_info: Dict[str, Any],
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:

def generate_api_docs(
    codebase_info: Dict[str, Any],
    endpoints: Optional[list] = None,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:

def generate_basic_api_docs(
    endpoints: list,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:
```

**Change:** Added `agent_context` parameter and made `codebase_info` the first parameter for `generate_api_docs`.

### Fix 2: Update `generate_basic_diagram` to extract entry points from AgentResult

**File:** `ai-readme-gen/cli/commands/generate.py`

**Before:**
```python
# agent_context is Dict[str, AgentResult], extract metadata from CodebaseAnalyst result
if agent_context:
    # Look for entry_points in any AgentResult's metadata
    entry_points = []
    for result in agent_context.values():
        if result.success and result.metadata:
            entry_points = result.metadata.get("entry_points", [])
            break
    if entry_points:
        lines.append("")
        lines.append("    Entry Points:")
        for ep in entry_points[:5]:
            lines.append(f"    ├── [⚡ {ep}]")
```

**Change:** Extract entry points from `AgentResult.metadata` in the `agent_context` dictionary.

### Fix 3: Update `generate_basic_api_docs` to use codebase_info for fallback

**File:** `ai-readme-gen/cli/commands/generate.py`

**Before:**
```python
def generate_basic_api_docs(endpoints: list, agent_context: Optional[Dict[str, AgentResult]] = None) -> str:
    # ... endpoint documentation
```

**After:**
```python
def generate_basic_api_docs(
    endpoints: list,
    agent_context: Optional[Dict[str, AgentResult]] = None
) -> str:
    # agent_context is Dict[str, AgentResult], extract metadata from APIExtractor result
    if agent_context:
        metadata = {}
        for result in agent_context.values():
            if result.success and result.metadata:
                metadata = result.metadata
                break
        if metadata:
            lines.append("")
            lines.append("### Summary")
            # ... use metadata
```

**Change:** Extract metadata from `AgentResult` objects in `agent_context` to enhance fallback API docs.

### Fix 4: Update `generate_api_docs` to include full endpoint details

**File:** `ai-readme-gen/cli/commands/generate.py`

**Before:**
```python
for ep in endpoints[:10]:
    lines.append(f"#### {ep.get('method', 'GET').upper()} {ep.get('path', '')}")
    lines.append("- **Source**: {ep.get('source', 'Unknown')}")
```

**After:**
```python
for ep in endpoints[:10]:
    lines.append(f"#### {ep.get('method', 'GET').upper()} {ep.get('path', '')}")
    lines.append("")
    lines.append(f"- **Source**: {ep.get('source', 'Unknown')}")
    lines.append(f"- **Description**: {ep.get('description', 'No description')}")
    lines.append(f"- **Params**: {ep.get('params', [])}")
    lines.append(f"- **Response**: {ep.get('response', 'No response schema')}")
    lines.append("")
```

**Change:** Include description, parameters, and response schema from endpoint definitions.

### Fix 5: Update `analyze.py` to pass codebase_info to generate_api_docs

**File:** `ai-readme-gen/cli/commands/analyze.py`

**Before:**
```python
api_docs = generate_api_docs(analysis['endpoints'], analysis.get('agents') if use_agents else None)
```

**After:**
```python
api_docs = generate_api_docs(analysis['codebase'], analysis['endpoints'], analysis.get('agents') if use_agents else None)
```

**Change:** Pass `codebase_info` as first parameter and full `agents` dict as `agent_context`.

### Fix 6: Update `main.py` CLI function invocations

**File:** `ai-readme-gen/cli/main.py`

**Before:**
```python
diagram = generate_diagram(analysis['codebase'], analysis.get('agents', {}).get('Architect') or analysis)
api_docs = generate_api_docs(analysis.get('endpoints', []))
```

**After:**
```python
diagram = generate_diagram(analysis['codebase'], analysis.get('agents', {}).get('Architect'), analysis.get('agents'))
api_docs = generate_api_docs(analysis.get('codebase', {}), analysis.get('endpoints', []), analysis.get('agents'))
```

**Change:** Pass `codebase_info` as first parameter and `agent_context` (full agents dict) as third parameter.

## Why This Works

1. **Explicit context flow**: The `agent_context` parameter now carries the full agent results dictionary through the call chain, preserving `CodebaseAnalyst`, `APIExtractor`, and other agent metadata.

2. **Correct parameter order**: `generate_api_docs` now receives `codebase_info` as the first parameter (matching the actual data structure), not just endpoints.

3. **Entry point extraction**: The fallback diagram generation now extracts entry points from `AgentResult.metadata` instead of showing hardcoded templates.

4. **Enriched API docs**: API documentation now displays description, parameters, and response schema extracted from endpoint definitions.

5. **Proper fallback behavior**: When AI is unavailable, basic diagrams and API docs use actual codebase data (file counts, entry points) instead of hardcoded templates.

## Prevention

1. **Always verify function signatures**: Before modifying function calls, verify the target function's signature matches the caller's expectations.

2. **Use type hints consistently**: Type hints for function parameters help catch mismatches at static analysis time:
   ```python
   def generate_api_docs(
       codebase_info: Dict[str, Any],
       endpoints: Optional[list] = None,
       agent_context: Optional[Dict[str, AgentResult]] = None
   ) -> str:
   ```

3. **Parameter naming discipline**: Use descriptive, consistent parameter names:
   - `codebase_info` (not `analysis` or `data`)
   - `agent_context` (not `agents` or `context`)

4. **Integration tests with mocked AI**: Create tests that mock `call_ai_model` and verify fallback generators receive correct arguments:
   ```python
   @patch('cli.commands.generate.call_ai_model')
   def test_fallback_diagram(mock_call):
       mock_call.side_effect = AuthenticationError("API unavailable")
       result = generate_diagram(codebase_info, agent_context)
       assert "Entry Points:" in result
       assert "⚡" in result
   ```

5. **Code review checklist**: Include "parameter signature verification" in code review tasks for CLI modifications.

6. **Function contract documentation**: Add explicit docstring parameter lists with examples showing expected types.

## Related Documentation

- [Fix undefined json, list, and Optional import errors](./undefined-import-errors-2026-04-11.md) - Related import error fixes in the same codebase
- [Fix Codebase Review Findings Plan](../../ai-readme-gen/docs/plans/2026-04-11-001-fix-codebase-review-findings-plan.md) - Broader context for all import and error handling fixes in the codebase
- [code-review-verified-fixes-2026-04-12.md](./code-review-verified-fixes-2026-04-12.md) - Comprehensive fixes from code review including similar import issues
- [missing-agentresult-import-2026-04-11.md](./missing-agentresult-import-2026-04-11.md) - Related import error fixes for AgentResult

## Session History

This fix was identified during integration testing of the diagram generation pipeline. The CLI was calling functions with incorrect argument names and passing the `analysis` dict directly instead of `agent_context`. The fix involved updating all function signatures in `generate.py` to accept `agent_context` and updating the CLI invocations in `main.py` to pass the correct parameters.

The parameter signature mismatch was discovered when:
- Architecture diagrams lacked actual codebase file counts and entry point annotations
- API documentation showed only basic placeholders without endpoint descriptions, parameters, or response schemas

The fix followed the compound engineering principles:
- Atomic commits representing single decisions
- Isolated work using git worktrees
- Documentation in `docs/solutions/` for future reference

---

*Updated 2026-04-13 using /ce:compound*
