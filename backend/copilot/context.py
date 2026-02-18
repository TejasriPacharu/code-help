from __future__ import annotations as _annotations

from chatkit.agents import AgentContext
from pydantic import BaseModel
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .github_service import RepoContext


class CopilotContext(BaseModel):
    """
    Runtime context for AI Software Engineering Copilot agents.
    
    Lifecycle:
      1. preprocessing.py populates repo_context before agents run
      2. Agents read from repo_context via tools — they never mutate it
      3. Analysis results (complexity_score, vulnerabilities, etc.) are
         written by tools after analysis completes
    """

    # ── Ingestion layer (set by preprocessing.py, read-only for agents) ──
    repo_context: Optional["RepoContext"] = None
    github_url: str | None = None
    github_owner: str | None = None
    github_repo: str | None = None
    github_branch: str | None = None

    # ── Derived metadata (populated from repo_context by preprocessing) ──
    project_name: str | None = None
    repo_path: str | None = None
    current_file: str | None = None
    language: str | None = None
    framework: str | None = None

    # ── Bug diagnosis results ──
    error_message: str | None = None
    stack_trace: str | None = None
    error_type: str | None = None
    affected_endpoint: str | None = None
    diagnosis_report: str | None = None

    # ── Refactoring results ──
    code_smells: list[str] | None = None
    refactoring_suggestions: list[dict[str, str]] | None = None
    complexity_score: float | None = None

    # ── Testing results ──
    test_coverage: float | None = None
    test_framework: str | None = None
    generated_tests: list[dict[str, str]] | None = None
    load_test_config: dict[str, str] | None = None

    # ── Security results ──
    vulnerabilities: list[dict[str, str]] | None = None
    security_score: float | None = None
    rate_limit_config: dict[str, str] | None = None
    dependency_audit: list[dict[str, str]] | None = None

    # ── Documentation results ──
    documentation_type: str | None = None
    generated_docs: str | None = None

    class Config:
        arbitrary_types_allowed = True


class CopilotChatContext(AgentContext[dict]):
    """AgentContext wrapper used during ChatKit runs."""
    state: CopilotContext


def create_initial_context() -> CopilotContext:
    return CopilotContext()


def public_context(ctx: CopilotContext) -> dict:
    """
    Filtered context view for UI display.
    Excludes large objects and None values.
    Exposes a lightweight repo summary instead of the full RepoContext.
    """
    data = ctx.model_dump()

    # Never expose these to the UI
    data.pop("repo_context", None)

    # Remove None values for clean display
    data = {k: v for k, v in data.items() if v is not None}

    # Inject lightweight repo summary
    if ctx.repo_context:
        repo = ctx.repo_context
        data["repo_loaded"] = {
            "full_name": repo.meta.full_name,
            "language": repo.primary_language,
            "framework": repo.framework,
            "files_fetched": len(repo.file_contents),
            "total_files": repo.total_files,
            "entry_points": repo.entry_points,
        }

    return data