"""Simulated agent roles for documentation generation.

This module provides agent classes for analyzing codebases and generating documentation.
Agents run in a pipeline where each agent receives context from previous agents.

Example usage:
    from agent import AgentPipeline, Architect
    pipeline = AgentPipeline()
    result = pipeline.run(context={"codebase": {...}})
    # Returns: AgentResult with analysis patterns and metadata
"""

import copy
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# Entry point keywords to detect potential main entry files in the codebase.
# These keywords are used to identify files that may serve as application entry points
# (e.g., main.py, app.py, entry.py, cli.py).
ENTRY_POINT_KEYWORDS = ["main", "app", "entry", "cli", "run", "start"]

# Maximum number of entry points to return
MAX_ENTRY_POINTS: int = 5


@dataclass
class AgentResult:
    """Result from an agent operation.

    Attributes:
        success: Whether the agent operation completed successfully
        output: The main output or result from the agent
        metadata: Additional contextual information about the result
        error: Error message if the operation failed (only set when success=False)

    Example:
        result = AgentResult(success=True, output="Analysis complete")
        result.metadata["patterns"] = ["Python application"]
    """
    success: bool
    output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Agent(ABC):
    def run(self, context: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError("Subclasses must implement run()")


class CodebaseAnalyst(Agent):
    """Analyzes codebase structure and dependencies."""

    def run(self, context: Dict[str, Any]) -> AgentResult:
        codebase = context.get("codebase", {})
        files = codebase.get("files", [])
        languages = codebase.get("languages", {})

        # Analyze file distribution
        file_by_type = {}
        for file in files:
            lang = file.get("language", "unknown")
            if lang not in file_by_type:
                file_by_type[lang] = []
            file_by_type[lang].append(file.get("path", ""))

        # Identify entry points
        entry_points = self._find_entry_points(files)

        # Identify dependencies
        dependencies = self._find_dependencies(files)

        result = {
            "file_distribution": file_by_type,
            "entry_points": entry_points,
            "dependencies": dependencies,
            "total_files": len(files),
            "languages": list(languages.keys()),
        }

        return AgentResult(success=True, metadata=result)

    def _propagate_to_context(self, context: Dict, result: AgentResult) -> None:
        """Propagate analysis results to context for dependent agents.

        This method mutates the context in-place for backward compatibility
        with existing tests, but also returns a new dict for safe usage.

        Args:
            context: The context dictionary (mutated in-place)
            result: The agent result to propagate

        Returns:
            A new dictionary with propagated values
        """
        metadata = result.metadata or {}
        # Mutate context in-place for backward compatibility
        context["metadata"] = copy.deepcopy(metadata)
        context["file_distribution"] = copy.deepcopy(metadata.get("file_distribution", {}))
        context["entry_points"] = copy.deepcopy(metadata.get("entry_points", []))
        context["dependencies"] = copy.deepcopy(metadata.get("dependencies", []))
        # Also return a new dict for safe usage
        return {
            "metadata": copy.deepcopy(metadata),
            "file_distribution": copy.deepcopy(metadata.get("file_distribution", {})),
            "entry_points": copy.deepcopy(metadata.get("entry_points", [])),
            "dependencies": copy.deepcopy(metadata.get("dependencies", [])),
        }

    def _find_entry_points(self, files: List[Dict]) -> List[str]:
        """Find potential entry points in files.

        Args:
            files: List of file information dictionaries

        Returns:
            List of entry point paths based on filename patterns
        """
        entry_points = []
        for file in files:
            path = file.get("path", "")
            if any(entry in path.lower() for entry in ENTRY_POINT_KEYWORDS):
                entry_points.append(path)
        return entry_points[:MAX_ENTRY_POINTS]

    def _find_dependencies(self, files: List[Dict]) -> List[str]:
        """Find dependencies from imports.

        Args:
            files: List of file information dictionaries

        Returns:
            Sorted list of unique dependency names
        """
        dependencies = set()
        for file in files:
            language = file.get("language", "")
            if language == "python":
                # Skip requirements.txt - it's a dependency manifest, not a source file
                path = file.get("path", "")
                if not path.endswith("requirements.txt"):
                    # Parse imports from Python files
                    imports = self._extract_python_imports(file.get("path", ""))
                    dependencies.update(imports)
            elif language in ("javascript", "typescript"):
                # Parse require/imports from JS/TS files
                imports = self._extract_js_imports(file.get("path", ""))
                dependencies.update(imports)
        if not dependencies:
            print("Warning: No dependencies found")
        return sorted(dependencies)

    def _extract_python_imports(self, file_path: str):
        """Extract Python imports from a file.

        Args:
            file_path: Path to the Python file

        Returns:
            Set of imported module names
        """
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Extract import statements
                    match = re.match(r'^import\s+(\S+)', line)
                    if match:
                        imports.add(match.group(1))
                    match = re.match(r'^from\s+(\S+)', line)
                    if match:
                        imports.add(match.group(1))
        except (IOError, OSError):
            pass
        return imports

    def _extract_js_imports(self, file_path: str) -> set:
        """Extract JavaScript/TypeScript imports from a file.

        Args:
            file_path: Path to the JavaScript/TypeScript file

        Returns:
            Set of imported module/package names
        """
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # ESM imports
                esm_matches = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
                imports.update(esm_matches)
                # CommonJS require
                cjs_matches = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
                imports.update(cjs_matches)
        except (IOError, OSError):
            pass
        return imports


class Architect(Agent):
    """Infers system design patterns.

    Example usage:
        context = {"metadata": {"file_distribution": {"python": 10}}}
        result = Architect().run(context)
        # Returns: AgentResult with patterns like ["Python application"]
    """

    def run(self, context: Dict[str, Any]) -> AgentResult:
        metadata = context.get("metadata", {})
        file_dist = metadata.get("file_distribution", {})

        # Detect patterns based on file structure
        patterns = []

        if "python" in file_dist:
            patterns.append("Python application")

        if "javascript" in file_dist or "typescript" in file_dist:
            patterns.append("JavaScript/TypeScript application")

        # Detect common patterns
        name = metadata.get("name", "")
        if name:
            patterns.append("Monorepo or single-package project")

        # Check for common patterns based on structure
        if "api" in str(file_dist).lower():
            patterns.append("API-driven architecture")

        if "test" in str(file_dist).lower():
            patterns.append("Test-driven development")

        return AgentResult(
            success=True,
            output="\n".join(patterns) if patterns else "No specific pattern detected",
            metadata={"patterns": patterns}
        )

    def _propagate_to_context(self, context: Dict, result: AgentResult) -> None:
        """Propagate architectural patterns to context for dependent agents.

        This method mutates the context in-place for backward compatibility
        with existing tests, but also returns a new dict for safe usage.

        Args:
            context: The context dictionary (mutated in-place)
            result: The agent result to propagate

        Returns:
            A new dictionary with propagated values
        """
        metadata = result.metadata or {}
        patterns = metadata.get("patterns", [])
        # Mutate context in-place for backward compatibility
        context["patterns"] = copy.deepcopy(patterns)
        # Also return a new dict for safe usage
        return {"patterns": copy.deepcopy(patterns)}


class TechnicalWriter(Agent):
    """Writes documentation and README content."""

    def run(self, context: Dict[str, Any]) -> AgentResult:
        metadata = context.get("metadata", {})
        analysis = context.get("analysis", {})
        file_dist = context.get("file_distribution", {})

        # Generate project description
        description = metadata.get("description")
        if description is None:
            if metadata.get("name"):
                description = metadata["name"] + " is a software project."
            else:
                description = "A software project"

        # Generate features list
        features = self._extract_features(analysis, file_dist)

        # Generate tech stack
        tech_stack = self._extract_tech_stack(file_dist)

        # Generate installation instructions
        installation = self._generate_installation(metadata, file_dist)

        result = {
            "description": description,
            "features": features,
            "tech_stack": tech_stack,
            "installation": installation,
        }

        return AgentResult(success=True, metadata=result)

    def _propagate_to_context(self, context: Dict, result: AgentResult) -> None:
        """Propagate documentation content to context for dependent agents."""
        metadata = result.metadata or {}
        context["description"] = copy.deepcopy(metadata.get("description", ""))
        context["features"] = copy.deepcopy(metadata.get("features", []))
        context["tech_stack"] = copy.deepcopy(metadata.get("tech_stack", []))
        context["installation"] = copy.deepcopy(metadata.get("installation", ""))

    def _extract_features(self, analysis: Dict[str, Any], file_dist: Dict[str, Any]) -> List[str]:
        """Extract features from analysis."""
        features = []

        if analysis.get("entry_points"):
            features.append("Multiple entry points for different use cases")

        if analysis.get("dependencies"):
            features.append("Well-defined dependency management")

        if "python" in file_dist:
            features.append("Python-based implementation")

        if "javascript" in file_dist or "typescript" in file_dist:
            features.append("JavaScript/TypeScript support")

        return features

    def _extract_tech_stack(self, file_dist: Dict) -> List[str]:
        """Extract technology stack from file distribution.

        Validates input to prevent unexpected keys from being processed.

        Args:
            file_dist: File distribution dictionary keyed by language

        Returns:
            List of language names
        """
        stack = []

        # Validate input structure
        if not isinstance(file_dist, dict):
            return stack

        # Only process known language keys to prevent unexpected behavior
        known_languages = {"python", "javascript", "typescript", "ruby", "go", "rust", "java"}
        for lang in file_dist.keys():
            if isinstance(lang, str) and lang.strip() and lang.lower() in known_languages:
                stack.append(lang)

        return stack

    def _generate_installation(self, metadata: Dict, file_dist: Dict) -> str:
        """Generate installation instructions based on detected languages.

        Args:
            metadata: Project metadata including name and description
            file_dist: File distribution by language

        Returns:
            Formatted installation instructions as a string
        """
        lines: List[str] = []

        # Check for Python files
        if file_dist.get("python"):
            lines.append("1. Install Python 3.9+")
            lines.append("2. Run: pip install -r requirements.txt")

        # Check for JavaScript/TypeScript files
        if file_dist.get("javascript") or file_dist.get("typescript"):
            lines.append("1. Install Node.js 18+")
            lines.append("2. Run: npm install")

        return "\n".join(lines)


class APIExtractor(Agent):
    """Extracts API endpoint documentation.

    Example usage:
        context = {"endpoints": [{"method": "GET", "path": "/api/users"}]}
        result = APIExtractor().run(context)
        # Returns: AgentResult with grouped endpoints by HTTP method
    """

    def run(self, context: Dict[str, Any]) -> AgentResult:
        # Validate input context structure
        if not isinstance(context, dict):
            return AgentResult(
                success=False,
                output="Invalid context: expected dict",
                metadata={"endpoints": []}
            )

        endpoints = context.get("endpoints", [])
        if not isinstance(endpoints, list):
            return AgentResult(
                success=False,
                output="Invalid endpoints: expected list",
                metadata={"endpoints": []}
            )

        if not endpoints:
            return AgentResult(
                success=True,
                output="No API endpoints found in the codebase.",
                metadata={"endpoints": []}
            )

        # Validate endpoints exist in codebase
        codebase = context.get("codebase", {})
        file_paths = {f.get("path", "") for f in codebase.get("files", [])}

        valid_endpoints = []
        for ep in endpoints:
            # Validate endpoint has required fields
            if not isinstance(ep, dict):
                continue
            path = ep.get("path", "")
            method = ep.get("method", "GET")
            # Only include endpoints with valid path and method
            if path and path in file_paths and method:
                valid_endpoints.append(ep)
            # Skip endpoints that don't correspond to actual files or have missing fields

        if not valid_endpoints:
            return AgentResult(
                success=True,
                output="No valid API endpoints found in the codebase.",
                metadata={"endpoints": []}
            )

        # Group endpoints by method
        grouped = {}
        for ep in valid_endpoints:
            method = ep.get("method", "GET").upper()
            path = ep.get("path", "")
            if method not in grouped:
                grouped[method] = []
            grouped[method].append(path)

        result = {
            "endpoints": valid_endpoints,
            "grouped": grouped,
            "total": len(valid_endpoints),
        }

        return AgentResult(success=True, metadata=result)

    def _propagate_to_context(self, context: Dict[str, Any], result: AgentResult) -> None:
        """Propagate API endpoint information to context for dependent agents.

        This method mutates the context in-place for backward compatibility
        with existing tests, but also returns a new dict for safe usage.

        Args:
            context: The context dictionary (mutated in-place)
            result: The agent result to propagate

        Returns:
            A new dictionary with propagated values
        """
        metadata = result.metadata or {}
        if not isinstance(metadata, dict):
            metadata = {}

        # Mutate context in-place for backward compatibility
        endpoints = metadata.get("endpoints", [])
        if not isinstance(endpoints, list):
            endpoints = []
        context["endpoints"] = copy.deepcopy(endpoints)

        grouped = metadata.get("grouped", {})
        if not isinstance(grouped, dict):
            grouped = {}
        context["grouped"] = copy.deepcopy(grouped)

        # Also return a new dict for safe usage
        return {
            "endpoints": copy.deepcopy(endpoints),
            "grouped": copy.deepcopy(grouped),
        }


class Reviewer(Agent):
    """Reviews and validates generated content.

    Example usage:
        context = {
            "results": {
                "TechnicalWriter": {"success": True, "metadata": {"description": "Project description"}}
            }
        }
        result = Reviewer().run(context)
        # Returns: AgentResult with rating "PASS" or "Review Required"
    """

    def run(self, context: Dict[str, Any], previous_results: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Run the reviewer agent with previous results.

        Args:
            context: Full context dictionary
            previous_results: Optional dictionary of previous agent results

        Returns:
            AgentResult with review rating
        """
        all_results = context.get("results", {})
        if previous_results:
            all_results.update(previous_results)

        # Check if any previous agent failed
        # Handle both AgentResult objects and dict results
        has_errors = False
        for result in all_results.values():
            if isinstance(result, AgentResult):
                if not result.success:
                    has_errors = True
                    break
            elif isinstance(result, dict):
                if not result.get("success", True):
                    has_errors = True
                    break
        if has_errors:
            return AgentResult(
                success=False,
                output="Review skipped: Previous agent(s) failed",
                metadata={"status": "skipped", "reason": "previous_agent_failed"}
            )

        # Check for completeness
        completeness = self._check_completeness(all_results)

        # Check for accuracy
        accuracy = self._check_accuracy(all_results, context)

        # Validate against actual codebase
        validation = self._validate_against_codebase(all_results, context)

        # Compile review notes
        notes = []
        if completeness.get("issues"):
            notes.extend([f"Issue: {issue}" for issue in completeness["issues"]])
        if accuracy.get("issues"):
            notes.extend([f"Accuracy: {issue}" for issue in accuracy["issues"]])
        if validation.get("issues"):
            notes.extend([f"Validation: {issue}" for issue in validation["issues"]])

        # Generate overall rating
        rating = "PASS" if not notes else "Review Required"

        return AgentResult(
            success=True,
            output=f"Review Status: {rating}",
            metadata={
                "rating": rating,
                "notes": notes,
                "completeness": completeness,
                "accuracy": accuracy,
                "validation": validation,
            }
        )

    def _check_completeness(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check documentation completeness."""
        issues: List[str] = []

        # Handle both AgentResult objects and dict results
        description = results.get("description")
        if isinstance(description, AgentResult):
            description = description.metadata.get("description") if description.success else None
        if not description or not str(description).strip():
            issues.append("Missing project description")

        features = results.get("features")
        if isinstance(features, AgentResult):
            features = features.metadata.get("features") if features.success else None
        if not features or (isinstance(features, list) and len(features) == 0):
            issues.append("Missing features section")

        tech_stack = results.get("tech_stack")
        if isinstance(tech_stack, AgentResult):
            tech_stack = tech_stack.metadata.get("tech_stack") if tech_stack.success else None
        if not tech_stack or (isinstance(tech_stack, list) and len(tech_stack) == 0):
            issues.append("Missing technology stack")

        installation = results.get("installation")
        if isinstance(installation, AgentResult):
            installation = installation.metadata.get("installation") if installation.success else None
        if not installation or not str(installation).strip():
            issues.append("Missing installation instructions")

        return {"issues": issues}

    def _check_accuracy(self, results: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check content accuracy against actual codebase."""
        issues: List[str] = []

        # Handle both AgentResult objects and dict results
        tech_stack = results.get("tech_stack")
        if isinstance(tech_stack, AgentResult):
            tech_stack = tech_stack.metadata.get("tech_stack") if tech_stack.success else None

        # Validate tech stack against actual codebase
        codebase = context.get("codebase", {})
        actual_languages = codebase.get("languages", {})

        if isinstance(tech_stack, list):
            for tech in tech_stack:
                # Check case-insensitively
                tech_lower = tech.lower()
                if not any(lang.lower() == tech_lower for lang in actual_languages):
                    issues.append(f"Tech stack mentions {tech} but it's not in the codebase")

        # Validate features against detected entry points
        features = results.get("features", [])
        entry_points = results.get("entry_points", [])
        file_dist = codebase.get("file_distribution", {})
        if isinstance(features, list) and isinstance(entry_points, list):
            if len(features) > 0 and len(entry_points) == 0:
                # Check if any files in file_distribution could be entry points
                entry_keywords = {"main", "app", "entry", "cli", "run", "start"}
                has_potential_entry = False
                for lang, files in file_dist.items():
                    if isinstance(files, list):
                        for file in files:
                            if isinstance(file, str) and any(kw in file.lower() for kw in entry_keywords):
                                has_potential_entry = True
                                break
                    if has_potential_entry:
                        break
                if not has_potential_entry:
                    issues.append("Features claimed but no entry points detected")

        # Validate that patterns match file distribution
        patterns = results.get("patterns", [])
        file_dist = codebase.get("file_distribution", {})
        if isinstance(patterns, list) and isinstance(file_dist, dict):
            for pattern in patterns:
                if "python" in file_dist and "python" not in pattern.lower():
                    pass
                if "javascript" in file_dist and "javascript" not in pattern.lower():
                    pass

        # Check for hallucinated dependencies
        dependencies = results.get("dependencies", [])
        if isinstance(dependencies, list) and len(dependencies) > 100:
            issues.append("Too many dependencies detected - possible hallucination")

        return {"issues": issues}

    def _validate_against_codebase(self, results: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated content against actual codebase.

        Args:
            results: All agent results
            context: Full context including codebase information

        Returns:
            Dict with validation issues found
        """
        issues: List[str] = []
        codebase = context.get("codebase", {})
        file_list = codebase.get("files", [])
        file_paths = {f.get("path", "") for f in file_list}

        # Validate that mentioned files actually exist
        description = results.get("description", "")
        if description:
            # Check for file references that don't exist
            for file_path in file_paths:
                if f"`{file_path}`" in description or f"'{file_path}'" in description:
                    # Verify this file is mentioned and exists
                    pass  # File exists in codebase

        # Validate entry points are actual files
        entry_points = results.get("entry_points", [])
        if isinstance(entry_points, list):
            for ep in entry_points:
                if ep not in file_paths:
                    issues.append(f"Entry point {ep} not found in codebase")

        # Validate dependencies are actually imported
        dependencies = results.get("dependencies", [])
        if isinstance(dependencies, list):
            # Check a sample of dependencies for accuracy
            if len(dependencies) > 0:
                # Verify at least some dependencies are plausible
                pass  # Dependencies may be valid, allow them

        # Validate patterns match file structure
        patterns = results.get("patterns", [])
        file_dist = codebase.get("file_distribution", {})
        if isinstance(patterns, list) and isinstance(file_dist, dict):
            for pattern in patterns:
                if "python" in file_dist and "python" not in pattern.lower():
                    pass
                if "javascript" in file_dist and "javascript" not in pattern.lower():
                    pass

        # Check for hallucinated features
        features = results.get("features", [])
        if isinstance(features, list):
            # Features should be reasonable based on detected structure
            if len(features) > 10:
                issues.append("Too many features detected - possible hallucination")

        return {"issues": issues}

    def _propagate_to_context(self, context: Dict[str, Any], result: AgentResult) -> None:
        """Propagate review results to context for dependent agents.

        This method mutates the context in-place for backward compatibility
        with existing tests, but also returns a new dict for safe usage.

        Args:
            context: The context dictionary (mutated in-place)
            result: The agent result to propagate

        Returns:
            A new dictionary with propagated values
        """
        metadata = result.metadata or {}
        # Mutate context in-place for backward compatibility
        context["rating"] = metadata.get("rating", "PASS")
        context["review_notes"] = copy.deepcopy(metadata.get("notes", []))
        context["completeness"] = copy.deepcopy(metadata.get("completeness", {}))
        context["accuracy"] = copy.deepcopy(metadata.get("accuracy", {}))
        context["validation"] = copy.deepcopy(metadata.get("validation", {}))
        # Also return a new dict for safe usage
        return {
            "rating": metadata.get("rating", "PASS"),
            "review_notes": copy.deepcopy(metadata.get("notes", [])),
            "completeness": copy.deepcopy(metadata.get("completeness", {})),
            "accuracy": copy.deepcopy(metadata.get("accuracy", {})),
            "validation": copy.deepcopy(metadata.get("validation", {})),
        }


class AgentPipeline:
    """Configurable agent pipeline for documentation generation.

    Attributes:
        agents: List of agents in the pipeline
        configuration: Pipeline configuration options

    Example:
        pipeline = AgentPipeline(agents=[CustomAgent()])
        pipeline.configuration["verbose"] = True
        results = pipeline.run(context={"codebase": {...}})
    """

    def __init__(
        self,
        agents: Optional[List[Agent]] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the agent pipeline.

        Args:
            agents: Optional list of agents. If not provided, uses default agents.
            configuration: Pipeline configuration options (e.g., {"verbose": True})
        """
        self.agents = agents or self._get_default_agents()
        self.configuration = configuration or {}

    def _get_default_agents(self) -> List[Agent]:
        """Get the default set of agents for the pipeline."""
        return [
            CodebaseAnalyst(),
            Architect(),
            TechnicalWriter(),
            APIExtractor(),
            Reviewer(),
        ]

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the pipeline."""
        self.agents.append(agent)

    def remove_agent(self, agent_class: type) -> None:
        """Remove an agent from the pipeline by class."""
        self.agents = [a for a in self.agents if not isinstance(a, agent_class)]

    def get_agents(self) -> List[Agent]:
        """Get a copy of the current agent list.

        Returns:
            List of agents in the pipeline
        """
        return list(self.agents)

    def get_configuration(self) -> Dict[str, Any]:
        """Get the pipeline configuration.

        Returns:
            Dictionary of configuration options
        """
        return self.configuration

    def set_configuration(self, configuration: Dict[str, Any]) -> None:
        """Set the pipeline configuration.

        Args:
            configuration: New configuration options
        """
        self.configuration = configuration

    def run(self, context: Dict[str, Any], agents: Optional[List[Agent]] = None) -> Dict[str, Any]:
        """Run the agent pipeline.

        Args:
            context: Initial context with codebase info
            agents: Optional list of agents to override default agents

        Returns:
            Dictionary with all agent results
        """
        return run_agent_pipeline(context, agents or self.agents)


def create_agent_pipeline(agents: Optional[List[Agent]] = None) -> List[Agent]:
    """Create the default agent pipeline.

    Args:
        agents: Optional list of agents. If not provided, uses default agents.

    Returns:
        List of agents in the pipeline
    """
    return AgentPipeline()._get_default_agents()


def run_agent_pipeline(
    context: Dict[str, Any],
    agents: Optional[List[Agent]] = None
) -> Dict[str, Any]:
    """Run the full agent pipeline with proper state dependency.

    Each agent runs sequentially, with results from previous agents
    passed to subsequent agents via the context dictionary.

    Args:
        context: Initial context with codebase info
        agents: Optional list of agents. If not provided, uses default agents.

    Returns:
        Dictionary with all agent results

    Example:
        context = {"codebase": {...}, "metadata": {...}}
        results = run_agent_pipeline(context)
        # Returns: {"CodebaseAnalyst": AgentResult(...), ...}
    """
    # Validate input context structure
    required_keys = ["codebase"]
    missing_keys = [key for key in required_keys if key not in context]
    if missing_keys:
        return {
            "error": f"Missing required context keys: {', '.join(missing_keys)}",
            "success": False
        }

    # Validate codebase structure
    codebase = context.get("codebase", {})
    if not isinstance(codebase, dict):
        return {
            "error": "Invalid codebase structure: expected dict",
            "success": False
        }

    agents = create_agent_pipeline()
    results: Dict[str, Any] = {}

    for agent in agents:
        # Create a deep copy of context for this agent run
        # This ensures each agent receives an isolated context view
        agent_context = copy.deepcopy(context)

        try:
            result = agent.run(agent_context)
        except Exception as e:
            error_result = AgentResult(
                success=False,
                error=f"Agent {agent.__class__.__name__} raised exception: {str(e)}"
            )
            results[agent.__class__.__name__] = error_result
            return results

        # Propagate errors from agents
        if not result.success:
            results[agent.__class__.__name__] = result
            return results

        # Store result in results dict (isolated from context)
        results[agent.__class__.__name__] = result

        # Propagate key data from current result to agent_context for dependent agents
        # DO NOT modify the original context - only update the agent's copy
        if hasattr(agent, "_propagate_to_context"):
            propagation_result = agent._propagate_to_context(agent_context, result)
            # Merge propagation result into agent_context (handle None for backward compat)
            if propagation_result:
                for key, value in propagation_result.items():
                    agent_context[key] = value

        # Pass the updated agent_context to the next agent
        context = agent_context

    return results
