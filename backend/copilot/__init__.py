"""
AI Software Engineering Copilot

Multi-agent system for analyzing real code from GitHub repositories.
Provides bug diagnosis, security scanning, test generation, and documentation.
"""

from .agents import (
    bug_diagnosis_agent,
    documentation_agent,
    refactoring_agent,
    security_review_agent,
    test_generator_agent,
    triage_agent,
)
from .context import (
    CopilotChatContext,
    CopilotContext,
    create_initial_context,
    public_context,
)
from .guardrails import jailbreak_guardrail, relevance_guardrail
from .tools_github import (
    analyze_github_code,
    scan_github_repo_security,
    get_repo_structure,
    generate_tests_for_github_file,
    explain_github_code,
    detect_github_url,
)
from .github_service import (
    GitHubClient,
    GitHubURLParser,
    GitHubError,
    RepoAnalyzer,
    fetch_github_file,
    analyze_github_repo,
)

__all__ = [
    # Agents
    "bug_diagnosis_agent",
    "documentation_agent",
    "refactoring_agent",
    "security_review_agent",
    "test_generator_agent",
    "triage_agent",
    # Context
    "CopilotChatContext",
    "CopilotContext",
    "create_initial_context",
    "public_context",
    # Guardrails
    "jailbreak_guardrail",
    "relevance_guardrail",
    # GitHub Tools
    "fetch_github_url",
    "analyze_github_code",
    "scan_github_repo_security",
    "get_repo_structure",
    "generate_tests_for_github_file",
    "explain_github_code",
    "detect_github_url",
    # GitHub Service
    "GitHubClient",
    "GitHubURLParser",
    "GitHubError",
    "RepoAnalyzer",
    "fetch_github_file",
    "analyze_github_repo",
]