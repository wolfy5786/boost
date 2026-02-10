# Testing Agent Architecture

## Overview

A specialized testing agent built with Python + LangGraph that generates tests through a two-phase process:
1. **Spec Generation**: Create structured JSON test specifications
2. **Code Generation**: Convert specs to executable test files

Both phases include feedback loops with MCP-based validation.

---

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TESTING AGENT (LangGraph)                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  PHASE 1: SPEC GENERATION (with feedback loop)                        │   │
│  │                                                                       │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐  │   │
│  │  │ Spec Agent   │────▶│ Schema       │────▶│ MCP Validator       │  │   │
│  │  │ (Model A)    │     │ Selector     │     │ (validate_spec)     │  │   │
│  │  └──────┬───────┘     └──────────────┘     └──────────┬──────────┘  │   │
│  │         │                                             │              │   │
│  │         │ JSON spec                                   │              │   │
│  │         │                                             │              │   │
│  │         │                                    ┌────────▼──────────┐   │   │
│  │         │                                    │ Validation Result │   │   │
│  │         │                                    └────────┬──────────┘   │   │
│  │         │                                             │              │   │
│  │         │                                    ┌────────▼──────────┐   │   │
│  │         └────────────────────────────────────│ Retry/Refine?     │   │   │
│  │                                              └────────┬──────────┘   │   │
│  │                                                       │              │   │
│  │                                              ┌────────▼──────────┐   │   │
│  │                                              │ Valid Spec ✅     │   │   │
│  │                                              └───────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                          │
│                                    ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  PHASE 2: CODE GENERATION (with feedback loop)                        │   │
│  │                                                                       │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐  │   │
│  │  │ Writing      │────▶│ Generate     │────▶│ MCP Validator       │  │   │
│  │  │ Agent        │     │ Test Files   │     │ (validate_code)     │  │   │
│  │  │ (Model B)    │     │              │     └──────────┬──────────┘  │   │
│  │  └──────┬───────┘     └──────────────┘                │              │   │
│  │         │                                              │              │   │
│  │         │ Test files (pytest/jest/etc.)                │              │   │
│  │         │                                              │              │   │
│  │         │                                    ┌────────▼──────────┐   │   │
│  │         │                                    │ Validation Result │   │   │
│  │         │                                    │ (lint, syntax,    │   │   │
│  │         │                                    │  structure)       │   │   │
│  │         │                                    └────────┬──────────┘   │   │
│  │         │                                             │              │   │
│  │         │                                    ┌────────▼──────────┐   │   │
│  │         └────────────────────────────────────│ Retry/Refine?     │   │   │
│  │                                              └────────┬──────────┘   │   │
│  │                                                       │              │   │
│  │                                              ┌────────▼──────────┐   │   │
│  │                                              │ Valid Code ✅     │   │   │
│  │                                              └───────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                          │
│                                    ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  PHASE 3: EXECUTION & ANALYSIS (optional in CI mode)                   │   │
│  │                                                                       │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐  │   │
│  │  │ Test Runner  │────▶│ Results      │────▶│ Analyzer Agent      │  │   │
│  │  │              │     │ Collection   │     │ (Model C)           │  │   │
│  │  └──────────────┘     └──────────────┘     └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLANNING AGENT LAYER                                                       │
│                                                                             │
│  - Orchestrates all testing flows (unit, integration, E2E, performance).    │
│  - Creates a discrete, machine-readable test plan (ordered steps).         │
│  - Executes each step by calling:                                           │
│      - Testing graphs (spec + code + validation pipelines)                  │
│      - Internal MCP tools (context, validation, file operations, CI, etc.)  │
│      - Other agents exposed via MCP, if needed.                             │
│  - Responsible for deciding which test types to run and where to save       │
│    generated spec/code files.                                               │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MCP LAYER                                                                   │
│                                                                              │
│  Exposed Tools (for other agents):                                          │
│  - generate_test_spec(test_type, target, context)                           │
│  - generate_tests_from_spec(spec_path, framework)                           │
│  - validate_test_spec(spec_json, schema_type)                               │
│  - validate_test_code(code_path, framework)                                 │
│  - run_tests(test_path, options)                                            │
│  - analyze_test_results(results_path)                                       │
│                                                                              │
│  Consumed Tools (from other agents):                                        │
│  - get_codebase_context(query, file_paths)                                  │
│  - get_ast_analysis(file_path)                                             │
│  - get_openapi_spec(endpoint)                                               │
│  - lint_code(file_path)                                                     │
│  - check_syntax(file_path, language)                                        │
│  - run_build()                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schema Registry

### Multiple Test Type Schemas

Different schemas for different testing types:

| Test Type | Schema File | Description |
|-----------|-------------|-------------|
| **API Tests** | `api_test_schema_v2.json` | HTTP API endpoint testing (current schema) |
| **Unit Tests** | `unit_test_schema_v1.json` | Function/class unit testing |
| **Integration Tests** | `integration_test_schema_v1.json` | Multi-component integration testing |
| **E2E Tests** | `e2e_test_schema_v1.json` | End-to-end user flow testing |
| **Performance Tests** | `performance_test_schema_v1.json` | Load/stress testing |

### Schema Selection Logic

```python
def select_schema(test_type: str, hints: dict) -> str:
    """
    Select appropriate schema based on test type and context hints.
    
    Args:
        test_type: "api", "unit", "integration", "e2e", "performance"
        hints: Additional context (e.g., {"framework": "pytest", "target": "REST API"})
    
    Returns:
        Path to schema JSON file
    """
    schema_registry = {
        "api": "schemas/api_test_schema_v2.json",
        "unit": "schemas/unit_test_schema_v1.json",
        "integration": "schemas/integration_test_schema_v1.json",
        "e2e": "schemas/e2e_test_schema_v1.json",
        "performance": "schemas/performance_test_schema_v1.json"
    }
    return schema_registry.get(test_type)
```

---

## Feedback Loops

### 1. Spec Generation Feedback Loop

**Flow:**
```
Spec Agent generates JSON
    ↓
Schema Validation (via MCP: validate_test_spec)
    ↓
[Invalid?] → Collect errors → Refine prompt → Retry (max 3 attempts)
    ↓
[Valid?] → Proceed to Code Generation
```

**MCP Tool: `validate_test_spec`**
```json
{
  "name": "validate_test_spec",
  "description": "Validates a test specification JSON against its schema",
  "inputSchema": {
    "type": "object",
    "properties": {
      "spec_json": {"type": "object", "description": "The test spec JSON"},
      "schema_type": {"type": "string", "enum": ["api", "unit", "integration", "e2e", "performance"]},
      "strict": {"type": "boolean", "default": true}
    },
    "required": ["spec_json", "schema_type"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "valid": {"type": "boolean"},
      "errors": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "path": {"type": "string"},
            "message": {"type": "string"},
            "severity": {"type": "string", "enum": ["error", "warning"]}
          }
        }
      },
      "suggestions": {"type": "array", "items": {"type": "string"}}
    }
  }
}
```

**Error Handling:**
- If validation fails, collect all errors
- Format errors into structured feedback for Spec Agent
- Include JSON path, error message, and suggested fixes
- Retry with refined prompt (include previous errors)
- Max retries: 3, then fail gracefully

### 2. Code Generation Feedback Loop

**Flow:**
```
Writing Agent generates test code
    ↓
Code Validation (via MCP: validate_test_code)
    ↓
[Invalid?] → Collect errors → Refine prompt → Retry (max 3 attempts)
    ↓
[Valid?] → Optional: Run tests → Analyze results
```

**MCP Tool: `validate_test_code`**
```json
{
  "name": "validate_test_code",
  "description": "Validates generated test code for syntax, linting, and structure",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code_path": {"type": "string", "description": "Path to generated test file"},
      "framework": {"type": "string", "enum": ["pytest", "jest", "unittest", "playwright"]},
      "check_syntax": {"type": "boolean", "default": true},
      "check_lint": {"type": "boolean", "default": true},
      "check_structure": {"type": "boolean", "default": true}
    },
    "required": ["code_path", "framework"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "valid": {"type": "boolean"},
      "syntax_valid": {"type": "boolean"},
      "lint_passed": {"type": "boolean"},
      "structure_valid": {"type": "boolean"},
      "errors": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": {"type": "string", "enum": ["syntax", "lint", "structure"]},
            "line": {"type": "integer"},
            "message": {"type": "string"},
            "suggestion": {"type": "string"}
          }
        }
      }
    }
  }
}
```

**Validation Checks:**
1. **Syntax**: Python AST parsing, JavaScript parsing, etc.
2. **Linting**: ruff/flake8 for Python, ESLint for JS
3. **Structure**: Verify test structure matches framework conventions
   - pytest: test functions start with `test_`, fixtures defined correctly
   - jest: describe/it blocks, proper imports

**Error Handling:**
- Collect all validation errors
- Format with line numbers and suggestions
- Retry with refined prompt (include errors)
- Max retries: 3, then fail gracefully

---

## LangGraph State Machine

There are **two primary graphs**:
- A **Planning graph** that orchestrates and sequences all work.
- A **Testing graph** (per test type) that handles spec generation, code generation, and validation.

### Planning Agent State Definition

```python
from typing import TypedDict, Literal, Optional, List, Dict, Any


class PlanStep(TypedDict):
    id: str                      # stable identifier for the step
    type: str                    # e.g. "retrieve_context", "generate_unit_spec", "generate_unit_tests"
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"]
    params: Dict[str, Any]       # step-specific parameters
    result: Optional[Dict[str, Any]]  # optional structured result
    error_message: Optional[str]      # populated on failure


class PlanningAgentState(TypedDict):
    # Input
    request_id: str
    user_request: str
    test_type: Optional[Literal["api", "unit", "integration", "e2e", "performance"]]
    target: Optional[str]  # file/module/endpoint/scenario to test

    # Plan
    plan: List[PlanStep]
    current_step_index: int

    # Logging and retries
    max_retries_per_step: int
    attempt_counts: Dict[str, int]   # step_id -> attempts
    logs: List[str]                  # high-level log lines for this plan

    # Overall status
    status: Literal["planning", "executing", "completed", "failed"]
```

### Planning Graph Nodes

Each node is implemented in its own file under `graph/planning_nodes/`.

```python
def build_plan(state: PlanningAgentState) -> PlanningAgentState:
    """LLM-based planning node that expands user_request into a discrete ordered plan."""
    # Implementation lives in `graph/planning_nodes/build_plan.py`
    pass


def execute_current_step(state: PlanningAgentState) -> PlanningAgentState:
    """Executes the current step by delegating to testing graphs or MCP tools."""
    # Implementation lives in `graph/planning_nodes/execute_current_step.py`
    # Examples of delegated actions:
    # - Call context MCP tools (get_codebase_context, get_ast_analysis, get_openapi_spec).
    # - Invoke a testing graph for a specific test_type.
    # - Use file MCP tools to create/save generated spec and test files.
    pass


def advance_or_finish(state: PlanningAgentState) -> PlanningAgentState:
    """Moves to the next step or marks the plan as completed/failed."""
    # Implementation lives in `graph/planning_nodes/advance_or_finish.py`
    pass
```

The Planning graph runs until all steps are completed or a terminal error is reached, and it is the **only entrypoint** exposed to CI or user-facing workflows. It, in turn, calls into one or more Testing graphs as needed.

---

### Testing Graph State Definition

```python
from typing import TypedDict, Literal, Optional, List, Dict, Any
from langgraph.graph import StateGraph

class TestingAgentState(TypedDict):
    # Input
    user_request: str
    test_type: Literal["api", "unit", "integration", "e2e", "performance"]
    target: str  # file/module/endpoint to test
    framework: str  # pytest, jest, etc.
    
    # Context
    codebase_context: Optional[Dict[str, Any]]
    ast_analysis: Optional[Dict[str, Any]]
    selected_schema: Optional[str]
    
    # Phase 1: Spec Generation
    spec_attempts: int
    spec_json: Optional[Dict[str, Any]]
    spec_validation_result: Optional[Dict[str, Any]]
    spec_errors: List[Dict[str, Any]]
    
    # Phase 2: Code Generation
    code_attempts: int
    generated_code_path: Optional[str]
    code_validation_result: Optional[Dict[str, Any]]
    code_errors: List[Dict[str, Any]]
    
    # Phase 3: Execution (optional)
    test_results: Optional[Dict[str, Any]]
    analysis: Optional[str]
    
    # Control flow
    phase: Literal["spec_generation", "code_generation", "execution", "complete", "error"]
    should_retry: bool
    max_retries: int
```

### Testing Graph Nodes

```python
# Phase 1: Spec Generation
# NOTE: each node is implemented in its own file under `graph/nodes/`.

def retrieve_context(state: TestingAgentState) -> TestingAgentState:
    """Retrieve codebase context exclusively via MCP tools."""
    # Implementation lives in `graph/nodes/retrieve_context.py`
    # Calls MCP tools: get_codebase_context, get_ast_analysis, get_openapi_spec
    pass


def select_schema(state: TestingAgentState) -> TestingAgentState:
    """Select appropriate schema based on test_type."""
    # Implementation lives in `graph/nodes/select_schema.py`
    pass


def generate_spec(state: TestingAgentState) -> TestingAgentState:
    """Spec Agent generates JSON spec."""
    # Implementation lives in `graph/nodes/generate_spec.py`
    pass


def validate_spec(state: TestingAgentState) -> TestingAgentState:
    """Validate spec via internal MCP tool `validate_test_spec`."""
    # Implementation lives in `graph/nodes/validate_spec.py`
    pass


def refine_spec(state: TestingAgentState) -> TestingAgentState:
    """Refine spec based on MCP validation errors."""
    # Implementation lives in `graph/nodes/refine_spec.py`
    pass


# Phase 2: Code Generation

def generate_code(state: TestingAgentState) -> TestingAgentState:
    """Writing Agent generates test code from spec."""
    # Implementation lives in `graph/nodes/generate_code.py`
    pass


def validate_code(state: TestingAgentState) -> TestingAgentState:
    """Validate code via internal MCP tool `validate_test_code`."""
    # Implementation lives in `graph/nodes/validate_code.py`
    pass


def refine_code(state: TestingAgentState) -> TestingAgentState:
    """Refine code based on MCP validation errors."""
    # Implementation lives in `graph/nodes/refine_code.py`
    pass


# Phase 3: Execution (optional)

def run_tests(state: TestingAgentState) -> TestingAgentState:
    """Run tests via internal MCP tool `run_tests`."""
    # Implementation lives in `graph/nodes/run_tests.py`
    pass


def analyze_results(state: TestingAgentState) -> TestingAgentState:
    """Analyzer Agent analyzes test results."""
    # Implementation lives in `graph/nodes/analyze_results.py`
    pass
```

### Graph Edges (Conditional Routing)

```python
def should_retry_spec(state: TestingAgentState) -> str:
    """Check if spec validation failed and retries available"""
    if state["spec_validation_result"]["valid"]:
        return "proceed_to_code"
    if state["spec_attempts"] < state["max_retries"]:
        return "refine_spec"
    return "error"

def should_retry_code(state: TestingAgentState) -> str:
    """Check if code validation failed and retries available"""
    if state["code_validation_result"]["valid"]:
        return "proceed_to_execution"
    if state["code_attempts"] < state["max_retries"]:
        return "refine_code"
    return "error"
```

### Complete Graph Structure

```
[START]
  ↓
retrieve_context
  ↓
select_schema
  ↓
generate_spec ──┐
  ↓             │
validate_spec   │
  ↓             │
should_retry_spec (conditional)
  ├─→ refine_spec ──┘
  ├─→ proceed_to_code
  └─→ error

proceed_to_code
  ↓
generate_code ──┐
  ↓             │
validate_code   │
  ↓             │
should_retry_code (conditional)
  ├─→ refine_code ──┘
  ├─→ proceed_to_execution
  └─→ error

proceed_to_execution (optional)
  ↓
run_tests
  ↓
analyze_results
  ↓
[END]
```

---

## MCP Tools Specification

### Tools Exposed by Testing Agent

1. **generate_test_spec**
   - Generate test spec JSON for given target
   - Returns spec JSON or error

2. **generate_tests_from_spec**
   - Generate test code from existing spec
   - Returns path to generated test file

3. **validate_test_spec**
   - Validate spec against schema
   - Returns validation result with errors

4. **validate_test_code**
   - Validate generated code
   - Returns validation result with errors

5. **run_tests**
   - Execute tests and return results
   - Returns test results JSON

6. **analyze_test_results**
   - Analyze test execution results
   - Returns analysis and suggestions

### Tools Consumed by Testing Agent

1. **get_codebase_context** (from codebase agent)
   - Semantic search for relevant code
   - Returns code snippets and context

2. **get_ast_analysis** (from codebase agent)
   - AST analysis of target code
   - Returns AST structure and metadata

3. **get_openapi_spec** (from API agent)
   - Fetch OpenAPI specification
   - Returns API schema

4. **lint_code** (from linting agent)
   - Lint code files
   - Returns linting errors

5. **check_syntax** (from validation agent)
   - Check code syntax
   - Returns syntax errors

6. **run_build** (from build agent)
   - Run project build
   - Returns build status

---

## Implementation Considerations

### 1. Schema Versioning
- Each schema has version (e.g., `api_test_schema_v2.json`)
- Support schema migration/upgrading
- Validate schema compatibility

### 2. Retry Strategy
- Exponential backoff for retries
- Track retry reasons for debugging
- Log all attempts for audit trail

### 3. Error Handling
- Graceful degradation: if validation fails after retries, return partial results
- Clear error messages for users
- Log errors for debugging

### 4. Performance
- Cache schema validation results
- Parallel validation where possible
- Optimize MCP tool calls (batch if supported)

### 5. Testing the Agent
- Unit tests for each node
- Integration tests for full flows
- Test with various test types and frameworks

---

## Repository Structure

**Note:** The repository structure has been updated to reflect a cleaner organization with separate planning and execution graphs.

```
Root-level/
├── schemas/                    # Test specification schemas (JSON canonical)
│   ├── api_test_schema_v2.json
│   ├── unit_test_schema_v1.json
│   ├── integration_test_schema_v1.json
│   ├── e2e_test_schema_v1.json
│   └── performance_test_schema_v1.json
├── agents/                     # LLM agent implementations
│   ├── spec_agent.py          # Generates test specs (Model A)
│   ├── writing_agent.py       # Generates test code from specs (Model B)
│   └── analyzer_agent.py      # Analyzes test results (Model C)
├── mcp/                        # MCP tools and server
│   ├── tools/
│   │   ├── validate_spec.py   # Internal: validates spec against schema
│   │   ├── validate_code.py   # Internal: validates generated code
│   │   └── run_tests.py       # Internal: executes tests
│   └── server.py              # MCP server exposing tools
├── graph/                      # LangGraph state machines
│   ├── execution_graph/       # Testing graph (spec → code → validation)
│   │   ├── state.py           # Testing graph state definitions
│   │   ├── graph.py           # Testing graph wiring
│   │   └── nodes/             # Individual node implementations
│   │       ├── retrieve_context.py
│   │       ├── select_schema.py
│   │       ├── generate_spec.py
│   │       ├── validate_spec.py
│   │       ├── refine_spec.py
│   │       ├── generate_code.py
│   │       ├── validate_code.py
│   │       ├── refine_code.py
│   │       ├── run_tests.py
│   │       └── analyze_results.py
│   └── planning_graph/        # Planning Agent graph (orchestrates everything)
│       ├── planning_state.py  # Planning Agent state & PlanStep definitions
│       ├── planning_graph.py  # Planning graph wiring
│       └── nodes/             # Planning node implementations
│           ├── build_plan.py
│           ├── execute_current_step.py
│           └── advance_or_finish.py
├── utils/                      # Shared utilities
│   ├── schema_registry.py     # Schema selection and loading
│   └── error_formatter.py     # Error formatting for feedback loops
└── main.py                     # Entry point
```

### Key Changes:
- **Schemas** moved to root-level `schemas/` directory
- **Graph** split into `execution_graph/` (testing pipeline) and `planning_graph/` (orchestration)
- Each graph has its own `nodes/` subdirectory for node implementations
- All nodes are separate files (one node = one file)

---

## Next Steps

1. **Schema Design**: Create schemas for unit/integration/e2e/performance tests
2. **MCP Tool Implementation**: Implement validation tools as MCP servers
3. **LangGraph Implementation**: Build state machine with feedback loops
4. **Agent Models**: Configure specialized models for each phase
5. **CI Integration**: GitHub Actions workflow integration
6. **Testing**: Test the agent with various scenarios
