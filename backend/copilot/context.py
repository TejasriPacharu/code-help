from __future__ import annotations as _annotations

from chatkit.agents import AgentContext
from pydantic import BaseModel


class CopilotContext(BaseModel):
    """Context for AI Software Engineering Copilot agents."""
    
    # Project information
    project_name: str | None = None
    repo_path: str | None = None
    current_file: str | None = None
    language: str | None = None  # python, javascript, typescript, etc.
    framework: str | None = None  # flask, fastapi, react, etc.
    
    # Bug diagnosis context
    error_message: str | None = None
    stack_trace: str | None = None
    error_type: str | None = None  # performance, runtime, logic, etc.
    affected_endpoint: str | None = None
    diagnosis_report: str | None = None
    
    # Refactoring context
    code_smells: list[str] | None = None
    refactoring_suggestions: list[dict[str, str]] | None = None
    complexity_score: float | None = None
    
    # Testing context
    test_coverage: float | None = None
    test_framework: str | None = None  # pytest, jest, unittest, etc.
    generated_tests: list[dict[str, str]] | None = None
    load_test_config: dict[str, str] | None = None
    
    # Security context
    vulnerabilities: list[dict[str, str]] | None = None
    security_score: float | None = None
    rate_limit_config: dict[str, str] | None = None
    dependency_audit: list[dict[str, str]] | None = None
    
    # Documentation context
    documentation_type: str | None = None  # api, readme, docstring, etc.
    generated_docs: str | None = None
    
    # Internal tracking
    scenario: str | None = None  # demo scenario being used
    analysis_history: list[dict[str, str]] | None = None


class CopilotChatContext(AgentContext[dict]):
    """
    AgentContext wrapper used during ChatKit runs.
    Holds the persisted CopilotContext in `state`.
    """
    state: CopilotContext


def create_initial_context() -> CopilotContext:
    """
    Factory for a new CopilotContext.
    Starts empty; values are populated during the conversation.
    """
    return CopilotContext()


def public_context(ctx: CopilotContext) -> dict:
    """
    Return a filtered view of the context for UI display.
    Hides internal fields and only shows relevant information.
    """
    data = ctx.model_dump()
    
    # Hide internal tracking fields
    hidden_keys = {
        "scenario",
        "analysis_history",
    }
    
    for key in list(data.keys()):
        if key in hidden_keys:
            data.pop(key, None)
        # Remove None values for cleaner display
        elif data[key] is None:
            data.pop(key, None)
    
    return data
