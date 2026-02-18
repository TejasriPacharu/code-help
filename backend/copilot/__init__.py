"""AI Software Engineering Copilot - Multi-agent system for code analysis and improvement."""

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
from .tools import (
    analyze_code_quality,
    analyze_coverage,
    analyze_logs,
    apply_refactoring,
    audit_dependencies,
    check_rate_limiting,
    detect_project,
    explain_code,
    generate_api_docs,
    generate_docstrings,
    generate_load_tests,
    generate_unit_tests,
    get_performance_metrics,
    scan_vulnerabilities,
    suggest_fix,
    suggest_refactoring,
    trace_error,
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
    # Tools
    "analyze_code_quality",
    "analyze_coverage",
    "analyze_logs",
    "apply_refactoring",
    "audit_dependencies",
    "check_rate_limiting",
    "detect_project",
    "explain_code",
    "generate_api_docs",
    "generate_docstrings",
    "generate_load_tests",
    "generate_unit_tests",
    "get_performance_metrics",
    "scan_vulnerabilities",
    "suggest_fix",
    "suggest_refactoring",
    "trace_error",
]
