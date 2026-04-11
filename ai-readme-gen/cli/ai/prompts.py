"""Prompt templates for AI interactions."""

from typing import Dict, Any, List


def create_analysis_prompt(codebase_info: Dict[str, Any]) -> str:
    """
    Create a prompt for analyzing a codebase.

    Args:
        codebase_info: Dictionary containing codebase information

    Returns:
        Prompt string for AI analysis
    """
    languages = list(codebase_info.get("languages", {}).keys())
    total_files = len(codebase_info.get("files", []))
    root_files = codebase_info.get("root_files", [])
    directories = codebase_info.get("directories", [])

    prompt = f"""You are a senior software engineer analyzing a codebase for documentation generation.

## Codebase Overview
- **Total files**: {total_files}
- **Languages detected**: {', '.join(languages)}
- **Root-level files**: {', '.join(root_files)}
- **Directory structure**: {', '.join(directories[:5])}{'...' if len(directories) > 5 else ''}

## Analysis Task
Analyze this codebase and provide a comprehensive summary including:

1. **Project Purpose**: What does this project do?
2. **Key Components**: What are the main modules/components?
3. **Architecture Patterns**: What design patterns are used?
4. **Dependencies**: What external libraries/packages are used?
5. **Data Flow**: How does data move through the system?
6. **Entry Points**: What are the main entry points?

Respond in JSON format with the following structure:
{{
  "project_purpose": "string",
  "key_components": ["component1", "component2", ...],
  "architecture_patterns": ["pattern1", "pattern2", ...],
  "dependencies": ["dep1", "dep2", ...],
  "data_flow": "string",
  "entry_points": ["entry1", "entry2", ...]
}}
"""
    return prompt


def create_readme_prompt(codebase_info: Dict[str, Any], metadata: Dict[str, Any],
                         analysis: Dict[str, Any]) -> str:
    """
    Create a prompt for generating a README.

    Args:
        codebase_info: Dictionary containing codebase information
        metadata: Project metadata
        analysis: AI analysis results

    Returns:
        Prompt string for README generation
    """
    prompt = f"""You are a senior technical writer creating a high-quality README.md for a software project.

## Project Information
- **Name**: {metadata.get('name', 'Unknown')}
- **Description**: {metadata.get('description', 'No description available')}
- **Version**: {metadata.get('version', '0.1.0')}

## Codebase Analysis
- **Languages**: {', '.join(list(codebase_info.get('languages', {}).keys()))}
- **Total Files**: {len(codebase_info.get('files', []))}
- **Key Components**: {', '.join(analysis.get('key_components', []))}

## AI Analysis Summary
{analysis.get('project_purpose', 'No analysis available')}

{analysis.get('data_flow', '')}

## Instructions
Write a comprehensive README.md including these sections:

### 1. Project Title and Description
- Clear, engaging title
- Brief description of what the project does
- Key features/benefits

### 2. Installation
- Prerequisites
- Step-by-step installation instructions
- Environment variables (if any)

### 3. Usage
- Basic usage examples
- Common use cases

### 4. Architecture
- High-level architecture overview
- Component descriptions

### 5. Configuration
- Configuration options
- Environment variables

### 6. API Reference (if applicable)
- List of endpoints/interfaces

### 7. Contributing
- How to contribute
- Development setup

### 8. License
- License information

## Requirements
- Write like a senior engineer documenting for onboarding
- Be clear, concise, and accurate
- No hallucination of non-existent features
- Use proper Markdown formatting
"""
    return prompt


def create_diagram_prompt(codebase_info: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """
    Create a prompt for generating ASCII architecture diagrams.

    Args:
        codebase_info: Dictionary containing codebase information
        analysis: AI analysis results

    Returns:
        Prompt string for diagram generation
    """
    prompt = f"""You are a technical architect creating ASCII art diagrams for a software project.

## Project Information
- **Name**: {analysis.get('project_purpose', 'Unknown project')}
- **Key Components**: {', '.join(analysis.get('key_components', []))}
- **Languages**: {', '.join(list(codebase_info.get('languages', {}).keys()))}

## Analysis Summary
{analysis.get('data_flow', '')}

## Instructions
Create ASCII art diagrams showing:

1. **Component Hierarchy**: A tree-like structure showing how components relate
2. **Data Flow**: How data moves between components
3. **Module Relationships**: How modules interact with each other

## Requirements
- Use simple ASCII characters (boxes, arrows, lines)
- Keep diagrams readable and not too wide
- Use consistent formatting
- Include brief labels for each component
- Focus on high-level structure, not implementation details

Respond with valid ASCII art that can be directly rendered in a terminal.
"""
    return prompt


def create_api_docs_prompt(codebase_info: Dict[str, Any], endpoints: List[Dict[str, Any]]) -> str:
    """
    Create a prompt for generating API documentation.

    Args:
        codebase_info: Dictionary containing codebase information
        endpoints: List of API endpoint definitions

    Returns:
        Prompt string for API documentation generation
    """
    if not endpoints:
        return "No API endpoints found. Skip API documentation section."

    prompt = f"""You are a technical writer creating API documentation.

## Endpoints Found
{len(endpoints)} endpoints detected:
"""

    for ep in endpoints[:10]:  # Limit to first 10
        prompt += f"- {ep.get('method', 'GET').upper()} {ep.get('path', '')}\n"

    prompt += """

## Instructions
Generate API documentation including:

1. **Endpoint Summary**: Brief description of each endpoint
2. **Request Details**: Parameters, body schema (if known)
3. **Response Format**: Response structure
4. **Examples**: Request/response examples

## Requirements
- Use proper Markdown formatting
- Include code blocks for examples
- Be accurate - don't hallucinate parameters
- Group related endpoints together
"""
    return prompt


def create_review_prompt(readme_content: str, codebase_info: Dict[str, Any]) -> str:
    """
    Create a prompt for reviewing generated README content.

    Args:
        readme_content: The generated README content
        codebase_info: Dictionary containing codebase information

    Returns:
        Prompt string for review
    """
    prompt = f"""You are a senior technical reviewer reviewing a generated README.md.

## Generated README
```
{readme_content}
```

## Codebase Context
- **Languages**: {', '.join(list(codebase_info.get('languages', {}).keys()))}
- **Total Files**: {len(codebase_info.get('files', []))}
- **Root Files**: {', '.join(codebase_info.get('root_files', []))}

## Review Checklist
Check the following and provide feedback:

1. **Accuracy**: Does the README accurately reflect the codebase?
2. **Completeness**: Are important features documented?
3. **Clarity**: Is the writing clear and concise?
4. **Formatting**: Is Markdown formatting correct?
5. **Hallucination**: Are there any claims about non-existent features?

Provide specific feedback on each point. If issues are found, suggest corrections.
"""
    return prompt
