from __future__ import annotations as _annotations

import random
import string

from agents import Agent, RunContextWrapper, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from .context import CopilotChatContext
from .demo_data import apply_codebase_defaults
from .guardrails import jailbreak_guardrail, relevance_guardrail
from .tools import (
    # Triage tools
    detect_project,
    # Bug Diagnosis tools
    analyze_logs,
    trace_error,
    suggest_fix,
    get_performance_metrics,
    # Refactoring tools
    analyze_code_quality,
    suggest_refactoring,
    apply_refactoring,
    # Test Generation tools
    generate_unit_tests,
    generate_load_tests,
    analyze_coverage,
    # Security tools
    scan_vulnerabilities,
    check_rate_limiting,
    audit_dependencies,
    # Documentation tools
    generate_api_docs,
    explain_code,
    generate_docstrings,
)


MODEL = "gpt-4.1"


# ============================================================================
# BUG DIAGNOSIS AGENT
# ============================================================================

def bug_diagnosis_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[unknown]"
    error_type = ctx.error_type or "[not yet diagnosed]"
    endpoint = ctx.affected_endpoint or "[unknown]"
    
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Bug Diagnosis Agent. You analyze errors, performance issues, and help identify root causes.\n\n"
        f"Current project: {project}\n"
        f"Error type: {error_type}\n"
        f"Affected endpoint: {endpoint}\n\n"
        "Your workflow:\n"
        "1. Use analyze_logs to examine error patterns and warnings\n"
        "2. Use get_performance_metrics to understand system behavior\n"
        "3. Use trace_error to identify root causes\n"
        "4. Use suggest_fix to propose solutions\n\n"
        "Work autonomously: chain multiple tool calls to build a complete diagnosis before responding.\n"
        "If the issue involves security concerns, hand off to the Security Review Agent.\n"
        "If the user wants performance tests, hand off to the Test Generator Agent.\n"
        "If code changes are needed, hand off to the Refactoring Agent.\n"
        "When done or if the topic changes, hand off back to the Triage Agent."
    )


bug_diagnosis_agent = Agent[CopilotChatContext](
    name="Bug Diagnosis Agent",
    model=MODEL,
    handoff_description="Analyzes logs, traces errors, and diagnoses performance issues.",
    instructions=bug_diagnosis_instructions,
    tools=[analyze_logs, trace_error, suggest_fix, get_performance_metrics],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# REFACTORING AGENT
# ============================================================================

def refactoring_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[unknown]"
    complexity = ctx.complexity_score or "[not analyzed]"
    smells = len(ctx.code_smells) if ctx.code_smells else 0
    
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Refactoring Agent. You improve code quality, suggest design patterns, and generate cleaner code.\n\n"
        f"Current project: {project}\n"
        f"Complexity score: {complexity}\n"
        f"Code smells found: {smells}\n\n"
        "Your workflow:\n"
        "1. Use analyze_code_quality to identify code smells and complexity issues\n"
        "2. Use suggest_refactoring to propose improvement patterns\n"
        "3. Use apply_refactoring to generate the refactored code\n\n"
        "Work autonomously: analyze the code thoroughly before suggesting changes.\n"
        "After refactoring, if the user wants tests, hand off to the Test Generator Agent.\n"
        "If security issues are found, hand off to the Security Review Agent.\n"
        "When done or if the topic changes, hand off back to the Triage Agent."
    )


refactoring_agent = Agent[CopilotChatContext](
    name="Refactoring Agent",
    model=MODEL,
    handoff_description="Analyzes code quality and suggests refactoring improvements.",
    instructions=refactoring_instructions,
    tools=[analyze_code_quality, suggest_refactoring, apply_refactoring],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# TEST GENERATOR AGENT
# ============================================================================

def test_generator_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[unknown]"
    coverage = ctx.test_coverage or "[not analyzed]"
    framework = ctx.test_framework or "pytest"
    
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Test Generator Agent. You create unit tests, integration tests, and load tests.\n\n"
        f"Current project: {project}\n"
        f"Test coverage: {coverage}%\n"
        f"Test framework: {framework}\n\n"
        "Your workflow:\n"
        "1. Use analyze_coverage to understand current test gaps\n"
        "2. Use generate_unit_tests to create tests for uncovered code\n"
        "3. Use generate_load_tests for performance testing needs\n\n"
        "Work autonomously: generate comprehensive tests that cover edge cases.\n"
        "If bugs are found during testing, hand off to the Bug Diagnosis Agent.\n"
        "If security tests are needed, hand off to the Security Review Agent.\n"
        "When done or if the topic changes, hand off back to the Triage Agent."
    )


test_generator_agent = Agent[CopilotChatContext](
    name="Test Generator Agent",
    model=MODEL,
    handoff_description="Generates unit tests, integration tests, and load/performance tests.",
    instructions=test_generator_instructions,
    tools=[generate_unit_tests, generate_load_tests, analyze_coverage],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# SECURITY REVIEW AGENT
# ============================================================================

def security_review_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[unknown]"
    security_score = ctx.security_score or "[not scanned]"
    vulns = len(ctx.vulnerabilities) if ctx.vulnerabilities else 0
    
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Security Review Agent. You scan for vulnerabilities, check configurations, and audit dependencies.\n\n"
        f"Current project: {project}\n"
        f"Security score: {security_score}/100\n"
        f"Known vulnerabilities: {vulns}\n\n"
        "Your workflow:\n"
        "1. Use scan_vulnerabilities for OWASP-style security checks\n"
        "2. Use check_rate_limiting to verify API protection\n"
        "3. Use audit_dependencies to find vulnerable packages\n\n"
        "Work autonomously: perform a comprehensive security review.\n"
        "If code fixes are needed, hand off to the Refactoring Agent.\n"
        "If testing is needed to verify fixes, hand off to the Test Generator Agent.\n"
        "When done or if the topic changes, hand off back to the Triage Agent."
    )


security_review_agent = Agent[CopilotChatContext](
    name="Security Review Agent",
    model=MODEL,
    handoff_description="Scans for security vulnerabilities, checks rate limiting, and audits dependencies.",
    instructions=security_review_instructions,
    tools=[scan_vulnerabilities, check_rate_limiting, audit_dependencies],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# DOCUMENTATION AGENT
# ============================================================================

def documentation_instructions(
    run_context: RunContextWrapper[CopilotChatContext], agent: Agent[CopilotChatContext]
) -> str:
    ctx = run_context.context.state
    project = ctx.project_name or "[unknown]"
    doc_type = ctx.documentation_type or "[none generated]"
    
    return (
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Documentation Agent. You generate API docs, explain code, and create docstrings.\n\n"
        f"Current project: {project}\n"
        f"Last doc type generated: {doc_type}\n\n"
        "Your workflow:\n"
        "1. Use explain_code to provide code walkthroughs\n"
        "2. Use generate_api_docs for API documentation\n"
        "3. Use generate_docstrings for inline documentation\n\n"
        "Work autonomously: create comprehensive, clear documentation.\n"
        "If you need to understand bugs first, hand off to the Bug Diagnosis Agent.\n"
        "If code improvements are needed, hand off to the Refactoring Agent.\n"
        "When done or if the topic changes, hand off back to the Triage Agent."
    )


documentation_agent = Agent[CopilotChatContext](
    name="Documentation Agent",
    model=MODEL,
    handoff_description="Generates API documentation, explains code, and creates docstrings.",
    instructions=documentation_instructions,
    tools=[generate_api_docs, explain_code, generate_docstrings],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# TRIAGE AGENT (Entry Point)
# ============================================================================

triage_agent = Agent[CopilotChatContext](
    name="Triage Agent",
    model=MODEL,
    handoff_description="Routes requests to the appropriate specialist agent.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the Triage Agent for an AI Software Engineering Copilot. "
        "Route users to the appropriate specialist:\n\n"
        "• Bug Diagnosis Agent: For errors, performance issues, slow APIs, crashes, logs analysis\n"
        "• Refactoring Agent: For code improvements, design patterns, code quality\n"
        "• Test Generator Agent: For unit tests, load tests, test coverage\n"
        "• Security Review Agent: For vulnerabilities, rate limiting, dependency audits\n"
        "• Documentation Agent: For API docs, code explanations, docstrings\n\n"
        "First, if the user describes a project or issue, use detect_project to understand the context.\n"
        "Then hand off to the most appropriate agent based on the user's needs.\n"
        "If the user says 'my API is slow', that's a performance issue - hand off to Bug Diagnosis.\n"
        "Work efficiently: detect the project, then hand off immediately without asking clarifying questions."
    ),
    tools=[detect_project],
    handoffs=[],  # Will be set below
    input_guardrails=[relevance_guardrail, jailbreak_guardrail],
)


# ============================================================================
# HANDOFF CALLBACKS
# ============================================================================

async def on_diagnosis_handoff(context: RunContextWrapper[CopilotChatContext]) -> None:
    """Ensure context is hydrated when handing off to bug diagnosis agent."""
    apply_codebase_defaults(context.context.state)


async def on_refactoring_handoff(context: RunContextWrapper[CopilotChatContext]) -> None:
    """Prepare context when handing off to refactoring agent."""
    apply_codebase_defaults(context.context.state)


async def on_testing_handoff(context: RunContextWrapper[CopilotChatContext]) -> None:
    """Prepare context when handing off to test generator agent."""
    apply_codebase_defaults(context.context.state)
    if context.context.state.test_framework is None:
        # Default to pytest for Python projects
        if context.context.state.language == "python":
            context.context.state.test_framework = "pytest"
        else:
            context.context.state.test_framework = "jest"


async def on_security_handoff(context: RunContextWrapper[CopilotChatContext]) -> None:
    """Prepare context when handing off to security agent."""
    apply_codebase_defaults(context.context.state)


async def on_documentation_handoff(context: RunContextWrapper[CopilotChatContext]) -> None:
    """Prepare context when handing off to documentation agent."""
    apply_codebase_defaults(context.context.state)


# ============================================================================
# SET UP HANDOFF RELATIONSHIPS
# ============================================================================

# Triage can hand off to all specialists
triage_agent.handoffs = [
    handoff(agent=bug_diagnosis_agent, on_handoff=on_diagnosis_handoff),
    handoff(agent=refactoring_agent, on_handoff=on_refactoring_handoff),
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),
    handoff(agent=security_review_agent, on_handoff=on_security_handoff),
    handoff(agent=documentation_agent, on_handoff=on_documentation_handoff),
]

# Bug Diagnosis can hand off to related agents
bug_diagnosis_agent.handoffs = [
    handoff(agent=refactoring_agent, on_handoff=on_refactoring_handoff),
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),
    handoff(agent=security_review_agent, on_handoff=on_security_handoff),
    triage_agent,
]

# Refactoring can hand off to related agents
refactoring_agent.handoffs = [
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),
    handoff(agent=security_review_agent, on_handoff=on_security_handoff),
    handoff(agent=documentation_agent, on_handoff=on_documentation_handoff),
    triage_agent,
]

# Test Generator can hand off to related agents
test_generator_agent.handoffs = [
    handoff(agent=bug_diagnosis_agent, on_handoff=on_diagnosis_handoff),
    handoff(agent=security_review_agent, on_handoff=on_security_handoff),
    triage_agent,
]

# Security Review can hand off to related agents
security_review_agent.handoffs = [
    handoff(agent=refactoring_agent, on_handoff=on_refactoring_handoff),
    handoff(agent=test_generator_agent, on_handoff=on_testing_handoff),
    triage_agent,
]

# Documentation can hand off to related agents
documentation_agent.handoffs = [
    handoff(agent=bug_diagnosis_agent, on_handoff=on_diagnosis_handoff),
    handoff(agent=refactoring_agent, on_handoff=on_refactoring_handoff),
    triage_agent,
]
