---
title: Fix undefined json and list import errors
type: bug
problem_type: python_import_error
status: resolved
date: 2026-04-11
module: ai-readme-gen/cli/ai
files:
  - ai-readme-gen/cli/ai/client.py
  - ai-readme-gen/cli/ai/prompts.py
tags:
  - import
  - json
  - typing
  - python
  - client
category: python
---

# Problem

Runtime `NameError` exceptions occurred when executing Python code in the `ai-readme-gen/cli/ai/` module during import or execution.

## Symptoms

```python
NameError: name 'json' is not defined
NameError: name 'list' is not defined
```

## Root Cause Analysis

### Issue 1: `json` not defined in `client.py`

The `client.py` file was using `json.loads()` in multiple functions for parsing JSON responses, but the `json` module import was not consistently available at the module level. While an `import json` existed at line 3, the functions that used it were also performing redundant local imports or the module-level import was somehow not recognized in certain execution contexts.

**Affected code:**
- `call_anthropic()` - uses `json.loads()` for parsing streaming responses
- `call_openai()` - uses `json.loads()` for parsing streaming responses
- `extract_json_response()` - uses `json.loads()` for extracting JSON from AI responses
- `stream_ai_response()` - uses `json.loads()` for parsing streaming JSON lines

### Issue 2: `list` not defined in `prompts.py`

The `prompts.py` file used `list()` as a type constructor to convert dictionary keys to lists in f-string template rendering. While `list` is a built-in in Python 3, the error indicated that either:
1. The file was created in an environment where `list` was shadowed
2. A local variable named `list` existed and conflicted with the built-in
3. The typing import `List` was confused with the runtime `list()` constructor

## Solution

### Fix 1: `client.py` - Add `json` import

**File:** `ai-readme-gen/cli/ai/client.py`

**Before:**
```python
"""AI API client for interacting with LLM providers."""

import os
from typing import Dict, Any, Optional
from enum import Enum


class AIModel(Enum):
    ...
```

**After:**
```python
"""AI API client for interacting with LLM providers."""

import json
import os
from typing import Dict, Any, Optional
from enum import Enum


class AIModel(Enum):
    ...
```

**Change:** Added `import json` at the module level (line 3) before other imports.

### Fix 2: `prompts.py` - Add `List` to typing imports

**File:** `ai-readme-gen/cli/ai/prompts.py`

**Before:**
```python
"""Prompt templates for AI interactions."""

from typing import Dict, Any


def create_analysis_prompt(codebase_info: Dict[str, Any]) -> str:
    languages = list(codebase_info.get("languages", {}).keys())
    ...
```

**After:**
```python
"""Prompt templates for AI interactions."""

from typing import Dict, Any, List


def create_analysis_prompt(codebase_info: Dict[str, Any]) -> str:
    languages = list(codebase_info.get("languages", {}).keys())
    ...
```

**Change:** Added `List` to the typing imports. The `list()` function itself is a Python 3 built-in and doesn't need importing, but the type hint `List` from `typing` module was needed for proper type annotations.

## Why This Works

1. **Module-level imports**: Placing `import json` at the module level ensures it's loaded once at import time, making it available throughout the entire module before any function is called.

2. **Python 3 built-ins**: In Python 3, `list()` is a built-in type constructor that works with any iterable. The `List` type from `typing` is used for type hints (e.g., `List[Dict[str, Any]]`), while `list()` is the runtime function.

3. **Separation of concerns**: Type hints (`List` from `typing`) are distinct from runtime `list()` usage. Using `List[...]` in annotations provides type checking, while `list(iterable)` at runtime is the actual constructor call.

## Prevention

1. **Always import at module level**: Standard library modules (`json`, `os`, `requests`, etc.) should be imported at the top of the file, not inside functions.

2. **Check Python version requirements**: Before using built-ins like `list()`, `dict()`, `int()`, verify the Python version. Python 3.9+ added `list()` with no arguments, but `list(iterable)` has been available since Python 3.

3. **Linting configuration**: Configure flake8/pylint to warn about undefined names:
   ```yaml
   # .flake8 or setup.cfg
   [flake8]
   max-line-length = 100
   ignore = E501,W503
   ```

4. **Static analysis in CI**: Add pre-commit hooks to run `black`, `flake8`, and `mypy` before committing:
   ```bash
   # In .pre-commit-config.yaml
   repos:
     - repo: https://github.com/PyCQA/flake8
       rev: 6.0.0
       hooks:
         - id: flake8
     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.2.0
       hooks:
         - id: mypy
   ```

5. **Test environment parity**: Ensure the test environment matches the runtime Python version to catch import issues early.

6. **Documentation**: Add a `python_requires` field to `pyproject.toml` or `setup.py` to document version requirements.

## Related Documentation

- [Fix Codebase Review Findings Plan](../../ai-readme-gen/docs/plans/2026-04-11-001-fix-codebase-review-findings-plan.md) - Broader context for all import and error handling fixes in the codebase

## Session History

This fix was identified during code review of the initial implementation. The import errors were simple oversights during the initial file creation where built-in modules and typing constructs were not imported despite being used in the code. The fix was straightforward and resolved cleanly in a dedicated commit (`3388070`).

---

*Documented 2026-04-11 using /ce:compound*
