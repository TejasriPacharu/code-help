"""
AI Software Engineering Copilot - Agent Definitions

All agents use GitHub tools to analyze REAL code from repositories.
No mock data - everything is fetched from actual GitHub URLs.
"""

from __future__ import annotations as _annotations

from agents import Agent, RunContextWrapper, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from .context import CopilotChatContext
from .guardrails import jailbreak_guardrail, relevance_guardrail
from .tools_github import (
    analyze_github_code,
    scan_github_repo_security,
    get_repo_structure,
    generate_tests_for_github_file,
    explain_github_code,
    detect_github_url,
)


MODEL = "gpt-4.1"


# ============================================================================
# BUG DIAGNOSIS AGENT
# ============================================================================

def bug_diagnosis_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[no project loaded]"
    github_url = ctx.github_url or "[no GitHub URL]"
    current_file = ctx.current_file or "[no file loaded]"

    # Surface repo loading status so LLM knows what's available
    if ctx.repo_context:
        repo = ctx.repo_context
        files_loaded = len(repo.file_contents)
        total_files = repo.total_files
        repo_status = (
            f"✅ Repository loaded: {repo.meta.full_name} "
            f"({files_loaded} files fetched of {total_files} total)"
        )
        available_files = "\n".join(
            f"  - {path}" for path in list(repo.file_contents.keys())[:10]
        )
        if files_loaded > 10:
            available_files += f"\n  - ... and {files_loaded - 10} more"
    else:
        repo_status = "⚠️ No repository loaded. Ask user for a GitHub URL."
        available_files = ""

    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Bug Diagnosis Agent. You analyze real code from GitHub for bugs and performance issues.\n\n"

        f"Current project: {project}\n"
        f"GitHub URL: {github_url}\n"
        f"Current file: {current_file}\n"
        f"Repo status: {repo_status}\n"
        + (f"Available files:\n{available_files}\n" if available_files else "")
        + "\n"
        "## Code Access\n"
        "Repository data is preloaded. Use `analyze_github_code` directly.\n"
        "You can specify a file_path parameter to analyze a specific file from the list above.\n\n"

        "## Your Workflow\n"
        "1. Use `analyze_github_code` to find bugs, performance issues, and code smells\n"
        "2. Explain issues with specific line numbers\n"
        "3. Provide concrete code fixes\n\n"

        "## Handoffs\n"
        "- Security concerns → Security Review Agent\n"
        "- Need tests → Test Generator Agent\n"
        "- Code improvements → Refactoring Agent\n"
        "- Done or topic changes → Triage Agent"
    )

bug_diagnosis_agent = Agent[CopilotChatContext](
    name="Bug Diagnosis Agent",
    model=MODEL,
    handoff_description="Analyzes real GitHub code for bugs, errors, and performance issues.",
    instructions=bug_diagnosis_instructions,
    tools=[analyze_github_code],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# REFACTORING AGENT
# ============================================================================

def refactoring_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[no project loaded]"
    complexity = ctx.complexity_score or "[not analyzed]"
    smells = len(ctx.code_smells) if ctx.code_smells else 0
    
    if ctx.repo_context:
        repo = ctx.repo_context
        files_loaded = len(repo.file_contents)
        total_files = repo.total_files
        repo_status = (
            f"✅ Repository loaded: {repo.meta.full_name} "
            f"({files_loaded} files fetched of {total_files} total)"
        )
        available_files = "\n".join(
            f"  - {path}" for path in list(repo.file_contents.keys())[:10]
        )
        if files_loaded > 10:
            available_files += f"\n  - ... and {files_loaded - 10} more"
    else:
        repo_status = "⚠️ No repository loaded. Ask user for a GitHub URL."
        available_files = ""
    return (
    f"{RECOMMENDED_PROMPT_PREFIX}\n"
    "You are the Refactoring Agent. You improve code quality and suggest design patterns.\n\n"

    f"Current project: {project}\n"
    f"Complexity score: {complexity}\n"
    f"Code smells found: {smells}\n"
    f"Repo status: {repo_status}\n"
    + (f"Available files:\n{available_files}\n" if available_files else "")
    +
    "\n## Code Access\n"
    "Repository data is preloaded. Use `analyze_github_code` directly.\n"
    "You can specify a file_path parameter to target a specific file.\n\n"

    "## Your Workflow\n"
    "1. Use `analyze_github_code` to identify code smells and complexity\n"
    "2. Suggest specific refactoring patterns (Repository, DataLoader, Caching, etc.)\n"
    "3. Provide refactored code examples\n\n"

    "## Handoffs\n"
    "- Need tests after refactoring → Test Generator Agent\n"
    "- Security issues found → Security Review Agent\n"
    "- Need documentation → Documentation Agent\n"
    "- Done → Triage Agent"
)


refactoring_agent = Agent[CopilotChatContext](
    name="Refactoring Agent",
    model=MODEL,
    handoff_description="Analyzes code quality and suggests refactoring improvements.",
    instructions=refactoring_instructions,
    tools=[analyze_github_code],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# TEST GENERATOR AGENT
# ============================================================================

def test_generator_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[no project loaded]"
    framework = ctx.test_framework or "pytest"
    current_file = ctx.current_file or "[no file loaded]"

    if ctx.repo_context:
        repo = ctx.repo_context
        files_loaded = len(repo.file_contents)
        total_files = repo.total_files
        repo_status = (
            f"✅ Repository loaded: {repo.meta.full_name} "
            f"({files_loaded} files fetched of {total_files} total)"
        )
        available_files = "\n".join(
            f"  - {path}" for path in list(repo.file_contents.keys())[:10]
        )
        if files_loaded > 10:
            available_files += f"\n  - ... and {files_loaded - 10} more"
    else:
        repo_status = "⚠️ No repository loaded. Ask user for a GitHub URL."
        available_files = ""

    return (
    f"{RECOMMENDED_PROMPT_PREFIX}\n"
    "You are the Test Generator Agent. You create unit tests for real GitHub code.\n\n"

    f"Current project: {project}\n"
    f"Test framework: {framework}\n"
    f"Current file: {current_file}\n"
    f"Repo status: {repo_status}\n"
    + (f"Available files:\n{available_files}\n" if available_files else "")
    +
    "\n## Code Access\n"
    "Repository data is preloaded. Use `generate_tests_for_github_file` directly.\n"
    "You can specify a file_path parameter to generate tests for a specific file.\n\n"

    "## Your Workflow\n"
    "1. Use `generate_tests_for_github_file` to create test templates\n"
    "2. Explain how to run the tests\n"
    "3. Suggest additional edge cases to test\n\n"

    "## Test Types\n"
    "- Unit tests for individual functions\n"
    "- Integration tests for workflows\n"
    "- Edge case tests (empty input, null, large values)\n\n"

    "## Handoffs\n"
    "- Bugs found → Bug Diagnosis Agent\n"
    "- Security tests needed → Security Review Agent\n"
    "- Done → Triage Agent"
  )


test_generator_agent = Agent[CopilotChatContext](
    name="Test Generator Agent",
    model=MODEL,
    handoff_description="Generates unit tests for real GitHub code.",
    instructions=test_generator_instructions,
    tools=[generate_tests_for_github_file],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# SECURITY REVIEW AGENT
# ============================================================================

def security_review_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[no project loaded]"
    security_score = ctx.security_score or "[not scanned]"
    vulns = len(ctx.vulnerabilities) if ctx.vulnerabilities else 0
    
    if ctx.repo_context:
        repo = ctx.repo_context
        files_loaded = len(repo.file_contents)
        total_files = repo.total_files
        repo_status = (
            f"✅ Repository loaded: {repo.meta.full_name} "
            f"({files_loaded} files fetched of {total_files} total)"
        )
        available_files = "\n".join(
            f"  - {path}" for path in list(repo.file_contents.keys())[:10]
        )
        if files_loaded > 10:
            available_files += f"\n  - ... and {files_loaded - 10} more"
    else:
        repo_status = "⚠️ No repository loaded. Ask user for a GitHub URL."
        available_files = ""

    return (
    f"{RECOMMENDED_PROMPT_PREFIX}\n"
    "You are the Security Review Agent. You scan real GitHub code for vulnerabilities.\n\n"

    f"Current project: {project}\n"
    f"Security score: {security_score}/100\n"
    f"Known vulnerabilities: {vulns}\n"
    f"Repo status: {repo_status}\n"
    + (f"Available files:\n{available_files}\n" if available_files else "")
    +
    "\n## Code Access\n"
    "Repository data is preloaded. No fetching required.\n\n"

    "## Your Workflow\n"
    "1. For a specific file: use `analyze_github_code` with the file_path parameter\n"
    "2. For the entire loaded repository: use `scan_github_repo_security` "
    "(scans all preloaded files automatically)\n"
    "3. Report vulnerabilities with severity levels (CRITICAL, HIGH, MEDIUM, LOW)\n"
    "4. Provide specific remediation steps\n\n"

    "## What You Check For\n"
    "- SQL Injection\n"
    "- Hardcoded secrets/credentials\n"
    "- Command injection (eval, exec, os.system)\n"
    "- Missing input validation\n"
    "- Insecure cryptography\n\n"

    "## Handoffs\n"
    "- Code fixes needed → Refactoring Agent\n"
    "- Need security tests → Test Generator Agent\n"
    "- Done → Triage Agent"
)

security_review_agent = Agent[CopilotChatContext](
    name="Security Review Agent",
    model=MODEL,
    handoff_description="Scans real GitHub code for security vulnerabilities.",
    instructions=security_review_instructions,
    tools=[analyze_github_code, scan_github_repo_security],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# DOCUMENTATION AGENT
# ============================================================================

def documentation_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[no project loaded]"
    current_file = ctx.current_file or "[no file loaded]"
    
    if ctx.repo_context:
        repo = ctx.repo_context
        files_loaded = len(repo.file_contents)
        total_files = repo.total_files
        repo_status = (
            f"✅ Repository loaded: {repo.meta.full_name} "
            f"({files_loaded} files fetched of {total_files} total)"
        )
        available_files = "\n".join(
            f"  - {path}" for path in list(repo.file_contents.keys())[:10]
        )
        if files_loaded > 10:
            available_files += f"\n  - ... and {files_loaded - 10} more"
    else:
        repo_status = "⚠️ No repository loaded. Ask user for a GitHub URL."
        available_files = ""

    return (
    f"{RECOMMENDED_PROMPT_PREFIX}\n"
    "You are the Documentation Agent. You explain and document real GitHub code.\n\n"

    f"Current project: {project}\n"
    f"Current file: {current_file}\n"
    f"Repo status: {repo_status}\n"
    + (f"Available files:\n{available_files}\n" if available_files else "")
    +
    "\n## Code Access\n"
    "Repository data is preloaded. Use `explain_github_code` or `get_repo_structure` directly.\n"
    "You can specify a file_path parameter to explain a specific file.\n\n"

    "## Your Workflow\n"
    "1. Use `explain_github_code` to analyze code structure\n"
    "2. Use `get_repo_structure` to understand the project layout\n"
    "3. Generate clear documentation\n\n"

    "## What You Generate\n"
    "- Code explanations (what does this code do?)\n"
    "- Docstrings for functions and classes\n"
    "- API documentation\n"
    "- README content\n\n"

    "## Handoffs\n"
    "- Need to understand bugs → Bug Diagnosis Agent\n"
    "- Code improvements needed → Refactoring Agent\n"
    "- Done → Triage Agent"
)


documentation_agent = Agent[CopilotChatContext](
    name="Documentation Agent",
    model=MODEL,
    handoff_description="Explains and documents real GitHub code.",
    instructions=documentation_instructions,
    tools=[explain_github_code, get_repo_structure],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# TRIAGE AGENT (Entry Point)
# ============================================================================
def triage_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state

    if ctx.repo_context:
        repo = ctx.repo_context
        repo_status = (
            f"✅ Repository preloaded: {repo.meta.full_name} "
            f"({len(repo.file_contents)} files ready for analysis)"
        )
    else:
        repo_status = "⚠️ No repository loaded yet."

    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Triage Agent for an AI Software Engineering Copilot.\n\n"

        f"Current repo status: {repo_status}\n\n"

        "## Your Job\n"
        "Route users to the right specialist based on their needs:\n\n"

        "• **Bug Diagnosis Agent** → Performance issues, errors, bugs, slow code\n"
        "• **Refactoring Agent** → Code improvements, design patterns, code quality\n"
        "• **Test Generator Agent** → Unit tests, test coverage\n"
        "• **Security Review Agent** → Vulnerabilities, security audit\n"
        "• **Documentation Agent** → Code explanation, docs, README\n\n"

        "## GitHub URL Handling\n"
        "When a user provides a GitHub URL, the repository is loaded automatically "
        "before you receive the message. You do NOT need to fetch anything.\n"
        "1. Use `detect_github_url` to confirm what was detected and show the user\n"
        "2. Immediately hand off to the appropriate specialist\n\n"

        "## Routing Examples\n"
        "- 'Analyze https://github.com/user/repo/blob/main/app.py for bugs' → Bug Diagnosis Agent\n"
        "- 'Check security of https://github.com/user/repo' → Security Review Agent\n"
        "- 'Generate tests for https://github.com/user/repo/file.py' → Test Generator Agent\n"
        "- 'Explain https://github.com/user/repo/blob/main/utils.py' → Documentation Agent\n"
        "- 'Refactor this code' → Refactoring Agent\n\n"

        "## If No GitHub URL\n"
        "Ask the user to provide a GitHub URL. Example:\n"
        "'Please provide a GitHub URL to analyze. "
        "For example: https://github.com/username/repo/blob/main/file.py'"
    )


triage_agent = Agent[CopilotChatContext](
    name="Triage Agent",
    model=MODEL,
    handoff_description="Routes requests to the appropriate specialist agent.",
    instructions=triage_instructions,   # ← now a function, not a string
    tools=[detect_github_url],
    handoffs=[],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)




async def on_testing_handoff(context: RunContextWrapper[CopilotChatContext]) -> None:
    """Prepare context for test generator agent."""
    ctx = context.context.state
    # Set default test framework based on language
    if ctx.test_framework is None:
        if ctx.language == "python":
            ctx.test_framework = "pytest"
        elif ctx.language in ("javascript", "typescript"):
            ctx.test_framework = "jest"
        else:
            ctx.test_framework = "pytest"  # Default



# ============================================================================
# SET UP HANDOFF RELATIONSHIPS
# ============================================================================

triage_agent.handoffs = [
    handoff(agent=bug_diagnosis_agent),
    handoff(agent=refactoring_agent),
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),  # keep — has logic
    handoff(agent=security_review_agent),
    handoff(agent=documentation_agent),
]

bug_diagnosis_agent.handoffs = [
    handoff(agent=refactoring_agent),
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),
    handoff(agent=security_review_agent),
    triage_agent,
]

refactoring_agent.handoffs = [
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),
    handoff(agent=security_review_agent),
    handoff(agent=documentation_agent),
    triage_agent,
]

test_generator_agent.handoffs = [
    handoff(agent=bug_diagnosis_agent),
    handoff(agent=security_review_agent),
    triage_agent,
]

security_review_agent.handoffs = [
    handoff(agent=refactoring_agent),
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),
    triage_agent,
]

documentation_agent.handoffs = [
    handoff(agent=bug_diagnosis_agent),
    handoff(agent=refactoring_agent),
    triage_agent,
]