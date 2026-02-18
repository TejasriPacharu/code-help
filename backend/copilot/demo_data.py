from __future__ import annotations as _annotations

from copy import deepcopy

from .context import CopilotContext


# Mock codebases with various issues for demonstration
MOCK_CODEBASES = {
    "slow_api": {
        "name": "E-Commerce API",
        "project_name": "ecommerce-api",
        "language": "python",
        "framework": "fastapi",
        "repo_path": "/repos/ecommerce-api",
        "description": "FastAPI backend with performance issues",
        "files": {
            "main.py": '''from fastapi import FastAPI
from database import get_products, get_user

app = FastAPI()

@app.get("/products")
def list_products():
    products = get_products()  # N+1 query issue
    for p in products:
        p["reviews"] = get_reviews(p["id"])  # Slow!
    return products

@app.get("/user/{user_id}")
def get_user_profile(user_id: int):
    user = get_user(user_id)
    orders = get_orders(user_id)  # No caching
    return {"user": user, "orders": orders}
''',
            "database.py": '''import time

def get_products():
    time.sleep(0.1)  # Simulated DB call
    return [{"id": i, "name": f"Product {i}"} for i in range(100)]

def get_reviews(product_id: int):
    time.sleep(0.05)  # N+1 problem - called 100 times!
    return [{"rating": 5, "text": "Great!"}]

def get_user(user_id: int):
    time.sleep(0.1)
    return {"id": user_id, "name": "John Doe"}

def get_orders(user_id: int):
    time.sleep(0.2)  # Expensive query, no caching
    return [{"id": 1, "total": 99.99}]
''',
        },
        "error_logs": [
            {
                "timestamp": "2024-12-09T14:32:15Z",
                "level": "WARNING",
                "message": "Slow response detected: GET /products took 5.2s",
                "endpoint": "/products",
                "response_time_ms": 5200,
            },
            {
                "timestamp": "2024-12-09T14:35:22Z",
                "level": "WARNING",
                "message": "Database connection pool exhausted",
                "endpoint": "/products",
                "active_connections": 100,
            },
            {
                "timestamp": "2024-12-09T14:40:01Z",
                "level": "ERROR",
                "message": "Request timeout after 30s",
                "endpoint": "/products",
                "error_type": "TimeoutError",
            },
        ],
        "performance_metrics": {
            "avg_response_time_ms": 4800,
            "p95_response_time_ms": 8500,
            "p99_response_time_ms": 12000,
            "requests_per_second": 15,
            "error_rate": 0.05,
            "db_queries_per_request": 101,  # N+1 problem!
        },
        "vulnerabilities": [
            {
                "id": "SEC-001",
                "severity": "HIGH",
                "type": "No Rate Limiting",
                "description": "API endpoints have no rate limiting, vulnerable to DoS attacks",
                "affected_files": ["main.py"],
                "recommendation": "Implement rate limiting using slowapi or similar",
            },
            {
                "id": "SEC-002",
                "severity": "MEDIUM",
                "type": "Missing Input Validation",
                "description": "user_id parameter not validated, potential injection risk",
                "affected_files": ["main.py"],
                "recommendation": "Add Pydantic validation and sanitization",
            },
        ],
        "suggested_fixes": {
            "performance": [
                "Implement batch loading for reviews using DataLoader pattern",
                "Add Redis caching for user orders with 5-minute TTL",
                "Use database connection pooling with SQLAlchemy",
                "Implement pagination for /products endpoint",
            ],
            "security": [
                "Add rate limiting: 100 requests/minute per IP",
                "Validate user_id as positive integer",
                "Add authentication middleware",
            ],
        },
    },
    "memory_leak": {
        "name": "Data Processing Service",
        "project_name": "data-processor",
        "language": "python",
        "framework": "celery",
        "repo_path": "/repos/data-processor",
        "description": "Celery worker with memory leak issues",
        "files": {
            "tasks.py": '''from celery import Celery
import pandas as pd

app = Celery('tasks')
CACHE = {}  # Memory leak - grows indefinitely!

@app.task
def process_data(file_path: str):
    # Memory leak: data stored but never cleaned
    df = pd.read_csv(file_path)
    result = df.groupby('category').sum()
    CACHE[file_path] = result  # Never cleared!
    return result.to_dict()

@app.task
def aggregate_results():
    # Uses all cached data - memory grows
    all_data = pd.concat(CACHE.values())
    return all_data.sum().to_dict()
''',
            "worker.py": '''from tasks import app

if __name__ == "__main__":
    app.worker_main(["worker", "--loglevel=info"])
''',
        },
        "error_logs": [
            {
                "timestamp": "2024-12-09T10:00:00Z",
                "level": "WARNING",
                "message": "Worker memory usage: 512MB",
                "worker_id": "worker-1",
            },
            {
                "timestamp": "2024-12-09T12:00:00Z",
                "level": "WARNING",
                "message": "Worker memory usage: 2.1GB",
                "worker_id": "worker-1",
            },
            {
                "timestamp": "2024-12-09T14:00:00Z",
                "level": "ERROR",
                "message": "Worker killed: OOMKilled",
                "worker_id": "worker-1",
                "memory_at_death": "4.0GB",
            },
        ],
        "performance_metrics": {
            "memory_growth_rate_mb_per_hour": 500,
            "tasks_processed": 1000,
            "peak_memory_gb": 4.0,
        },
        "vulnerabilities": [
            {
                "id": "SEC-003",
                "severity": "MEDIUM",
                "type": "Arbitrary File Read",
                "description": "file_path parameter allows reading any file on system",
                "affected_files": ["tasks.py"],
                "recommendation": "Validate file paths against whitelist directory",
            },
        ],
        "suggested_fixes": {
            "performance": [
                "Replace global CACHE with Redis or Memcached",
                "Implement LRU cache with max size limit",
                "Add cache expiration/TTL",
                "Use streaming processing for large files",
            ],
            "memory": [
                "Clear CACHE after aggregation",
                "Use weak references for cached data",
                "Implement periodic cache cleanup task",
            ],
        },
    },
    "healthy_api": {
        "name": "User Service",
        "project_name": "user-service",
        "language": "python",
        "framework": "fastapi",
        "repo_path": "/repos/user-service",
        "description": "Well-structured FastAPI service",
        "files": {
            "main.py": '''from fastapi import FastAPI, Depends, HTTPException
from fastapi_limiter import RateLimiter
from pydantic import BaseModel, validator

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

@app.get("/users/{user_id}")
@RateLimiter(times=100, minutes=1)
async def get_user(user_id: int):
    if user_id < 0:
        raise HTTPException(400, "Invalid user ID")
    return {"id": user_id, "name": "John"}
''',
        },
        "error_logs": [],
        "performance_metrics": {
            "avg_response_time_ms": 45,
            "p95_response_time_ms": 120,
            "error_rate": 0.001,
        },
        "vulnerabilities": [],
        "suggested_fixes": {},
    },
}


def apply_codebase_defaults(ctx: CopilotContext, scenario_key: str | None = None) -> None:
    """Populate the context with a demo codebase if missing."""
    target_key = scenario_key or ctx.scenario or "slow_api"
    data = MOCK_CODEBASES.get(target_key) or next(iter(MOCK_CODEBASES.values()))
    
    ctx.scenario = target_key
    ctx.project_name = ctx.project_name or data.get("project_name")
    ctx.repo_path = ctx.repo_path or data.get("repo_path")
    ctx.language = ctx.language or data.get("language")
    ctx.framework = ctx.framework or data.get("framework")
    
    # Set vulnerabilities if present
    if data.get("vulnerabilities") and ctx.vulnerabilities is None:
        ctx.vulnerabilities = deepcopy(data["vulnerabilities"])


def get_codebase_for_project(project_name: str | None) -> tuple[str, dict] | None:
    """Return (scenario_key, codebase) if the project exists in mock data."""
    if not project_name:
        return None
    for key, codebase in MOCK_CODEBASES.items():
        if codebase.get("project_name", "").lower() == project_name.lower():
            return key, codebase
        if key.lower() == project_name.lower():
            return key, codebase
    return None


def active_codebase(ctx: CopilotContext) -> tuple[str, dict]:
    """Resolve the active codebase for the current context."""
    if ctx.scenario and ctx.scenario in MOCK_CODEBASES:
        return ctx.scenario, MOCK_CODEBASES[ctx.scenario]
    
    match = get_codebase_for_project(ctx.project_name)
    if match:
        ctx.scenario = match[0]
        return match
    
    # Default to slow_api scenario
    ctx.scenario = "slow_api"
    return ctx.scenario, MOCK_CODEBASES["slow_api"]


# Test templates for different frameworks
TEST_TEMPLATES = {
    "pytest": {
        "unit": '''import pytest
from {module} import {function}

class Test{class_name}:
    """Unit tests for {function}."""
    
    def test_{function}_success(self):
        """Test successful execution."""
        result = {function}({test_input})
        assert result == {expected_output}
    
    def test_{function}_invalid_input(self):
        """Test with invalid input."""
        with pytest.raises({exception_type}):
            {function}({invalid_input})
    
    def test_{function}_edge_case(self):
        """Test edge cases."""
        result = {function}({edge_case_input})
        assert result is not None
''',
        "load": '''import pytest
from locust import HttpUser, task, between

class LoadTest{class_name}(HttpUser):
    """Load tests for {endpoint}."""
    wait_time = between(1, 3)
    
    @task(3)
    def test_{function}_load(self):
        """Simulate normal load."""
        self.client.get("{endpoint}")
    
    @task(1)
    def test_{function}_burst(self):
        """Simulate burst traffic."""
        for _ in range(10):
            self.client.get("{endpoint}")
''',
    },
    "jest": {
        "unit": '''import {{ {function} }} from './{module}';

describe('{class_name}', () => {{
    it('should handle successful execution', async () => {{
        const result = await {function}({test_input});
        expect(result).toEqual({expected_output});
    }});
    
    it('should throw on invalid input', async () => {{
        await expect({function}({invalid_input}))
            .rejects.toThrow({exception_type});
    }});
    
    it('should handle edge cases', async () => {{
        const result = await {function}({edge_case_input});
        expect(result).toBeDefined();
    }});
}});
''',
    },
}


# Documentation templates
DOC_TEMPLATES = {
    "api": '''# {project_name} API Documentation

## Overview
{description}

## Base URL
```
{base_url}
```

## Endpoints

{endpoints}

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Rate Limiting
{rate_limit_info}
''',
    "readme": '''# {project_name}

{description}

## Installation

```bash
{install_commands}
```

## Quick Start

```{language}
{quickstart_code}
```

## Configuration

{config_info}

## Contributing

{contributing_info}

## License

{license_info}
''',
    "docstring": '''"""{summary}

{description}

Args:
{args}

Returns:
{returns}

Raises:
{raises}

Example:
    >>> {example}
"""
''',
}
