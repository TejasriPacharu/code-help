# AI Software Engineering Copilot

![NextJS](https://img.shields.io/badge/Built_with-NextJS-blue)
![Tailwind CSS](https://img.shields.io/badge/Styled_with-Tailwind_CSS-06B6D4)
![OpenAI API](https://img.shields.io/badge/Powered_by-OpenAI_API-orange)

A multi-agent AI system for software engineering assistance, built on top of the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/).

It is composed of two parts:

1. A Python backend that handles the agent orchestration logic, implementing a multi-agent system for code analysis, debugging, testing, security review, and documentation.

2. A Next.js UI allowing the visualization of the agent orchestration process and providing a chat interface. It uses [ChatKit](https://openai.github.io/chatkit-js/) to provide a high-quality chat interface.

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

### Quick Start (5 minutes)

#### Step 1: Clone and Setup

```bash
# Clone the repository (or extract the zip)
cd ai-copilot

# Set your OpenAI API key
export OPENAI_API_KEY=sk-your-api-key-here
```

#### Step 2: Start the Backend

```bash
# Navigate to backend folder
cd python-backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

#### Step 3: Start the Frontend (New Terminal)

```bash
# Navigate to UI folder
cd ui

# Install dependencies
npm install

# Start the development server
npm run dev:frontend
```

You should see:
```
▲ Next.js 14.1.0
- Local:        http://localhost:3000
```

#### Step 4: Open the App

Open your browser and navigate to **http://localhost:3000**

---

### Alternative: Run Both Together

If you want to run both frontend and backend with a single command:

```bash
cd ui
npm install
npm run dev
```

This uses `concurrently` to start both servers simultaneously.

---

### Setting your OpenAI API key

You can set your OpenAI API key in your environment variables by running the following command in your terminal:

```bash
export OPENAI_API_KEY=your_api_key
```

You can also follow [these instructions](https://platform.openai.com/docs/libraries#create-and-export-an-api-key) to set your OpenAI key at a global level.

Alternatively, you can set the `OPENAI_API_KEY` environment variable in an `.env` file at the root of the `python-backend` folder:

```bash
# .env
OPENAI_API_KEY=your_api_key
```

### Install Dependencies

Install the dependencies for the backend by running the following commands:

```bash
cd python-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the UI, you can run:

```bash
cd ui
npm install
```

### Run the App

You can either run the backend independently if you want to use a separate UI, or run both the UI and backend at the same time.

#### Run the backend independently

From the `python-backend` folder, run:

```bash
python -m uvicorn main:app --reload --port 8000
```

The backend will be available at: [http://localhost:8000](http://localhost:8000)

#### Run the UI & backend simultaneously

From the `ui` folder, run:

```bash
npm run dev
```

The frontend will be available at: [http://localhost:3000](http://localhost:3000)

This command will also start the backend.

## Demo Flows

### Demo Flow #1: Slow API Performance Issue

1. **Start with a performance complaint:**
   
   - User: "My API is slow."
   - The Triage Agent detects this is a performance issue and routes to the Bug Diagnosis Agent.

2. **Performance Analysis:**
   
   - Bug Diagnosis Agent analyzes logs and finds slow response times
   - Traces the error to identify N+1 query problem
   - Bug Diagnosis Agent: "Found N+1 query issue in /products endpoint - 101 database queries per request!"

3. **Get Fix Suggestions:**
   
   - Bug Diagnosis Agent suggests fixes: batch loading, caching, connection pooling
   - Provides code examples for implementing the DataLoader pattern

4. **Security Check:**
   
   - User: "Are there any security issues?"
   - Routes to Security Review Agent
   - Security Agent: "Found 2 vulnerabilities: No rate limiting (HIGH) and missing input validation (MEDIUM)"

5. **Generate Tests:**
   
   - User: "Generate load tests for the /products endpoint"
   - Routes to Test Generator Agent
   - Generates Locust load tests with configurable RPS targets

### Demo Flow #2: Code Quality Review

1. **Start with a refactoring request:**
   
   - User: "I want to improve my code quality"
   - Routes to Refactoring Agent

2. **Code Analysis:**
   
   - Refactoring Agent analyzes code quality
   - Identifies code smells: N+1 queries, missing abstractions, no error handling
   - Reports complexity score: 6.5/10

3. **Get Refactoring Suggestions:**
   
   - Suggests patterns: Repository Pattern, DataLoader Pattern, Caching Layer
   - Provides effort estimates and benefits for each

4. **Apply Refactoring:**
   
   - User: "Apply the repository pattern"
   - Generates complete refactored code with the Repository pattern

5. **Generate Documentation:**
   
   - User: "Now document this code"
   - Routes to Documentation Agent
   - Generates API docs, docstrings, and code explanations

### Demo Flow #3: Security Audit

1. **Request Security Review:**
   
   - User: "Audit my application for security issues"
   - Routes to Security Review Agent

2. **Vulnerability Scan:**
   
   - Scans for OWASP-style vulnerabilities
   - Security Agent: "Security Score: 77/100. Found: No Rate Limiting (HIGH), Missing Input Validation (MEDIUM)"

3. **Check Rate Limiting:**
   
   - Analyzes API endpoints for DoS protection
   - Provides recommended rate limiting configuration with code examples

4. **Dependency Audit:**
   
   - Scans dependencies for known CVEs
   - Reports vulnerable packages with fix versions

5. **Trigger Guardrails:**
   
   - User: "Write me a poem about cats"
   - Relevance Guardrail trips: "Sorry, I can only answer questions related to software engineering."

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                    (Next.js + ChatKit)                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│                      (main.py)                                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CopilotServer                                  │
│              (Agent Orchestration)                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Triage Agent                          │    │
│  │              (Routes to Specialists)                     │    │
│  └──────────┬──────────┬──────────┬──────────┬─────────────┘    │
│             │          │          │          │                   │
│             ▼          ▼          ▼          ▼                   │
│  ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Bug Diagnosis│ │Refactor- │ │ Test     │ │ Security     │   │
│  │    Agent     │ │ing Agent │ │Generator │ │ Review Agent │   │
│  └──────────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│             │          │          │          │                   │
│             └──────────┴──────────┴──────────┘                   │
│                              │                                   │
│                              ▼                                   │
│                   ┌──────────────────┐                          │
│                   │ Documentation    │                          │
│                   │     Agent        │                          │
│                   └──────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## Customization

This app is designed for demonstration purposes. Feel free to update the agent prompts, guardrails, and tools to fit your own software engineering workflows or experiment with new use cases!

### Adding New Tools

1. Add your tool function in `copilot/tools.py`:

```python
@function_tool(
    name_override="my_new_tool",
    description_override="Description of what the tool does.",
)
async def my_new_tool(
    context: RunContextWrapper[CopilotChatContext],
    param: str,
) -> str:
    """Tool implementation."""
    # Your logic here
    return "Result"
```

2. Add the tool to the appropriate agent in `copilot/agents.py`.

### Adding New Agents

1. Define the agent instructions function
2. Create the agent with tools and guardrails
3. Set up handoff relationships with other agents

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chatkit` | POST | Main chat endpoint - processes messages |
| `/chatkit/state` | GET | Returns current state for a thread |
| `/chatkit/bootstrap` | GET | Creates new thread and returns initial state |
| `/chatkit/state/stream` | GET | SSE endpoint for real-time updates |
| `/health` | GET | Health check |
| `/` | GET | Service information |

## Contributing

You are welcome to open issues or submit PRs to improve this app. However, please note that we may not review all suggestions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
