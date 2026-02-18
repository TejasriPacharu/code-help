"""
Preprocessing pipeline: runs BEFORE agents start.
Extracts GitHub URLs from user input, builds RepoContext once,
injects it into CopilotContext.

This is the ingestion layer. Agents are the reasoning layer.
They never overlap.
"""

from __future__ import annotations

import re
from typing import Optional

from .context import CopilotContext
from .github_service import (
    GitHubURLParser,
    GitHubError,
    RepoContext,
    build_repo_context,
)


def extract_github_url(text: str) -> Optional[str]:
    """Extract the first GitHub URL from user input text."""
    pattern = r"https?://(?:www\.)?github\.com/[^\s)>\]\"']+"
    match = re.search(pattern, text)
    return match.group(0) if match else None


async def preprocess_user_input(
    user_text: str,
    ctx: CopilotContext,
) -> CopilotContext:
    """
    Examine user input and populate ctx.repo_context if a GitHub URL is found.
    
    Rules:
    - If a URL is found AND it differs from the already-loaded repo, fetch fresh.
    - If the same repo URL is already loaded, skip (use cache).
    - If no URL found, leave ctx unchanged.
    
    Returns the (mutated) context.
    """
    url = extract_github_url(user_text)
    if not url:
        return ctx

    # Check if we already have this repo loaded — avoid redundant fetches
    if ctx.repo_context and ctx.github_url:
        parsed_existing = GitHubURLParser.parse(ctx.github_url)
        parsed_new = GitHubURLParser.parse(url)
        if (
            parsed_existing
            and parsed_new
            and parsed_existing.owner == parsed_new.owner
            and parsed_existing.repo == parsed_new.repo
        ):
            # Same repo — just update the target file if it changed
            if parsed_new.is_file and parsed_new.path != ctx.repo_context.fetched_file_path:
                ctx.repo_context.fetched_file_path = parsed_new.path
                # Populate legacy field for backward compat
                ctx.github_file_content = ctx.repo_context.file_contents.get(parsed_new.path)
                ctx.current_file = parsed_new.path
            return ctx

    # New URL — fetch repo context
    try:
        repo_context: RepoContext = await build_repo_context(url)
    except GitHubError:
        # Don't crash the request — agents will handle gracefully
        return ctx

    # Inject into context
    ctx.repo_context = repo_context
    ctx.github_url = url
    ctx.github_owner = repo_context.meta.owner
    ctx.github_repo = repo_context.meta.name
    ctx.github_branch = repo_context.meta.default_branch
    ctx.project_name = repo_context.meta.full_name
    ctx.repo_path = f"github.com/{repo_context.meta.full_name}"
    ctx.language = repo_context.primary_language or None
    ctx.framework = repo_context.framework or None

    # Backward compat: populate legacy fields
    if repo_context.fetched_file_path:
        ctx.current_file = repo_context.fetched_file_path
        ctx.github_file_content = repo_context.file_contents.get(
            repo_context.fetched_file_path
        )

    return ctx