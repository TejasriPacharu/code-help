from __future__ import annotations as _annotations

import random
import string
from copy import deepcopy
from typing import Optional

from agents import RunContextWrapper, function_tool
from chatkit.types import ProgressUpdateEvent

from .context import CopilotChatContext
from .demo_data import (
    active_codebase,
    apply_codebase_defaults,
    get_codebase_for_project,
    MOCK_CODEBASES,
    TEST_TEMPLATES,
    DOC_TEMPLATES,
)


# ============================================================================
# TRIAGE / PROJECT DETECTION TOOLS
# ============================================================================

@function_tool(
    name_override="detect_project",
    description_override="Detect the project type and issues from user description and hydrate context.",
)
async def detect_project(
    context: RunContextWrapper[CopilotChatContext], message: str
) -> str:
    """
    Detect project type from user message and hydrate context with appropriate demo data.
    """
    text = message.lower()
    
    # Detect scenario based on keywords
    if any(k in text for k in ["slow", "performance", "api", "timeout", "latency"]):
        scenario_key = "slow_api"
    elif any(k in text for k in ["memory", "leak", "oom", "crash", "celery"]):
        scenario_key = "memory_leak"
    else:
        scenario_key = "slow_api"  # Default to slow API scenario
    
    apply_codebase_defaults(context.context.state, scenario_key=scenario_key)
    ctx = context.context.state
    codebase = MOCK_CODEBASES.get(scenario_key, {})
    
    return (
        f"Detected project: {ctx.project_name} ({ctx.language}/{ctx.framework}). "
        f"Description: {codebase.get('description', 'N/A')}. "
        f"Path: {ctx.repo_path}"
    )


# ============================================================================
# BUG DIAGNOSIS TOOLS
# ============================================================================

@function_tool(
    name_override="analyze_logs",
    description_override="Analyze error logs to identify issues and patterns.",
)
async def analyze_logs(
    context: RunContextWrapper[CopilotChatContext],
    log_level: str = "all",
) -> str:
    """Analyze error logs from the current project."""
    await context.context.stream(ProgressUpdateEvent(text="Analyzing logs..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    logs = codebase.get("error_logs", [])
    
    if not logs:
        return "No error logs found. The application appears to be running healthy."
    
    # Filter by log level if specified
    if log_level.lower() != "all":
        logs = [l for l in logs if l.get("level", "").lower() == log_level.lower()]
    
    # Analyze patterns
    error_count = sum(1 for l in logs if l.get("level") == "ERROR")
    warning_count = sum(1 for l in logs if l.get("level") == "WARNING")
    
    # Find affected endpoints
    endpoints = set(l.get("endpoint") for l in logs if l.get("endpoint"))
    
    log_summary = "\n".join([
        f"[{l.get('timestamp')}] {l.get('level')}: {l.get('message')}"
        for l in logs[:5]  # Show last 5 logs
    ])
    
    await context.context.stream(ProgressUpdateEvent(text=f"Found {len(logs)} log entries"))
    
    return (
        f"Log Analysis for {ctx_state.project_name}:\n"
        f"- Total entries: {len(logs)}\n"
        f"- Errors: {error_count}, Warnings: {warning_count}\n"
        f"- Affected endpoints: {', '.join(endpoints) if endpoints else 'N/A'}\n\n"
        f"Recent logs:\n{log_summary}"
    )


@function_tool(
    name_override="trace_error",
    description_override="Trace the root cause of an error through the codebase.",
)
async def trace_error(
    context: RunContextWrapper[CopilotChatContext],
    error_type: Optional[str] = None,
) -> str:
    """Trace the root cause of errors in the codebase."""
    await context.context.stream(ProgressUpdateEvent(text="Tracing error root cause..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    logs = codebase.get("error_logs", [])
    metrics = codebase.get("performance_metrics", {})
    files = codebase.get("files", {})
    
    # Store error type in context
    if error_type:
        ctx_state.error_type = error_type
    
    # Build diagnosis based on scenario
    if scenario_key == "slow_api":
        ctx_state.error_type = "performance"
        ctx_state.affected_endpoint = "/products"
        diagnosis = (
            "Root Cause Analysis:\n"
            "1. N+1 Query Problem detected in main.py:list_products()\n"
            f"   - {metrics.get('db_queries_per_request', 'N/A')} DB queries per request\n"
            "   - Each product triggers a separate get_reviews() call\n\n"
            "2. Missing caching in database.py:get_orders()\n"
            "   - Same user orders fetched repeatedly\n"
            "   - No TTL or invalidation strategy\n\n"
            "3. Connection pool exhaustion\n"
            f"   - Response time: {metrics.get('avg_response_time_ms')}ms avg\n"
            f"   - P99: {metrics.get('p99_response_time_ms')}ms\n"
        )
    elif scenario_key == "memory_leak":
        ctx_state.error_type = "memory"
        diagnosis = (
            "Root Cause Analysis:\n"
            "1. Unbounded cache growth in tasks.py\n"
            "   - Global CACHE dictionary never cleared\n"
            f"   - Memory growth: {metrics.get('memory_growth_rate_mb_per_hour', 'N/A')}MB/hour\n\n"
            "2. No cache eviction policy\n"
            "   - Data accumulates indefinitely\n"
            f"   - Peak memory before OOM: {metrics.get('peak_memory_gb', 'N/A')}GB\n"
        )
    else:
        diagnosis = "No significant issues detected in the codebase."
    
    ctx_state.diagnosis_report = diagnosis
    await context.context.stream(ProgressUpdateEvent(text="Root cause identified"))
    
    return diagnosis


@function_tool(
    name_override="suggest_fix",
    description_override="Suggest code fixes for identified issues.",
)
async def suggest_fix(
    context: RunContextWrapper[CopilotChatContext],
    issue_type: Optional[str] = None,
) -> str:
    """Suggest fixes for identified issues."""
    await context.context.stream(ProgressUpdateEvent(text="Generating fix suggestions..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    fixes = codebase.get("suggested_fixes", {})
    fix_type = issue_type or ctx_state.error_type or "performance"
    
    suggestions = fixes.get(fix_type, fixes.get("performance", []))
    
    if not suggestions:
        return "No specific fixes needed - code appears healthy."
    
    fix_list = "\n".join([f"• {fix}" for fix in suggestions])
    
    # Generate code example for the primary fix
    code_example = ""
    if scenario_key == "slow_api" and fix_type == "performance":
        code_example = '''
## Recommended Fix - Batch Loading:

```python
from functools import lru_cache
from typing import List, Dict

# Option 1: Batch load reviews
async def get_products_with_reviews():
    products = get_products()
    product_ids = [p["id"] for p in products]
    
    # Single query for all reviews
    all_reviews = await batch_get_reviews(product_ids)
    
    for p in products:
        p["reviews"] = all_reviews.get(p["id"], [])
    
    return products

# Option 2: Add caching
@lru_cache(maxsize=1000)
def get_orders_cached(user_id: int):
    return get_orders(user_id)
```
'''
    elif scenario_key == "memory_leak":
        code_example = '''
## Recommended Fix - LRU Cache:

```python
from functools import lru_cache
from cachetools import TTLCache

# Replace global dict with bounded cache
CACHE = TTLCache(maxsize=100, ttl=3600)  # Max 100 items, 1hr TTL

@app.task
def process_data(file_path: str):
    df = pd.read_csv(file_path)
    result = df.groupby('category').sum()
    
    # Bounded cache with automatic eviction
    CACHE[file_path] = result
    return result.to_dict()
```
'''
    
    await context.context.stream(ProgressUpdateEvent(text=f"Generated {len(suggestions)} suggestions"))
    
    return f"Suggested Fixes for {fix_type}:\n{fix_list}\n{code_example}"


@function_tool(
    name_override="get_performance_metrics",
    description_override="Get performance metrics for the current project.",
)
async def get_performance_metrics(
    context: RunContextWrapper[CopilotChatContext],
) -> str:
    """Retrieve performance metrics for analysis."""
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    metrics = codebase.get("performance_metrics", {})
    
    if not metrics:
        return "No performance metrics available."
    
    lines = [f"Performance Metrics for {ctx_state.project_name}:"]
    for key, value in metrics.items():
        readable_key = key.replace("_", " ").title()
        lines.append(f"• {readable_key}: {value}")
    
    return "\n".join(lines)


# ============================================================================
# REFACTORING TOOLS
# ============================================================================

@function_tool(
    name_override="analyze_code_quality",
    description_override="Analyze code quality and detect code smells.",
)
async def analyze_code_quality(
    context: RunContextWrapper[CopilotChatContext],
    file_path: Optional[str] = None,
) -> str:
    """Analyze code quality and identify code smells."""
    await context.context.stream(ProgressUpdateEvent(text="Analyzing code quality..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    files = codebase.get("files", {})
    
    # Detect code smells based on scenario
    code_smells = []
    complexity_score = 0.0
    
    if scenario_key == "slow_api":
        code_smells = [
            "N+1 Query Pattern: Nested database calls in loop (main.py:7-8)",
            "Missing Abstraction: Direct database calls in route handlers",
            "No Error Handling: Database calls lack try/except blocks",
            "Hardcoded Sleep: Simulated delays should use proper async patterns",
            "No Type Hints: Function parameters lack type annotations",
        ]
        complexity_score = 6.5
    elif scenario_key == "memory_leak":
        code_smells = [
            "Global Mutable State: CACHE dictionary grows unbounded",
            "Memory Leak: No cache eviction or cleanup strategy",
            "Missing Resource Management: No context managers for file handling",
            "Tight Coupling: Tasks directly manipulate shared state",
        ]
        complexity_score = 5.8
    else:
        code_smells = ["No significant code smells detected"]
        complexity_score = 3.2
    
    ctx_state.code_smells = code_smells
    ctx_state.complexity_score = complexity_score
    
    smell_list = "\n".join([f"• {smell}" for smell in code_smells])
    
    await context.context.stream(ProgressUpdateEvent(text=f"Found {len(code_smells)} code smells"))
    
    return (
        f"Code Quality Analysis for {ctx_state.project_name}:\n\n"
        f"Complexity Score: {complexity_score}/10 (lower is better)\n\n"
        f"Code Smells Detected:\n{smell_list}"
    )


@function_tool(
    name_override="suggest_refactoring",
    description_override="Suggest refactoring improvements for the codebase.",
)
async def suggest_refactoring(
    context: RunContextWrapper[CopilotChatContext],
    focus_area: Optional[str] = None,
) -> str:
    """Suggest refactoring improvements."""
    await context.context.stream(ProgressUpdateEvent(text="Generating refactoring suggestions..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    suggestions = []
    
    if scenario_key == "slow_api":
        suggestions = [
            {
                "pattern": "Repository Pattern",
                "description": "Extract database logic into a repository class",
                "benefit": "Improves testability and separation of concerns",
                "effort": "Medium",
            },
            {
                "pattern": "DataLoader Pattern",
                "description": "Batch database queries to eliminate N+1",
                "benefit": "Reduces DB queries from 101 to 2 per request",
                "effort": "Low",
            },
            {
                "pattern": "Caching Layer",
                "description": "Add Redis caching for frequently accessed data",
                "benefit": "Reduces response time by ~80%",
                "effort": "Medium",
            },
            {
                "pattern": "Async/Await",
                "description": "Convert synchronous DB calls to async",
                "benefit": "Better concurrent request handling",
                "effort": "High",
            },
        ]
    elif scenario_key == "memory_leak":
        suggestions = [
            {
                "pattern": "Dependency Injection",
                "description": "Inject cache instance rather than using global",
                "benefit": "Easier testing and cache management",
                "effort": "Medium",
            },
            {
                "pattern": "Resource Pool",
                "description": "Use bounded resource pool with eviction",
                "benefit": "Prevents memory exhaustion",
                "effort": "Low",
            },
            {
                "pattern": "Stream Processing",
                "description": "Process large files in chunks",
                "benefit": "Constant memory usage regardless of file size",
                "effort": "Medium",
            },
        ]
    
    if not suggestions:
        return "No refactoring suggestions - code structure is clean."
    
    ctx_state.refactoring_suggestions = suggestions
    
    output_lines = [f"Refactoring Suggestions for {ctx_state.project_name}:\n"]
    for i, s in enumerate(suggestions, 1):
        output_lines.append(
            f"{i}. {s['pattern']}\n"
            f"   Description: {s['description']}\n"
            f"   Benefit: {s['benefit']}\n"
            f"   Effort: {s['effort']}\n"
        )
    
    await context.context.stream(ProgressUpdateEvent(text=f"Generated {len(suggestions)} suggestions"))
    
    return "\n".join(output_lines)


@function_tool(
    name_override="apply_refactoring",
    description_override="Generate refactored code for a specific pattern.",
)
async def apply_refactoring(
    context: RunContextWrapper[CopilotChatContext],
    pattern: str,
) -> str:
    """Generate refactored code for the specified pattern."""
    await context.context.stream(ProgressUpdateEvent(text=f"Applying {pattern} pattern..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    pattern_lower = pattern.lower()
    
    if "repository" in pattern_lower:
        code = '''# repository.py - Repository Pattern Implementation

from typing import List, Dict, Optional
from abc import ABC, abstractmethod

class ProductRepository(ABC):
    @abstractmethod
    async def get_all(self) -> List[Dict]:
        pass
    
    @abstractmethod
    async def get_with_reviews(self) -> List[Dict]:
        pass

class SQLProductRepository(ProductRepository):
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_all(self) -> List[Dict]:
        return await self.db.fetch_all("SELECT * FROM products")
    
    async def get_with_reviews(self) -> List[Dict]:
        # Single query with JOIN - eliminates N+1
        query = """
            SELECT p.*, r.rating, r.text as review_text
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
        """
        rows = await self.db.fetch_all(query)
        return self._group_reviews(rows)

# main.py - Updated route
@app.get("/products")
async def list_products(repo: ProductRepository = Depends(get_repository)):
    return await repo.get_with_reviews()  # Single DB call!
'''
    elif "dataloader" in pattern_lower or "batch" in pattern_lower:
        code = '''# dataloader.py - DataLoader Pattern Implementation

from typing import List, Dict
from collections import defaultdict

class ReviewDataLoader:
    def __init__(self):
        self._cache: Dict[int, List] = {}
        self._batch: List[int] = []
    
    async def load(self, product_id: int) -> List[Dict]:
        if product_id in self._cache:
            return self._cache[product_id]
        
        self._batch.append(product_id)
        await self._dispatch()
        return self._cache.get(product_id, [])
    
    async def _dispatch(self):
        if not self._batch:
            return
        
        # Single batch query for all product IDs
        ids = tuple(self._batch)
        query = f"SELECT * FROM reviews WHERE product_id IN {ids}"
        rows = await db.fetch_all(query)
        
        # Group by product_id
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["product_id"]].append(row)
        
        self._cache.update(grouped)
        self._batch.clear()

# Usage in route
@app.get("/products")
async def list_products():
    loader = ReviewDataLoader()
    products = await get_products()
    
    # All reviews loaded in single batch
    for p in products:
        p["reviews"] = await loader.load(p["id"])
    
    return products  # 2 queries instead of 101!
'''
    elif "cach" in pattern_lower:
        code = '''# cache.py - Redis Caching Layer

import redis
import json
from functools import wraps
from typing import Optional

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cached(ttl_seconds: int = 300, prefix: str = ""):
    """Decorator for caching function results in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            key = f"{prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache
            cached_result = redis_client.get(key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute and cache
            result = await func(*args, **kwargs)
            redis_client.setex(key, ttl_seconds, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage
@cached(ttl_seconds=300, prefix="orders")
async def get_orders(user_id: int):
    return await db.fetch_all(
        "SELECT * FROM orders WHERE user_id = ?", user_id
    )
'''
    else:
        code = f"No code template available for pattern: {pattern}"
    
    await context.context.stream(ProgressUpdateEvent(text=f"Generated {pattern} implementation"))
    
    return f"Refactored Code - {pattern}:\n\n```python\n{code}\n```"


# ============================================================================
# TEST GENERATION TOOLS
# ============================================================================

@function_tool(
    name_override="generate_unit_tests",
    description_override="Generate unit tests for the specified function or module.",
)
async def generate_unit_tests(
    context: RunContextWrapper[CopilotChatContext],
    function_name: Optional[str] = None,
    module_name: Optional[str] = None,
) -> str:
    """Generate unit tests for specified function or module."""
    await context.context.stream(ProgressUpdateEvent(text="Generating unit tests..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    # Determine test framework based on language
    language = ctx_state.language or "python"
    test_framework = "pytest" if language == "python" else "jest"
    ctx_state.test_framework = test_framework
    
    # Generate tests based on scenario
    if scenario_key == "slow_api":
        tests = '''import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestListProducts:
    """Unit tests for the /products endpoint."""
    
    @patch('main.get_products')
    @patch('main.get_reviews')
    def test_list_products_success(self, mock_reviews, mock_products):
        """Test successful product listing."""
        mock_products.return_value = [
            {"id": 1, "name": "Product 1"},
            {"id": 2, "name": "Product 2"},
        ]
        mock_reviews.return_value = [{"rating": 5, "text": "Great!"}]
        
        response = client.get("/products")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["reviews"] is not None
    
    @patch('main.get_products')
    def test_list_products_empty(self, mock_products):
        """Test empty product list."""
        mock_products.return_value = []
        
        response = client.get("/products")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('main.get_products')
    def test_list_products_db_error(self, mock_products):
        """Test database error handling."""
        mock_products.side_effect = Exception("DB connection failed")
        
        with pytest.raises(Exception):
            client.get("/products")


class TestGetUserProfile:
    """Unit tests for the /user/{user_id} endpoint."""
    
    @patch('main.get_user')
    @patch('main.get_orders')
    def test_get_user_success(self, mock_orders, mock_user):
        """Test successful user profile retrieval."""
        mock_user.return_value = {"id": 1, "name": "John Doe"}
        mock_orders.return_value = [{"id": 1, "total": 99.99}]
        
        response = client.get("/user/1")
        
        assert response.status_code == 200
        assert response.json()["user"]["name"] == "John Doe"
        assert len(response.json()["orders"]) == 1
    
    def test_get_user_invalid_id(self):
        """Test with invalid user ID."""
        response = client.get("/user/-1")
        
        # Should handle gracefully (current code doesn't validate)
        assert response.status_code in [200, 400, 404]
    
    def test_get_user_not_found(self):
        """Test user not found scenario."""
        with patch('main.get_user', return_value=None):
            response = client.get("/user/99999")
            # Document expected behavior
            assert response.status_code in [200, 404]
'''
    elif scenario_key == "memory_leak":
        tests = '''import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from tasks import process_data, aggregate_results, CACHE


class TestProcessData:
    """Unit tests for the process_data task."""
    
    def setup_method(self):
        """Clear cache before each test."""
        CACHE.clear()
    
    @patch('pandas.read_csv')
    def test_process_data_success(self, mock_read_csv):
        """Test successful data processing."""
        mock_df = pd.DataFrame({
            'category': ['A', 'A', 'B'],
            'value': [10, 20, 30]
        })
        mock_read_csv.return_value = mock_df
        
        result = process_data('/path/to/file.csv')
        
        assert 'A' in str(result) or 'B' in str(result)
        assert '/path/to/file.csv' in CACHE
    
    @patch('pandas.read_csv')
    def test_process_data_caches_result(self, mock_read_csv):
        """Test that results are cached."""
        mock_read_csv.return_value = pd.DataFrame({'category': ['A'], 'value': [1]})
        
        process_data('/test.csv')
        
        assert '/test.csv' in CACHE
        assert len(CACHE) == 1
    
    @patch('pandas.read_csv')
    def test_process_data_file_not_found(self, mock_read_csv):
        """Test file not found error."""
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(FileNotFoundError):
            process_data('/nonexistent.csv')


class TestAggregateResults:
    """Unit tests for the aggregate_results task."""
    
    def setup_method(self):
        """Clear cache before each test."""
        CACHE.clear()
    
    def test_aggregate_empty_cache(self):
        """Test aggregation with empty cache."""
        # Should handle empty cache gracefully
        with pytest.raises(Exception):
            aggregate_results()
    
    def test_aggregate_with_data(self):
        """Test aggregation with cached data."""
        CACHE['/file1.csv'] = pd.DataFrame({'value': [10, 20]})
        CACHE['/file2.csv'] = pd.DataFrame({'value': [30, 40]})
        
        result = aggregate_results()
        
        assert result is not None


class TestCacheGrowth:
    """Tests for cache memory behavior."""
    
    def setup_method(self):
        CACHE.clear()
    
    @patch('pandas.read_csv')
    def test_cache_grows_unbounded(self, mock_read_csv):
        """Document that cache grows without limit (the bug)."""
        mock_read_csv.return_value = pd.DataFrame({'category': ['A'], 'value': [1]})
        
        # Process many files
        for i in range(100):
            process_data(f'/file_{i}.csv')
        
        # Cache contains all entries - THIS IS THE BUG
        assert len(CACHE) == 100
        # TODO: Implement cache eviction to fix this
'''
    else:
        tests = "# No specific tests generated - code appears healthy"
    
    ctx_state.generated_tests = [{"type": "unit", "content": tests}]
    
    await context.context.stream(ProgressUpdateEvent(text="Generated unit tests"))
    
    return f"Generated Unit Tests ({test_framework}):\n\n```python\n{tests}\n```"


@function_tool(
    name_override="generate_load_tests",
    description_override="Generate load/performance tests for API endpoints.",
)
async def generate_load_tests(
    context: RunContextWrapper[CopilotChatContext],
    endpoint: Optional[str] = None,
    target_rps: int = 100,
) -> str:
    """Generate load tests for API endpoints."""
    await context.context.stream(ProgressUpdateEvent(text="Generating load tests..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    endpoint = endpoint or ctx_state.affected_endpoint or "/products"
    
    load_tests = f'''# load_test.py - Locust Load Tests
# Run with: locust -f load_test.py --host=http://localhost:8000

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import time


class APILoadTest(HttpUser):
    """Load test for {ctx_state.project_name} API."""
    
    wait_time = between(0.5, 2)  # Wait 0.5-2 seconds between requests
    
    @task(5)
    def test_products_endpoint(self):
        """Test {endpoint} under load - most common operation."""
        with self.client.get("{endpoint}", catch_response=True) as response:
            if response.elapsed.total_seconds() > 2:
                response.failure(f"Too slow: {{response.elapsed.total_seconds()}}s")
            elif response.status_code != 200:
                response.failure(f"Status: {{response.status_code}}")
    
    @task(2)
    def test_user_profile(self):
        """Test /user/{{id}} endpoint."""
        user_id = 1  # Use test user
        self.client.get(f"/user/{{user_id}}")
    
    @task(1)
    def test_burst_traffic(self):
        """Simulate burst traffic pattern."""
        for _ in range(5):
            self.client.get("{endpoint}")
            time.sleep(0.1)


class StressTest(HttpUser):
    """Stress test to find breaking point."""
    
    wait_time = between(0.1, 0.5)  # Aggressive timing
    
    @task
    def hammer_endpoint(self):
        """Continuously hit endpoint to find limits."""
        self.client.get("{endpoint}")


# Custom metrics tracking
@events.request.add_listener
def track_response_time(request_type, name, response_time, response_length, **kwargs):
    """Track response times for analysis."""
    if response_time > 1000:  # > 1 second
        print(f"SLOW REQUEST: {{name}} took {{response_time}}ms")


# Test configuration
# Run normal load: locust -f load_test.py --users 50 --spawn-rate 10
# Run stress test: locust -f load_test.py --users 200 --spawn-rate 50

# Expected thresholds:
# - P95 response time: < 500ms
# - Error rate: < 1%
# - Throughput: > {target_rps} RPS
'''
    
    ctx_state.load_test_config = {
        "endpoint": endpoint,
        "target_rps": str(target_rps),
        "framework": "locust",
    }
    
    await context.context.stream(ProgressUpdateEvent(text="Generated load tests"))
    
    return f"Generated Load Tests (Locust):\n\n```python\n{load_tests}\n```"


@function_tool(
    name_override="analyze_coverage",
    description_override="Analyze test coverage for the codebase.",
)
async def analyze_coverage(
    context: RunContextWrapper[CopilotChatContext],
) -> str:
    """Analyze test coverage for the current project."""
    await context.context.stream(ProgressUpdateEvent(text="Analyzing test coverage..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    # Mock coverage data based on scenario
    if scenario_key in ["slow_api", "memory_leak"]:
        coverage = 23.5
        uncovered = [
            "main.py: lines 7-12 (list_products loop)",
            "main.py: lines 15-18 (get_user_profile)",
            "database.py: lines 4-15 (all functions)",
        ]
    else:
        coverage = 85.0
        uncovered = ["main.py: lines 20-22 (error handling)"]
    
    ctx_state.test_coverage = coverage
    
    uncovered_list = "\n".join([f"  • {line}" for line in uncovered])
    
    await context.context.stream(ProgressUpdateEvent(text=f"Coverage: {coverage}%"))
    
    return (
        f"Test Coverage Analysis for {ctx_state.project_name}:\n\n"
        f"Overall Coverage: {coverage}%\n"
        f"Status: {'⚠️ Below threshold (80%)' if coverage < 80 else '✅ Meets threshold'}\n\n"
        f"Uncovered Code:\n{uncovered_list}\n\n"
        f"Recommendation: Add tests for uncovered functions to improve reliability."
    )


# ============================================================================
# SECURITY REVIEW TOOLS
# ============================================================================

@function_tool(
    name_override="scan_vulnerabilities",
    description_override="Scan the codebase for security vulnerabilities.",
)
async def scan_vulnerabilities(
    context: RunContextWrapper[CopilotChatContext],
) -> str:
    """Scan for security vulnerabilities in the codebase."""
    await context.context.stream(ProgressUpdateEvent(text="Scanning for vulnerabilities..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    vulnerabilities = codebase.get("vulnerabilities", [])
    
    if not vulnerabilities:
        ctx_state.security_score = 95.0
        return "✅ No vulnerabilities detected. Security score: 95/100"
    
    ctx_state.vulnerabilities = vulnerabilities
    
    # Calculate security score
    severity_scores = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 8, "LOW": 3}
    total_deduction = sum(
        severity_scores.get(v.get("severity", "LOW"), 3) 
        for v in vulnerabilities
    )
    security_score = max(0, 100 - total_deduction)
    ctx_state.security_score = security_score
    
    vuln_list = []
    for v in vulnerabilities:
        vuln_list.append(
            f"\n[{v.get('severity')}] {v.get('type')} ({v.get('id')})\n"
            f"  Description: {v.get('description')}\n"
            f"  Affected: {', '.join(v.get('affected_files', []))}\n"
            f"  Fix: {v.get('recommendation')}"
        )
    
    await context.context.stream(
        ProgressUpdateEvent(text=f"Found {len(vulnerabilities)} vulnerabilities")
    )
    
    return (
        f"Security Scan Results for {ctx_state.project_name}:\n"
        f"Security Score: {security_score}/100\n"
        f"{''.join(vuln_list)}"
    )


@function_tool(
    name_override="check_rate_limiting",
    description_override="Check if API endpoints have proper rate limiting.",
)
async def check_rate_limiting(
    context: RunContextWrapper[CopilotChatContext],
) -> str:
    """Check rate limiting configuration for API endpoints."""
    await context.context.stream(ProgressUpdateEvent(text="Checking rate limiting..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    if scenario_key == "slow_api":
        has_rate_limiting = False
        analysis = '''Rate Limiting Analysis:

❌ NO RATE LIMITING DETECTED

Vulnerable Endpoints:
  • GET /products - No limits
  • GET /user/{id} - No limits

Risk Assessment:
  • DoS Attack: HIGH - Unlimited requests allowed
  • Brute Force: HIGH - No protection on user endpoints
  • Resource Exhaustion: HIGH - Database can be overwhelmed

Recommended Configuration:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/products")
@limiter.limit("100/minute")  # 100 requests per minute
async def list_products():
    ...

@app.get("/user/{user_id}")
@limiter.limit("30/minute")   # Stricter for user data
async def get_user_profile(user_id: int):
    ...
```

Additional Recommendations:
  • Add Redis backend for distributed rate limiting
  • Implement per-user limits for authenticated endpoints
  • Add exponential backoff for repeated violations
'''
    elif scenario_key == "healthy_api":
        has_rate_limiting = True
        analysis = '''Rate Limiting Analysis:

✅ RATE LIMITING CONFIGURED

Current Configuration:
  • GET /users/{id}: 100 requests/minute per IP

Assessment:
  • DoS Protection: Good
  • Brute Force Protection: Adequate
  • Resource Management: Configured
'''
    else:
        has_rate_limiting = False
        analysis = "Rate limiting status unknown for this project type."
    
    ctx_state.rate_limit_config = {
        "enabled": str(has_rate_limiting),
        "status": "configured" if has_rate_limiting else "missing",
    }
    
    await context.context.stream(ProgressUpdateEvent(text="Rate limit check complete"))
    
    return analysis


@function_tool(
    name_override="audit_dependencies",
    description_override="Audit project dependencies for known vulnerabilities.",
)
async def audit_dependencies(
    context: RunContextWrapper[CopilotChatContext],
) -> str:
    """Audit dependencies for known vulnerabilities."""
    await context.context.stream(ProgressUpdateEvent(text="Auditing dependencies..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    # Mock dependency audit results
    if scenario_key in ["slow_api", "memory_leak"]:
        audit_results = [
            {
                "package": "requests",
                "version": "2.25.0",
                "severity": "MEDIUM",
                "vulnerability": "CVE-2023-32681",
                "description": "Proxy-Authorization header leak",
                "fixed_in": "2.31.0",
            },
            {
                "package": "urllib3",
                "version": "1.26.5",
                "severity": "LOW",
                "vulnerability": "CVE-2023-43804",
                "description": "Cookie header leak in cross-origin redirects",
                "fixed_in": "2.0.6",
            },
        ]
    else:
        audit_results = []
    
    ctx_state.dependency_audit = audit_results
    
    if not audit_results:
        return "✅ No vulnerable dependencies found. All packages are up to date."
    
    audit_lines = [
        f"Dependency Audit Results for {ctx_state.project_name}:\n"
        f"Found {len(audit_results)} vulnerable packages:\n"
    ]
    
    for dep in audit_results:
        audit_lines.append(
            f"\n[{dep['severity']}] {dep['package']} {dep['version']}\n"
            f"  Vulnerability: {dep['vulnerability']}\n"
            f"  Description: {dep['description']}\n"
            f"  Fix: Upgrade to {dep['fixed_in']}"
        )
    
    audit_lines.append("\n\nRecommendation: Run `pip install --upgrade <package>` for each vulnerable package.")
    
    await context.context.stream(ProgressUpdateEvent(text=f"Found {len(audit_results)} issues"))
    
    return "".join(audit_lines)


# ============================================================================
# DOCUMENTATION TOOLS
# ============================================================================

@function_tool(
    name_override="generate_api_docs",
    description_override="Generate API documentation for the project.",
)
async def generate_api_docs(
    context: RunContextWrapper[CopilotChatContext],
) -> str:
    """Generate API documentation."""
    await context.context.stream(ProgressUpdateEvent(text="Generating API documentation..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    apply_codebase_defaults(ctx_state, scenario_key=scenario_key)
    
    project_name = ctx_state.project_name or "API"
    
    docs = f'''# {project_name} API Documentation

## Overview

{codebase.get("description", "API service")}

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required (TODO: Implement OAuth2).

## Endpoints

### GET /products

Retrieve all products with their reviews.

**Response:**
```json
[
  {{
    "id": 1,
    "name": "Product Name",
    "reviews": [
      {{"rating": 5, "text": "Great product!"}}
    ]
  }}
]
```

**Performance Note:** This endpoint currently has performance issues due to N+1 queries. Expected response time: ~5s for 100 products.

---

### GET /user/{{user_id}}

Retrieve user profile with order history.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| user_id | integer | The user's unique identifier |

**Response:**
```json
{{
  "user": {{"id": 1, "name": "John Doe"}},
  "orders": [{{"id": 1, "total": 99.99}}]
}}
```

---

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

## Rate Limiting

⚠️ **Warning:** No rate limiting currently implemented. See security recommendations.

---

*Documentation generated by AI Software Engineering Copilot*
'''
    
    ctx_state.documentation_type = "api"
    ctx_state.generated_docs = docs
    
    await context.context.stream(ProgressUpdateEvent(text="API documentation generated"))
    
    return f"Generated API Documentation:\n\n{docs}"


@function_tool(
    name_override="explain_code",
    description_override="Explain how a piece of code works.",
)
async def explain_code(
    context: RunContextWrapper[CopilotChatContext],
    file_name: Optional[str] = None,
) -> str:
    """Explain the code in the specified file."""
    await context.context.stream(ProgressUpdateEvent(text="Analyzing code..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    files = codebase.get("files", {})
    target_file = file_name or "main.py"
    
    code = files.get(target_file, "# File not found")
    
    # Generate explanation based on scenario
    if scenario_key == "slow_api" and target_file == "main.py":
        explanation = '''## Code Explanation: main.py

### Overview
This is a FastAPI application that provides two endpoints for an e-commerce API.

### Endpoint 1: GET /products (lines 6-10)

```python
@app.get("/products")
def list_products():
    products = get_products()  # Fetches all products (1 query)
    for p in products:
        p["reviews"] = get_reviews(p["id"])  # N+1 PROBLEM!
    return products
```

**What it does:** Returns all products with their reviews.

**Problem Identified:** This creates an N+1 query problem:
- 1 query to fetch all products
- N queries to fetch reviews (one per product)
- For 100 products = 101 database queries!

**Impact:** Response time scales linearly with product count. With 100 products and 50ms per review query, minimum response time is 5+ seconds.

### Endpoint 2: GET /user/{user_id} (lines 12-15)

```python
@app.get("/user/{user_id}")
def get_user_profile(user_id: int):
    user = get_user(user_id)
    orders = get_orders(user_id)  # No caching
    return {"user": user, "orders": orders}
```

**What it does:** Returns user profile with order history.

**Problem Identified:** 
- No input validation on user_id
- No caching for orders (same data fetched repeatedly)
- No error handling if user doesn't exist

### Recommendations
1. Implement batch loading for reviews
2. Add Redis caching for orders
3. Add input validation for user_id
4. Add proper error handling
'''
    elif scenario_key == "memory_leak" and target_file == "tasks.py":
        explanation = '''## Code Explanation: tasks.py

### Overview
Celery task definitions for data processing.

### Global Cache (line 5)

```python
CACHE = {}  # Memory leak - grows indefinitely!
```

**Problem:** This global dictionary is never cleared, causing unbounded memory growth.

### Task: process_data (lines 7-11)

```python
@app.task
def process_data(file_path: str):
    df = pd.read_csv(file_path)
    result = df.groupby('category').sum()
    CACHE[file_path] = result  # Never cleared!
    return result.to_dict()
```

**What it does:** Reads CSV, aggregates data, caches result.

**Problem:** Every processed file is added to CACHE but never removed, causing memory to grow continuously.

### Recommendations
1. Use bounded cache (LRU with max size)
2. Add TTL expiration
3. Use external cache (Redis) instead of in-process dict
'''
    else:
        explanation = f"Code in {target_file}:\n\n```python\n{code}\n```"
    
    await context.context.stream(ProgressUpdateEvent(text="Code explanation complete"))
    
    return explanation


@function_tool(
    name_override="generate_docstrings",
    description_override="Generate docstrings for functions in the codebase.",
)
async def generate_docstrings(
    context: RunContextWrapper[CopilotChatContext],
    function_name: Optional[str] = None,
) -> str:
    """Generate docstrings for code functions."""
    await context.context.stream(ProgressUpdateEvent(text="Generating docstrings..."))
    
    ctx_state = context.context.state
    scenario_key, codebase = active_codebase(ctx_state)
    
    if scenario_key == "slow_api":
        docstrings = '''## Generated Docstrings

### list_products()
```python
def list_products() -> List[Dict[str, Any]]:
    """Retrieve all products with their associated reviews.
    
    Fetches the complete product catalog and enriches each product
    with its review data. 
    
    Warning:
        Current implementation has O(n) database queries where n is
        the number of products. Consider using batch loading for
        production use.
    
    Returns:
        List[Dict[str, Any]]: List of product dictionaries, each containing:
            - id (int): Product identifier
            - name (str): Product name
            - reviews (List[Dict]): Associated reviews
    
    Raises:
        DatabaseError: If database connection fails
    
    Example:
        >>> products = list_products()
        >>> print(products[0]["name"])
        "Product 1"
    """
```

### get_user_profile()
```python
def get_user_profile(user_id: int) -> Dict[str, Any]:
    """Retrieve user profile with complete order history.
    
    Fetches user details and all associated orders for the given user ID.
    
    Args:
        user_id: Unique identifier for the user. Must be positive integer.
    
    Returns:
        Dict containing:
            - user (Dict): User details including id and name
            - orders (List[Dict]): List of order objects with id and total
    
    Raises:
        ValueError: If user_id is negative
        UserNotFoundError: If no user exists with given ID
    
    Example:
        >>> profile = get_user_profile(1)
        >>> print(profile["user"]["name"])
        "John Doe"
    """
```

### get_products()
```python
def get_products() -> List[Dict[str, Any]]:
    """Fetch all products from the database.
    
    Simulates database query with artificial delay for demo purposes.
    
    Returns:
        List[Dict[str, Any]]: List of product dictionaries with id and name.
    
    Note:
        Current implementation includes 100ms simulated delay.
    """
```
'''
    else:
        docstrings = "# Docstrings generated for healthy codebase - no issues found."
    
    ctx_state.documentation_type = "docstring"
    
    await context.context.stream(ProgressUpdateEvent(text="Docstrings generated"))
    
    return docstrings
