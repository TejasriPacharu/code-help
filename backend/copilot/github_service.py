"""
GitHub Service for fetching public repository data.

This module handles all GitHub API interactions for public repositories.
No authentication required for public repos (rate limited to 60 req/hour).
"""

from __future__ import annotations

import re
import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse
import httpx

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class GitHubFile:
    """Represents a file in a GitHub repository."""
    path: str
    name: str
    type: str  # "file" or "dir"
    size: int = 0
    sha: str = ""
    download_url: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None

@dataclass
class GitHubRepo:
    """Represents a GitHub repository."""
    owner: str
    name: str
    full_name: str
    description: str = ""
    language: str = ""
    default_branch: str = "main"
    stars: int = 0
    forks: int = 0
    topics: List[str] = field(default_factory=list)
    

@dataclass
class RepoStructure:
    """Represents the analyzed structure of a repository."""
    repo: GitHubRepo
    files: List[GitHubFile] = field(default_factory=list)
    tree: Dict[str, Any] = field(default_factory=dict)
    languages: Dict[str, int] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    framework: str = ""
    entry_points: List[str] = field(default_factory=list)
    total_files: int = 0
    total_dirs: int = 0


@dataclass
class ParsedGitHubURL:
    """Parsed components of a GitHub URL."""
    owner: str
    repo: str
    branch: str = "main"
    path: str = ""
    is_file: bool = False
    is_directory: bool = False
    is_repo_root: bool = False
    raw_url: str = ""
    original_url: str = ""

# ============================================================================
# URL PARSER
# ============================================================================

class GitHubURLParser:
    """Parse GitHub URLs into components."""
    
    # Pattern for GitHub URLs
    GITHUB_PATTERNS = [
        # https://github.com/owner/repo/blob/branch/path/to/file.py
        r"github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)",
        # https://github.com/owner/repo/tree/branch/path/to/dir
        r"github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)",
        # https://github.com/owner/repo/tree/branch (root with branch)
        r"github\.com/([^/]+)/([^/]+)/tree/([^/]+)/?$",
        # https://github.com/owner/repo (root)
        r"github\.com/([^/]+)/([^/]+)/?$",
        # Raw URLs: https://raw.githubusercontent.com/owner/repo/branch/path
        r"raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)",
    ]
    
    @classmethod
    def parse(cls, url: str) -> Optional[ParsedGitHubURL]:
        """Parse a GitHub URL and extract components."""
        url = url.strip()
        
        # Remove protocol if present
        clean_url = re.sub(r"^https?://", "", url)
        
        for i, pattern in enumerate(cls.GITHUB_PATTERNS):
            match = re.match(pattern, clean_url)
            if match:
                groups = match.groups()
                
                if i == 0:  # blob (file)
                    return ParsedGitHubURL(
                        owner=groups[0],
                        repo=groups[1],
                        branch=groups[2],
                        path=groups[3],
                        is_file=True,
                        original_url=url,
                        raw_url=f"https://raw.githubusercontent.com/{groups[0]}/{groups[1]}/{groups[2]}/{groups[3]}"
                    )
                elif i == 1:  # tree with path (directory)
                    return ParsedGitHubURL(
                        owner=groups[0],
                        repo=groups[1],
                        branch=groups[2],
                        path=groups[3],
                        is_directory=True,
                        original_url=url,
                    )
                elif i == 2:  # tree without path (root with branch)
                    return ParsedGitHubURL(
                        owner=groups[0],
                        repo=groups[1],
                        branch=groups[2],
                        path="",
                        is_repo_root=True,
                        original_url=url,
                    )
                elif i == 3:  # repo root
                    return ParsedGitHubURL(
                        owner=groups[0],
                        repo=groups[1],
                        branch="main",  # Will be updated from API
                        path="",
                        is_repo_root=True,
                        original_url=url,
                    )
                elif i == 4:  # raw URL
                    return ParsedGitHubURL(
                        owner=groups[0],
                        repo=groups[1],
                        branch=groups[2],
                        path=groups[3],
                        is_file=True,
                        original_url=url,
                        raw_url=url,
                    )
        
        return None
    
    @classmethod
    def is_github_url(cls, text: str) -> bool:
        """Check if text contains a GitHub URL."""
        return bool(re.search(r"github\.com/[^/]+/[^/]+", text))
    
    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """Extract all GitHub URLs from text."""
        pattern = r"https?://(?:www\.)?github\.com/[^\s)>\]\"']+"
        return re.findall(pattern, text)


# ============================================================================
# GITHUB API CLIENT
# ============================================================================

class GitHubClient:
    """Client for interacting with GitHub API."""
    
    BASE_URL = "https://api.github.com"
    RAW_URL = "https://raw.githubusercontent.com"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize client with optional auth token."""
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Copilot/1.0",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    async def _request(self, url: str) -> Dict[str, Any]:
        """Make an async HTTP request to GitHub API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 404:
                raise GitHubError(f"Not found: {url}")
            elif response.status_code == 403:
                raise GitHubError("Rate limit exceeded. Try again later or use a GitHub token.")
            elif response.status_code != 200:
                raise GitHubError(f"GitHub API error: {response.status_code}")
            
            return response.json()
    
    async def _fetch_raw(self, url: str) -> str:
        """Fetch raw file content."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers={"User-Agent": "AI-Copilot/1.0"})
            
            if response.status_code == 404:
                raise GitHubError(f"File not found: {url}")
            elif response.status_code != 200:
                raise GitHubError(f"Failed to fetch file: {response.status_code}")
            
            return response.text
    
    async def get_repo(self, owner: str, repo: str) -> GitHubRepo:
        """Get repository information."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        data = await self._request(url)
        
        return GitHubRepo(
            owner=owner,
            name=repo,
            full_name=data.get("full_name", f"{owner}/{repo}"),
            description=data.get("description") or "",
            language=data.get("language") or "",
            default_branch=data.get("default_branch", "main"),
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            topics=data.get("topics", []),
        )
    
    async def get_contents(
        self, 
        owner: str, 
        repo: str, 
        path: str = "",
        branch: str = "main"
    ) -> List[GitHubFile]:
        """Get contents of a directory or file."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        if branch:
            url += f"?ref={branch}"
        
        data = await self._request(url)
        
        # If it's a single file, wrap in list
        if isinstance(data, dict):
            data = [data]
        
        files = []
        for item in data:
            files.append(GitHubFile(
                path=item.get("path", ""),
                name=item.get("name", ""),
                type=item.get("type", "file"),
                size=item.get("size", 0),
                sha=item.get("sha", ""),
                download_url=item.get("download_url"),
            ))
        
        return files
    
    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: str = "main"
    ) -> str:
        """Get the content of a specific file."""
        raw_url = f"{self.RAW_URL}/{owner}/{repo}/{branch}/{path}"
        return await self._fetch_raw(raw_url)
    
    async def get_tree(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        recursive: bool = True
    ) -> List[GitHubFile]:
        """Get the entire file tree of a repository."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}"
        if recursive:
            url += "?recursive=1"
        
        data = await self._request(url)
        
        files = []
        for item in data.get("tree", []):
            files.append(GitHubFile(
                path=item.get("path", ""),
                name=item.get("path", "").split("/")[-1],
                type="file" if item.get("type") == "blob" else "dir",
                size=item.get("size", 0),
                sha=item.get("sha", ""),
            ))
        
        return files
    
    async def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get language breakdown for a repository."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/languages"
        return await self._request(url)


class GitHubError(Exception):
    """Custom exception for GitHub API errors."""
    pass


# ============================================================================
# REPOSITORY ANALYZER
# ============================================================================

class RepoAnalyzer:
    """Analyze repository structure and detect patterns."""
    
    # File patterns for detection
    FRAMEWORK_PATTERNS = {
        "fastapi": ["main.py", "app.py", "requirements.txt"],
        "flask": ["app.py", "wsgi.py", "requirements.txt"],
        "django": ["manage.py", "settings.py", "urls.py"],
        "express": ["index.js", "app.js", "package.json"],
        "nextjs": ["next.config.js", "pages/", "app/"],
        "react": ["src/App.js", "src/App.tsx", "package.json"],
        "spring": ["pom.xml", "src/main/java/"],
        "rails": ["Gemfile", "config/routes.rb"],
    }
    
    DEPENDENCY_FILES = {
        "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
        "javascript": ["package.json", "yarn.lock", "package-lock.json"],
        "java": ["pom.xml", "build.gradle"],
        "ruby": ["Gemfile"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod", "go.sum"],
    }
    
    ENTRY_POINTS = {
        "python": ["main.py", "app.py", "__main__.py", "run.py", "manage.py"],
        "javascript": ["index.js", "main.js", "app.js", "server.js"],
        "typescript": ["index.ts", "main.ts", "app.ts", "server.ts"],
    }
    
    CODE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".swift": "swift",
        ".kt": "kotlin",
    }
    
    def __init__(self, client: GitHubClient):
        self.client = client
    
    async def analyze(self, parsed_url: ParsedGitHubURL) -> RepoStructure:
        """Analyze a repository and return its structure."""
        # Get repo info
        repo = await self.client.get_repo(parsed_url.owner, parsed_url.repo)
        
        # Update branch from repo info
        branch = parsed_url.branch or repo.default_branch
        
        # Get file tree
        files = await self.client.get_tree(
            parsed_url.owner, 
            parsed_url.repo, 
            branch
        )
        
        # Get languages
        languages = await self.client.get_languages(
            parsed_url.owner, 
            parsed_url.repo
        )
        
        # Build tree structure
        tree = self._build_tree(files)
        
        # Detect framework
        framework = self._detect_framework(files, repo.language)
        
        # Find entry points
        entry_points = self._find_entry_points(files, repo.language)
        
        # Find dependencies
        dependencies = self._find_dependencies(files)
        
        # Count files and dirs
        total_files = sum(1 for f in files if f.type == "file")
        total_dirs = sum(1 for f in files if f.type == "dir")
        
        return RepoStructure(
            repo=repo,
            files=files,
            tree=tree,
            languages=languages,
            dependencies=dependencies,
            framework=framework,
            entry_points=entry_points,
            total_files=total_files,
            total_dirs=total_dirs,
        )
    
    def _build_tree(self, files: List[GitHubFile]) -> Dict[str, Any]:
        """Build a nested tree structure from flat file list."""
        tree: Dict[str, Any] = {}
        
        for file in files:
            parts = file.path.split("/")
            current = tree
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Leaf node
                    current[part] = {
                        "type": file.type,
                        "size": file.size,
                        "path": file.path,
                    }
                else:  # Directory
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        return tree
    
    def _detect_framework(self, files: List[GitHubFile], primary_language: str) -> str:
        """Detect the framework used in the repository."""
        file_paths = {f.path for f in files}
        file_names = {f.name for f in files}
        
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            matches = sum(1 for p in patterns if p in file_paths or p in file_names)
            if matches >= 2:
                return framework
        
        # Check for common patterns
        if "requirements.txt" in file_names and primary_language == "Python":
            if any("fastapi" in f.path.lower() for f in files):
                return "fastapi"
            if any("flask" in f.path.lower() for f in files):
                return "flask"
        
        return ""
    
    def _find_entry_points(self, files: List[GitHubFile], primary_language: str) -> List[str]:
        """Find likely entry point files."""
        entry_points = []
        file_names = {f.name: f.path for f in files}
        
        # Check for language-specific entry points
        lang_key = primary_language.lower() if primary_language else ""
        if lang_key in self.ENTRY_POINTS:
            for entry in self.ENTRY_POINTS[lang_key]:
                if entry in file_names:
                    entry_points.append(file_names[entry])
        
        # Also check common patterns
        for file in files:
            if file.name in ["main.py", "app.py", "index.js", "main.js", "server.js"]:
                if file.path not in entry_points:
                    entry_points.append(file.path)
        
        return entry_points[:5]  # Return top 5
    
    def _find_dependencies(self, files: List[GitHubFile]) -> List[str]:
        """Find dependency files."""
        deps = []
        file_names = {f.name for f in files}
        
        for lang, dep_files in self.DEPENDENCY_FILES.items():
            for dep_file in dep_files:
                if dep_file in file_names:
                    deps.append(dep_file)
        
        return deps
    
    def get_file_language(self, path: str) -> str:
        """Get the programming language for a file based on extension."""
        for ext, lang in self.CODE_EXTENSIONS.items():
            if path.endswith(ext):
                return lang
        return ""
    
    def find_related_files(
        self, 
        target_path: str, 
        all_files: List[GitHubFile],
        content: str = ""
    ) -> List[str]:
        """Find files related to the target file (imports, same directory, etc.)."""
        related = []
        target_dir = "/".join(target_path.split("/")[:-1])
        target_name = target_path.split("/")[-1].rsplit(".", 1)[0]
        
        # Same directory files
        for f in all_files:
            if f.type == "file" and f.path != target_path:
                file_dir = "/".join(f.path.split("/")[:-1])
                if file_dir == target_dir:
                    related.append(f.path)
        
        # Try to find imports (Python)
        if content and target_path.endswith(".py"):
            import_pattern = r"^(?:from|import)\s+([\w.]+)"
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                module = match.group(1).replace(".", "/")
                for f in all_files:
                    if f.path.startswith(module) or f.path.endswith(f"{module}.py"):
                        if f.path not in related:
                            related.append(f.path)
        
        return related[:10]  # Return top 10


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def fetch_github_file(url: str) -> Tuple[str, ParsedGitHubURL, Optional[RepoStructure]]:
    """
    Convenience function to fetch a file from GitHub.
    Returns (content, parsed_url, repo_structure).
    """
    parsed = GitHubURLParser.parse(url)
    if not parsed:
        raise GitHubError(f"Invalid GitHub URL: {url}")
    
    client = GitHubClient()
    
    # Get repo structure
    analyzer = RepoAnalyzer(client)
    structure = await analyzer.analyze(parsed)
    
    # Get file content if it's a file URL
    content = ""
    if parsed.is_file:
        content = await client.get_file_content(
            parsed.owner,
            parsed.repo,
            parsed.path,
            parsed.branch or structure.repo.default_branch
        )
    
    return content, parsed, structure


async def analyze_github_repo(url: str) -> RepoStructure:
    """Convenience function to analyze a GitHub repository."""
    parsed = GitHubURLParser.parse(url)
    if not parsed:
        raise GitHubError(f"Invalid GitHub URL: {url}")
    
    client = GitHubClient()
    analyzer = RepoAnalyzer(client)
    return await analyzer.analyze(parsed)



# ============================================================================
# REPO CONTEXT (New - replaces file-centric state)
# ============================================================================

from pydantic import BaseModel, Field
from typing import Optional

class RepoMeta(BaseModel):
    owner: str
    name: str
    full_name: str
    description: str = ""
    stars: int = 0
    default_branch: str = "main"
    language: str = ""
    topics: list[str] = Field(default_factory=list)

class RepoContext(BaseModel):
    """
    Fully pre-loaded repository context built ONCE before agents run.
    Agents read from this — they never call GitHub directly.
    """
    meta: RepoMeta
    tree: dict[str, Any] = Field(default_factory=dict)
    files: list[str] = Field(default_factory=list)           # all file paths
    file_contents: dict[str, str] = Field(default_factory=dict)  # path → content
    languages: dict[str, int] = Field(default_factory=dict)
    framework: str = ""
    entry_points: list[str] = Field(default_factory=list)
    dependency_files: list[str] = Field(default_factory=list)
    
    # Derived
    primary_language: str = ""
    total_files: int = 0
    total_dirs: int = 0
    
    # Source tracking
    original_url: str = ""
    fetched_file_path: Optional[str] = None  # Set if URL pointed to a specific file


# ============================================================================
# PREPROCESSING PIPELINE
# ============================================================================

import re as _re

# Files to always fetch (entry points, config, deps)
PRIORITY_FILE_PATTERNS = [
    r"^(main|app|index|server|manage)\.(py|js|ts)$",
    r"^requirements\.txt$",
    r"^package\.json$",
    r"^pyproject\.toml$",
    r"^Dockerfile$",
    r"^\.env\.example$",
]

MAX_FILES_TO_FETCH = 20       # Hard limit on file content fetching
MAX_FILE_SIZE_BYTES = 100_000 # Skip files larger than 100KB


def _is_priority_file(path: str) -> bool:
    name = path.split("/")[-1]
    return any(_re.match(p, name) for p in PRIORITY_FILE_PATTERNS)


def _is_code_file(path: str) -> bool:
    CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb"}
    return any(path.endswith(ext) for ext in CODE_EXTS)


async def build_repo_context(url: str) -> RepoContext:
    """
    Main preprocessing entrypoint. Call this ONCE before agent.run().
    
    Fetches and assembles a complete RepoContext from a GitHub URL.
    Respects file limits to avoid memory bloat on large repos.
    """
    parsed = GitHubURLParser.parse(url)
    if not parsed:
        raise GitHubError(f"Invalid GitHub URL: {url}")

    client = GitHubClient()
    analyzer = RepoAnalyzer(client)

    # --- Fetch repo metadata + tree ---
    structure = await analyzer.analyze(parsed)
    branch = parsed.branch or structure.repo.default_branch

    meta = RepoMeta(
        owner=parsed.owner,
        name=structure.repo.name,
        full_name=structure.repo.full_name,
        description=structure.repo.description,
        stars=structure.repo.stars,
        default_branch=branch,
        language=structure.repo.language,
        topics=structure.repo.topics,
    )

    all_file_paths = [f.path for f in structure.files if f.type == "file"]
    
    # --- Select which files to actually fetch content for ---
    # Strategy: priority files first, then code files, up to MAX_FILES_TO_FETCH
    priority = [p for p in all_file_paths if _is_priority_file(p)]
    code_files = [p for p in all_file_paths if _is_code_file(p) and p not in priority]
    
    # If a specific file was requested, always include it
    specific_file = parsed.path if parsed.is_file else None
    
    to_fetch: list[str] = []
    if specific_file and specific_file not in priority:
        to_fetch.append(specific_file)
    to_fetch.extend(priority)
    to_fetch.extend(code_files)
    
    # Deduplicate and cap
    seen = set()
    capped: list[str] = []
    for p in to_fetch:
        if p not in seen:
            seen.add(p)
            capped.append(p)
        if len(capped) >= MAX_FILES_TO_FETCH:
            break

    # --- Fetch file contents concurrently ---
    file_contents: dict[str, str] = {}

    async def _fetch_one(path: str) -> tuple[str, str]:
        try:
            content = await client.get_file_content(
                parsed.owner, structure.repo.name, path, branch
            )
            if len(content.encode()) <= MAX_FILE_SIZE_BYTES:
                return path, content
        except Exception:
            pass
        return path, ""

    import asyncio
    results = await asyncio.gather(*[_fetch_one(p) for p in capped])
    file_contents = {path: content for path, content in results if content}

    return RepoContext(
        meta=meta,
        tree=structure.tree,
        files=all_file_paths,
        file_contents=file_contents,
        languages=structure.languages,
        framework=structure.framework,
        entry_points=structure.entry_points,
        dependency_files=structure.dependencies,
        primary_language=structure.repo.language.lower() if structure.repo.language else "",
        total_files=structure.total_files,
        total_dirs=structure.total_dirs,
        original_url=url,
        fetched_file_path=specific_file,
    )