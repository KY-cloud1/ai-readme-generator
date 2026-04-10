"""Simulated agent roles for documentation generation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass, field


# Entry point keywords to detect potential main entry files in the codebase.
# These keywords are used to identify files that may serve as application entry points
# (e.g., main.py, app.py, entry.py, cli.py).
ENTRY_POINT_KEYWORDS = ["main", "app", "entry", "cli"]


@dataclass
class AgentResult:
    """Result from an agent operation.

    Attributes:
        success: Whether the agent operation completed successfully
        output: The main output or result from the agent
        metadata: Additional contextual information about the result
        error: Error message if the operation failed (only set when success=False)
    """
    success: bool
    output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Agent(ABC):
    @abstractmethod
    def run(self, context: Dict[str, Any]) -> AgentResult:
        pass


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
        """Propagate analysis results to context for dependent agents."""
        metadata = result.metadata or {}
        context["metadata"] = metadata
        context["file_distribution"] = metadata.get("file_distribution", {})
        context["entry_points"] = metadata.get("entry_points", [])
        context["dependencies"] = metadata.get("dependencies", [])

    def _find_entry_points(self, files: List[Dict]) -> List[str]:
        """Find potential entry points in files.

        Returns up to 5 entry points based on filename patterns.
        The limit prevents overwhelming the analysis with too many candidates
        and focuses on the most likely entry points.
        """
        entry_points: List[str] = []
        for file in files:
            path = file.get("path", "")
            if any(entry in path.lower() for entry in ENTRY_POINT_KEYWORDS):
                entry_points.append(path)
        return entry_points[:5]  # Limit to top 5 most likely entry points

    def _find_dependencies(self, files: List[Dict]) -> List[str]:
        """Find dependencies from imports."""
        dependencies: set = set()
        for file in files:
            if file.get("language") == "python":
                # Check requirements.txt
                if "requirements.txt" in file.get("path", ""):
                    # In a full implementation, we would parse this file
                    continue
                # Parse imports from Python files
                imports = self._extract_python_imports(file.get("path", ""))
                dependencies.update(imports)
            elif file.get("language") in ["javascript", "typescript"]:
                # Parse require/imports from JS/TS files
                imports = self._extract_js_imports(file.get("path", ""))
                dependencies.update(imports)
        return sorted(list(dependencies))

    def _extract_python_imports(self, file_path: str) -> set:
        """Extract Python imports from a file."""
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
        """Extract JavaScript/TypeScript imports from a file."""
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
    """Infers system design patterns."""

    def run(self, context: Dict[str, Any]) -> AgentResult:
        metadata = context.get("metadata", {})
        file_dist = metadata.get("file_distribution", {})

        # Detect patterns based on file structure
        patterns: List[str] = []

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
        """Propagate architectural patterns to context for dependent agents."""
        metadata = result.metadata or {}
        patterns = metadata.get("patterns", [])
        context["patterns"] = patterns


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
        context["description"] = metadata.get("description", "")
        context["features"] = metadata.get("features", [])
        context["tech_stack"] = metadata.get("tech_stack", [])
        context["installation"] = metadata.get("installation", "")

    def _extract_features(self, analysis: Dict, file_dist: Dict) -> List[str]:
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

        return features[:5]

    def _extract_tech_stack(self, file_dist: Dict) -> List[str]:
        """Extract technology stack from file distribution."""
        stack = []

        for lang in file_dist.keys():
            stack.append(lang)

        return stack

    def _generate_installation(self, metadata: Dict, file_dist: Dict) -> str:
        """Generate installation instructions."""
        lines: List[str] = []

        if "python" in file_dist:
            lines.append("1. Install Python 3.9+")
            lines.append("2. Run: pip install -r requirements.txt")

        if "javascript" in file_dist or "typescript" in file_dist:
            lines.append("1. Install Node.js 18+")
            lines.append("2. Run: npm install")

        return "\n".join(lines)


class APIExtractor(Agent):
    """Extracts API endpoint documentation."""

    def run(self, context: Dict[str, Any]) -> AgentResult:
        endpoints = context.get("endpoints", [])

        if not endpoints:
            return AgentResult(
                success=True,
                output="No API endpoints found in the codebase.",
                metadata={"endpoints": []}
            )

        # Group endpoints by method
        grouped = {}
        for ep in endpoints:
            method = ep.get("method", "GET").upper()
            path = ep.get("path", "")
            if method not in grouped:
                grouped[method] = []
            grouped[method].append(path)

        result = {
            "endpoints": endpoints,
            "grouped": grouped,
            "total": len(endpoints),
        }

        return AgentResult(success=True, metadata=result)

    def _propagate_to_context(self, context: Dict[str, Any], result: AgentResult) -> None:
        """Propagate API endpoint information to context for dependent agents."""
        metadata = result.metadata or {}
        context["endpoints"] = metadata.get("endpoints", [])
        context["grouped_endpoints"] = metadata.get("grouped", {})


class Reviewer(Agent):
    """Reviews and validates generated content."""

    def run(self, context: Dict[str, Any]) -> AgentResult:
        all_results = context.get("results", {})

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
        accuracy = self._check_accuracy(all_results)

        # Compile review notes
        notes = []
        if completeness.get("issues"):
            notes.extend([f"Issue: {issue}" for issue in completeness["issues"]])
        if accuracy.get("issues"):
            notes.extend([f"Accuracy: {issue}" for issue in accuracy["issues"]])

        # Generate overall rating
        rating = "Pass" if not notes else "Review Required"

        return AgentResult(
            success=True,
            output=f"Review Status: {rating}",
            metadata={
                "rating": rating,
                "notes": notes,
                "completeness": completeness,
                "accuracy": accuracy,
            }
        )

    def _check_completeness(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check documentation completeness."""
        issues: List[str] = []

        if not results.get("description"):
            issues.append("Missing project description")

        if not results.get("features"):
            issues.append("Missing features section")

        if not results.get("tech_stack"):
            issues.append("Missing technology stack")

        return {"issues": issues}

    def _check_accuracy(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check content accuracy."""
        issues: List[str] = []

        # Would validate against actual codebase here
        return {"issues": issues}

    def _propagate_to_context(self, context: Dict[str, Any], result: AgentResult) -> None:
        """Propagate review results to context for dependent agents."""
        metadata = result.metadata or {}
        context["rating"] = metadata.get("rating", "Pass")
        context["review_notes"] = metadata.get("notes", [])
        context["completeness"] = metadata.get("completeness", {})
        context["accuracy"] = metadata.get("accuracy", {})


class AgentPipeline:
    """Configurable agent pipeline for documentation generation."""

    def __init__(self, agents: Optional[List[Agent]] = None) -> None:
        """
        Initialize the agent pipeline.

        Args:
            agents: Optional list of agents. If not provided, uses default agents.
        """
        self.agents = agents or self._get_default_agents()

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
        """Get a copy of the current agent list."""
        return list(self.agents)


def create_agent_pipeline() -> List[Agent]:
    """Create the default agent pipeline."""
    return AgentPipeline()._get_default_agents()


def run_agent_pipeline(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full agent pipeline.

    Args:
        context: Initial context with codebase info

    Returns:
        Dictionary with all agent results
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
        try:
            result = agent.run(context)
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

        results[agent.__class__.__name__] = result

        # Create a copy of context to avoid mutating the original
        new_context = dict(context)

        # Update context with accumulated results (using copy to avoid mutation)
        import copy
        new_context["results"] = copy.deepcopy(results)
        new_context["result"] = copy.deepcopy(result)

        # Propagate key data from current result to context for dependent agents
        if hasattr(agent, "_propagate_to_context"):
            agent._propagate_to_context(new_context, result)

        # Update context with the new copy
        context = new_context

    return results
