# Code-help 

A multi-agent AI system for software engineering assistance, built on top of the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/).

It is composed of two parts:

1. Backend - Python

2. Frontend - Next.js , Tailwin CSS

## Agents Included

| Agent | Description | Tools |
|-------|-------------|-------|
| **Triage Agent** | Entry point that routes requests to specialists | `detect_project` |
| **Bug Diagnosis Agent** | Analyzes logs, traces errors, diagnoses performance issues | `analyze_logs`, `trace_error`, `suggest_fix`, `get_performance_metrics` |
| **Refactoring Agent** | Improves code quality, suggests design patterns | `analyze_code_quality`, `suggest_refactoring`, `apply_refactoring` |
| **Test Generator Agent** | Creates unit tests, integration tests, and load tests | `generate_unit_tests`, `generate_load_tests`, `analyze_coverage` |
| **Security Review Agent** | Scans for vulnerabilities, checks rate limiting | `scan_vulnerabilities`, `check_rate_limiting`, `audit_dependencies` |
| **Documentation Agent** | Generates API docs, explains code, creates docstrings | `generate_api_docs`, `explain_code`, `generate_docstrings` |

## How to Use

### Prerequisites

- **Python 3.10+** - For the backend
- **Node.js 18+** - For the frontend
- **OpenAI API Key** - Get one from [OpenAI Platform](https://platform.openai.com/api-keys)



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
