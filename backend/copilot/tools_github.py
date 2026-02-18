"""
GitHub-aware tools for AI Software Engineering Copilot.

Pure analyzer tools — all read from preloaded ctx.repo_context.
No GitHub API calls, no URL parsing, no remote fetching.
Preprocessing pipeline (preprocessing.py) handles all ingestion before agents run.
"""

from __future__ import annotations

import re
from typing import Optional, Dict, Any, List

from agents import RunContextWrapper, function_tool
from chatkit.types import ProgressUpdateEvent

from .context import CopilotChatContext
from .github_service import GitHubURLParser 


# ============================================================================
# CODE ANALYSIS UTILITIES 
# ============================================================================

class CodeAnalyzer:
    """Analyze code for issues, patterns, and quality."""

    @staticmethod
    def analyze_python(code: str, file_path: str) -> Dict[str, Any]:
        issues = []
        metrics = {
            "lines": len(code.split("\n")),
            "functions": len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE)),
            "classes": len(re.findall(r"^\s*class\s+\w+", code, re.MULTILINE)),
            "imports": len(re.findall(r"^(?:import|from)\s+", code, re.MULTILINE)),
        }

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # N+1 Query Pattern
            if re.search(r"for\s+\w+\s+in\s+\w+:", line):
                for j in range(i, min(i + 5, len(lines))):
                    if re.search(r"\.(get|query|filter|find|fetch|select)\s*\(", lines[j - 1]):
                        issues.append({
                            "type": "N+1 Query", "severity": "HIGH", "line": j,
                            "message": "Potential N+1 query pattern: database call inside loop",
                            "recommendation": "Use batch loading or eager loading",
                        })
                        break

            if re.search(r"(password|secret|api_key|token|auth)\s*=\s*['\"][^'\"]{8,}['\"]", line, re.I):
                issues.append({
                    "type": "Hardcoded Secret", "severity": "CRITICAL", "line": i,
                    "message": "Potential hardcoded secret detected",
                    "recommendation": "Use environment variables",
                })

            if re.search(r"execute\s*\([^)]*[+%]|f['\"].*SELECT.*\{", line, re.I):
                issues.append({
                    "type": "SQL Injection", "severity": "CRITICAL", "line": i,
                    "message": "Potential SQL injection vulnerability",
                    "recommendation": "Use parameterized queries",
                })

            if re.match(r"\s*except\s*:", line):
                issues.append({
                    "type": "Bare Except", "severity": "MEDIUM", "line": i,
                    "message": "Bare except clause catches all exceptions",
                    "recommendation": "Specify exception types explicitly",
                })

            if re.match(r"^[A-Z_]+\s*=\s*\{\s*\}$|^[A-Z_]+\s*=\s*\[\s*\]$", line):
                issues.append({
                    "type": "Global Mutable State", "severity": "MEDIUM", "line": i,
                    "message": "Global mutable state can cause issues",
                    "recommendation": "Use dependency injection or class encapsulation",
                })

            if re.match(r"\s*print\s*\(", line):
                issues.append({
                    "type": "Debug Statement", "severity": "LOW", "line": i,
                    "message": "Print statement found (should use logging)",
                    "recommendation": "Use logging module instead",
                })

            if "TODO" in line or "FIXME" in line:
                issues.append({
                    "type": "TODO", "severity": "INFO", "line": i,
                    "message": line.strip(),
                    "recommendation": "Consider addressing this TODO",
                })

        complexity = 1
        for keyword in (r"\bif\b", r"\bfor\b", r"\bwhile\b", r"\bexcept\b", r"\band\b|\bor\b"):
            complexity += len(re.findall(keyword, code))
        normalized = min(10, (complexity / max(1, metrics["lines"])) * 50)

        return {"issues": issues, "metrics": metrics, "complexity_score": round(normalized, 1)}

    @staticmethod
    def analyze_javascript(code: str, file_path: str) -> Dict[str, Any]:
        issues = []
        metrics = {
            "lines": len(code.split("\n")),
            "functions": len(re.findall(r"function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\(", code)),
            "classes": len(re.findall(r"class\s+\w+", code)),
            "imports": len(re.findall(r"^import\s+", code, re.MULTILINE)),
        }

        for i, line in enumerate(code.split("\n"), 1):
            if "console.log" in line:
                issues.append({
                    "type": "Debug Statement", "severity": "LOW", "line": i,
                    "message": "console.log found",
                    "recommendation": "Remove or use proper logging",
                })
            if re.match(r"\s*var\s+", line):
                issues.append({
                    "type": "Deprecated Syntax", "severity": "LOW", "line": i,
                    "message": "Using 'var' instead of 'let' or 'const'",
                    "recommendation": "Use 'const' or 'let'",
                })
            if "eval(" in line:
                issues.append({
                    "type": "Security Risk", "severity": "CRITICAL", "line": i,
                    "message": "eval() is a security risk",
                    "recommendation": "Avoid eval(), use safer alternatives",
                })

        complexity = min(10, (len(issues) + metrics["functions"]) / max(1, metrics["lines"]) * 30)
        return {"issues": issues, "metrics": metrics, "complexity_score": round(complexity, 1)}


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

def _is_code_file(path: str) -> bool:
    CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb"}
    return any(path.endswith(ext) for ext in CODE_EXTS)


# Updated _resolve_file — no legacy fallback needed
def _resolve_file(
    ctx,
    file_path: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve which file to operate on, in priority order:
    1. Explicitly passed file_path argument
    2. repo_context.fetched_file_path (URL pointed to a specific file)
    3. ctx.current_file
    4. First file in repo_context.file_contents
    """
    repo = ctx.repo_context

    if not repo:
        return None, None

    candidates = [
        file_path,
        repo.fetched_file_path,
        ctx.current_file,
    ]

    for candidate in candidates:
        if candidate and candidate in repo.file_contents:
            return candidate, repo.file_contents[candidate]

    # Last resort: first available file
    if repo.file_contents:
        path, content = next(iter(repo.file_contents.items()))
        return path, content

    return None, None


def _get_language(ctx, file_path: Optional[str] = None) -> str:
    """Determine language from file extension or context."""
    if file_path:
        ext_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".jsx": "javascript", ".tsx": "typescript",
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
    return ctx.language or "python"


def _build_tree_str(tree: Dict, prefix: str = "", depth: int = 0, max_depth: int = 3) -> str:
    """Render a nested tree dict as a unicode tree string."""
    if depth >= max_depth:
        return ""
    result = ""
    items = sorted(
        tree.items(),
        key=lambda x: (isinstance(x[1], dict) and "type" not in x[1], x[0]),
    )
    for i, (name, value) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        if isinstance(value, dict) and "type" in value:
            result += f"{prefix}{connector}📄 {name}\n"
        else:
            result += f"{prefix}{connector}📁 {name}/\n"
            new_prefix = prefix + ("    " if is_last else "│   ")
            result += _build_tree_str(value, new_prefix, depth + 1, max_depth)
    return result


# ============================================================================
# TOOLS — PURE ANALYZERS
# ============================================================================

@function_tool(
    name_override="analyze_github_code",
    description_override=(
        "Analyze preloaded repository code for bugs, security issues, and code quality. "
        "Optionally specify file_path to target a specific file. "
        "Use focus='security', 'quality', or 'performance' to narrow results."
    ),
)
async def analyze_github_code(
    context: RunContextWrapper[CopilotChatContext],
    focus: str = "all",
    file_path: Optional[str] = None,
) -> str:
    """Pure analyzer — reads from ctx.repo_context. No GitHub API calls."""
    ctx = context.context.state

    if not ctx.repo_context and not ctx.github_file_content:
        return (
            "❌ No repository loaded. Please provide a GitHub URL in your message, "
            "e.g. https://github.com/owner/repo/blob/main/file.py"
        )

    resolved_path, code = _resolve_file(ctx, file_path)
    if not code:
        return "❌ Could not resolve a file to analyze. Check that the repository was loaded correctly."

    await context.context.stream(ProgressUpdateEvent(text=f"Analyzing {resolved_path}..."))

    language = _get_language(ctx, resolved_path)
    if language == "python":
        result = CodeAnalyzer.analyze_python(code, resolved_path or "")
    elif language in ("javascript", "typescript"):
        result = CodeAnalyzer.analyze_javascript(code, resolved_path or "")
    else:
        return f"⚠️ Analysis not supported for '{language}'. Supported: Python, JavaScript, TypeScript."

    issues = result["issues"]
    metrics = result["metrics"]
    complexity = result["complexity_score"]

    # Persist to context
    ctx.complexity_score = complexity
    ctx.code_smells = [f"{i['type']}: {i['message']}" for i in issues]

    # Apply focus filter
    focus_lower = focus.lower()
    if focus_lower == "security":
        issues = [i for i in issues if i["severity"] in ("CRITICAL", "HIGH")]
    elif focus_lower == "quality":
        issues = [i for i in issues if i["type"] not in ("TODO", "Debug Statement")]
    elif focus_lower == "performance":
        issues = [i for i in issues if "N+1" in i["type"] or "loop" in i["message"].lower()]

    critical = sum(1 for i in issues if i["severity"] == "CRITICAL")
    high = sum(1 for i in issues if i["severity"] == "HIGH")
    medium = sum(1 for i in issues if i["severity"] == "MEDIUM")
    low = sum(1 for i in issues if i["severity"] == "LOW")

    await context.context.stream(ProgressUpdateEvent(text=f"Found {len(issues)} issues in {resolved_path}"))

    response = f"""## Code Analysis: {resolved_path}

### Metrics
- **Lines:** {metrics['lines']} | **Functions:** {metrics['functions']} | **Classes:** {metrics['classes']} | **Imports:** {metrics['imports']}
- **Complexity Score:** {complexity}/10

### Issues ({len(issues)} total)
🔴 Critical: {critical}  🟠 High: {high}  🟡 Medium: {medium}  🔵 Low: {low}

"""
    if issues:
        response += "### Issue Details\n\n"
        for issue in issues[:15]:
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "ℹ️"}.get(
                issue["severity"], "⚪"
            )
            response += (
                f"**{icon} {issue['type']}** (Line {issue['line']}) [{issue['severity']}]\n"
                f"- {issue['message']}\n"
                f"- 💡 {issue['recommendation']}\n\n"
            )
        if len(issues) > 15:
            response += f"*... and {len(issues) - 15} more issues*\n"
    else:
        response += "✅ No issues found for this focus area.\n"

    return response


@function_tool(
    name_override="scan_github_repo_security",
    description_override=(
        "Scan all preloaded repository files for security vulnerabilities. "
        "Analyzes every file already in memory — no GitHub fetching required."
    ),
)
async def scan_github_repo_security(
    context: RunContextWrapper[CopilotChatContext],
) -> str:
    """Pure analyzer — iterates ctx.repo_context.file_contents. No GitHub API calls."""
    ctx = context.context.state
    repo = ctx.repo_context

    if not repo:
        return (
            "❌ No repository loaded. Please provide a GitHub URL, "
            "e.g. https://github.com/owner/repo"
        )

    await context.context.stream(ProgressUpdateEvent(text=f"Scanning {repo.meta.full_name} for vulnerabilities..."))

    all_issues: List[Dict] = []
    scanned_files: List[str] = []

    for file_path, content in repo.file_contents.items():
        if not _is_code_file(file_path):
            continue

        await context.context.stream(ProgressUpdateEvent(text=f"Scanning {file_path}..."))

        language = _get_language(ctx, file_path)
        if language == "python":
            result = CodeAnalyzer.analyze_python(content, file_path)
        elif language in ("javascript", "typescript"):
            result = CodeAnalyzer.analyze_javascript(content, file_path)
        else:
            continue

        security_issues = [
            i for i in result["issues"]
            if i["severity"] in ("CRITICAL", "HIGH")
            or "injection" in i["type"].lower()
            or "secret" in i["type"].lower()
            or "security" in i["type"].lower()
        ]

        for issue in security_issues:
            issue["file"] = file_path
            all_issues.append(issue)

        scanned_files.append(file_path)

    critical_count = sum(1 for i in all_issues if i["severity"] == "CRITICAL")
    high_count = sum(1 for i in all_issues if i["severity"] == "HIGH")
    security_score = max(0, 100 - (critical_count * 25) - (high_count * 15))

    # Persist to context
    ctx.security_score = security_score
    ctx.vulnerabilities = [
        {
            "id": f"SEC-{i + 1:03d}",
            "severity": issue["severity"],
            "type": issue["type"],
            "description": issue["message"],
            "affected_files": [issue["file"]],
            "recommendation": issue["recommendation"],
        }
        for i, issue in enumerate(all_issues)
    ]

    await context.context.stream(
        ProgressUpdateEvent(text=f"Scan complete — {len(all_issues)} vulnerabilities in {len(scanned_files)} files")
    )

    score_icon = "✅" if security_score >= 80 else "⚠️" if security_score >= 50 else "🔴"
    response = f"""## Security Scan: {repo.meta.full_name}

**Security Score:** {security_score}/100 {score_icon}
**Files Scanned:** {len(scanned_files)} (of {repo.total_files} total in repo)
**Vulnerabilities Found:** {len(all_issues)}

### Summary
🔴 Critical: {critical_count}  🟠 High: {high_count}

"""
    if all_issues:
        response += "### Vulnerabilities\n\n"
        for issue in all_issues[:10]:
            icon = "🔴" if issue["severity"] == "CRITICAL" else "🟠"
            response += (
                f"**{icon} {issue['type']}** [{issue['severity']}]\n"
                f"- **File:** `{issue['file']}` (line {issue['line']})\n"
                f"- **Issue:** {issue['message']}\n"
                f"- **Fix:** {issue['recommendation']}\n\n"
            )
        if len(all_issues) > 10:
            response += f"*... and {len(all_issues) - 10} more vulnerabilities*\n"
    else:
        response += "✅ No security vulnerabilities detected in preloaded files.\n"

    response += "\n### Files Scanned\n"
    for f in scanned_files[:10]:
        response += f"- `{f}`\n"
    if len(scanned_files) > 10:
        response += f"- ... and {len(scanned_files) - 10} more\n"

    return response


@function_tool(
    name_override="get_repo_structure",
    description_override=(
        "Display the file tree of the preloaded repository. "
        "No GitHub URL required — reads from preloaded context."
    ),
)
async def get_repo_structure(
    context: RunContextWrapper[CopilotChatContext],
    max_depth: int = 3,
) -> str:
    """Pure analyzer — reads ctx.repo_context.tree. No GitHub API calls."""
    ctx = context.context.state
    repo = ctx.repo_context

    if not repo:
        return (
            "❌ No repository loaded. Please provide a GitHub URL, "
            "e.g. https://github.com/owner/repo"
        )

    await context.context.stream(ProgressUpdateEvent(text="Building repository tree..."))

    tree_str = _build_tree_str(repo.tree, max_depth=max_depth)

    if len(tree_str) > 3000:
        lines = tree_str.split("\n")[:100]
        tree_str = "\n".join(lines) + "\n... (truncated at 100 lines)"

    return f"""## Repository Structure: {repo.meta.full_name}

**Language:** {repo.primary_language or 'Unknown'} | **Framework:** {repo.framework or 'Not detected'}
**Branch:** {repo.meta.default_branch} | **Stars:** ⭐ {repo.meta.stars:,}
```
{repo.meta.name}/
{tree_str}
```

**Total:** {repo.total_files} files, {repo.total_dirs} directories
**Entry Points:** {', '.join(repo.entry_points) or 'None detected'}
**Dependency Files:** {', '.join(repo.dependency_files) or 'None found'}
"""


@function_tool(
    name_override="generate_tests_for_github_file",
    description_override=(
        "Generate unit tests for a preloaded file. "
        "Optionally specify file_path to target a specific file. "
        "Supports pytest and jest frameworks."
    ),
)
async def generate_tests_for_github_file(
    context: RunContextWrapper[CopilotChatContext],
    test_framework: str = "pytest",
    file_path: Optional[str] = None,
) -> str:
    """Pure analyzer — reads from ctx.repo_context. No GitHub API calls."""
    ctx = context.context.state

    if not ctx.repo_context and not ctx.github_file_content:
        return (
            "❌ No repository loaded. Please provide a GitHub URL in your message."
        )

    resolved_path, code = _resolve_file(ctx, file_path)
    if not code:
        return "❌ Could not resolve a file to generate tests for."

    await context.context.stream(ProgressUpdateEvent(text=f"Generating tests for {resolved_path}..."))

    functions = re.findall(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)", code, re.MULTILINE)
    classes = re.findall(r"^\s*class\s+(\w+)", code, re.MULTILINE)

    if not functions and not classes:
        return f"⚠️ No functions or classes found in `{resolved_path}` to generate tests for."

    ctx.test_framework = test_framework
    module_name = resolved_path.split("/")[-1].replace(".py", "") if resolved_path else "module"

    tests = f'''"""
Auto-generated tests for {resolved_path or 'module'}
Generated by AI Software Engineering Copilot
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

# TODO: Update import path to match your project structure
# from {module_name} import {", ".join(f[0] for f in functions[:5])}

'''

    for func_name, params in functions[:10]:
        param_list = [
            p.strip().split(":")[0].split("=")[0].strip()
            for p in params.split(",")
            if p.strip() and p.strip() != "self"
        ]
        is_async = f"async def {func_name}" in code
        indent = "        "

        tests += f'''

class Test{func_name.replace("_", " ").title().replace(" ", "")}:
    """Tests for {func_name}()"""

    {"@pytest.mark.asyncio" if is_async else ""}
    {"async " if is_async else ""}def test_{func_name}_success(self):
        """Test {func_name} with valid input."""
        # Arrange
        {(chr(10) + indent).join(f"{p} = None  # TODO: Set value" for p in param_list) if param_list else "pass  # No params"}

        # Act
        result = {"await " if is_async else ""}{func_name}({", ".join(param_list)})

        # Assert
        assert result is not None

    {"@pytest.mark.asyncio" if is_async else ""}
    {"async " if is_async else ""}def test_{func_name}_edge_case(self):
        """Test {func_name} with edge cases."""
        # TODO: Add edge case tests
        pass
'''

    for class_name in classes[:5]:
        tests += f'''

class Test{class_name}:
    """Tests for {class_name} class."""

    @pytest.fixture
    def instance(self):
        """Create a test instance of {class_name}."""
        return {class_name}()  # TODO: Add constructor args if needed

    def test_initialization(self, instance):
        """Test {class_name} initializes correctly."""
        assert instance is not None
'''

    await context.context.stream(
        ProgressUpdateEvent(text=f"Generated tests for {len(functions)} functions, {len(classes)} classes")
    )

    return f"""## Generated Tests: {resolved_path}

**Framework:** {test_framework}
**Functions covered:** {len(functions)}
**Classes covered:** {len(classes)}
```python
{tests}
```

### Next Steps
1. Save as `test_{module_name}.py`
2. Update the import path at the top
3. Fill in `# TODO` sections with real test values
4. Run with: `pytest test_{module_name}.py -v`
"""


@function_tool(
    name_override="explain_github_code",
    description_override=(
        "Explain what a preloaded file does — its structure, patterns, imports, and purpose. "
        "Optionally specify file_path to explain a specific file."
    ),
)
async def explain_github_code(
    context: RunContextWrapper[CopilotChatContext],
    file_path: Optional[str] = None,
) -> str:
    """Pure analyzer — reads from ctx.repo_context. No GitHub API calls."""
    ctx = context.context.state

    if not ctx.repo_context and not ctx.github_file_content:
        return (
            "❌ No repository loaded. Please provide a GitHub URL in your message."
        )

    resolved_path, code = _resolve_file(ctx, file_path)
    if not code:
        return "❌ Could not resolve a file to explain."

    await context.context.stream(ProgressUpdateEvent(text=f"Analyzing {resolved_path}..."))

    imports = re.findall(r"^(?:from\s+(\S+)\s+)?import\s+(.+)$", code, re.MULTILINE)
    functions = re.findall(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\):", code, re.MULTILINE)
    classes = re.findall(r"^\s*class\s+(\w+)(?:\(([^)]*)\))?:", code, re.MULTILINE)

    patterns = []
    if "@app.route" in code or "@app.get" in code or "@app.post" in code:
        patterns.append("Web API routes")
    if "@celery" in code or "@task" in code:
        patterns.append("Celery tasks")
    if "class Meta:" in code:
        patterns.append("Django/ORM models")
    if "async def" in code:
        patterns.append("Async programming")
    if "pytest" in code or "unittest" in code:
        patterns.append("Test file")
    if "@dataclass" in code:
        patterns.append("Dataclasses")

    language = _get_language(ctx, resolved_path)

    response = f"""## Code Explanation: {resolved_path}

### Overview
- **Language:** {language}
- **Lines:** {len(code.splitlines())}
- **Patterns detected:** {', '.join(patterns) or 'None'}

### Imports ({len(imports)})
"""
    for from_mod, import_names in imports[:10]:
        if from_mod:
            response += f"- From `{from_mod}`: {import_names}\n"
        else:
            response += f"- `{import_names}`\n"
    if len(imports) > 10:
        response += f"- ... and {len(imports) - 10} more\n"

    response += f"\n### Classes ({len(classes)})\n"
    for class_name, parent in classes[:5]:
        parent_str = f" (extends `{parent}`)" if parent else ""
        response += f"- `{class_name}`{parent_str}\n"

    response += f"\n### Functions ({len(functions)})\n"
    for func_name, params in functions[:10]:
        params_clean = params.replace("\n", "").strip()
        if len(params_clean) > 60:
            params_clean = params_clean[:60] + "..."
        response += f"- `{func_name}({params_clean})`\n"
    if len(functions) > 10:
        response += f"- ... and {len(functions) - 10} more\n"

    response += "\n### Purpose\n"
    if "fastapi" in code.lower() or "@app.get" in code or "@app.post" in code:
        response += "This is a **FastAPI application** defining API endpoints.\n"
    elif "flask" in code.lower() or "@app.route" in code:
        response += "This is a **Flask application** with route handlers.\n"
    elif "celery" in code.lower() or "@task" in code:
        response += "This defines **Celery background tasks** for async processing.\n"
    elif "test" in (resolved_path or "").lower() or "pytest" in code:
        response += "This is a **test file** containing unit/integration tests.\n"
    elif classes and not functions:
        response += "This defines **data models or classes**.\n"
    elif functions and not classes:
        response += "This is a **utility module** with helper functions.\n"
    else:
        response += f"This is a general **{language} module**.\n"

    return response


# ============================================================================
# URL DETECTION TOOL (unchanged — pure parsing, no fetching)
# ============================================================================

@function_tool(
    name_override="detect_github_url",
    description_override="Detect and extract GitHub URLs from a message. Returns parsed URL components.",
)
async def detect_github_url(
    context: RunContextWrapper[CopilotChatContext],
    message: str,
) -> str:
    """Pure URL parser — no network calls."""
    urls = GitHubURLParser.extract_urls(message)

    if not urls:
        return "No GitHub URLs found in the message."

    results = []
    for url in urls:
        parsed = GitHubURLParser.parse(url)
        if parsed:
            url_type = "file" if parsed.is_file else "directory" if parsed.is_directory else "repository"
            results.append(
                f"- **{url_type}**: `{parsed.owner}/{parsed.repo}`"
                + (f" → `{parsed.path}`" if parsed.path else "")
                + f" (branch: `{parsed.branch}`)"
            )

    return (
        "✅ Repository data is preloaded and ready for analysis.\n\n"
        "**Detected URLs:**\n" + "\n".join(results)
    )