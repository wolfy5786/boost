## Testing Agent – Overview

This project is an **AI-assisted software testing agent** built with **Python + LangGraph** and **MCP tools**.  
It generates tests in two stages:

1. **Spec generation** – create structured JSON specs using strict schemas (unit, integration, E2E, performance, API).
2. **Code generation** – turn specs into concrete test files, validate them, and (optionally) run them in CI.

All flows are orchestrated by a **Planning Agent** that builds a discrete plan (steps), executes it, and uses internal MCP tools for validation, context retrieval, and file operations.

---

## High-Level Architecture

- **Planning Agent (Planning Graph)**  
  - Entry point for user/CI requests (e.g., “add tests for `user_service`”).  
  - Produces a **plan**: ordered `PlanStep`s (retrieve context → generate spec → validate spec → generate code → validate code → save files → run tests).  
  - Executes each step by delegating to:
    - **Execution graph** (spec + code + validation pipelines),
    - **Internal MCP tools** (validation, context, filesystem, etc.),
    - Other agents exposed via MCP.

- **Execution Graph (Testing Graph)**  
  - Handles the **testing pipeline** for a given test type:
    - Context retrieval (via MCP only),
    - Spec generation using the appropriate JSON schema,
    - Spec validation (MCP `validate_test_spec`),
    - Test code generation,
    - Code validation (MCP `validate_test_code`),
    - Optional test execution + analysis.

- **MCP Layer (Internal Tools)**  
  - Validation: `validate_test_spec`, `validate_test_code`, `run_tests`.  
  - Context: `get_codebase_context`, `get_ast_analysis`, `get_openapi_spec`, etc.  
  - All validation and context retrieval flows **through MCP** – graph nodes do not access the filesystem or repo directly.

- **Schemas (JSON canonical)**  
  - API: `api_test_schema_v2.json`  
  - Unit: `unit_test_schema_v1.json`  
  - Integration: `integration_test_schema_v1.json`  
  - E2E: `e2e_test_schema_v1.json`  
  - Performance: `performance_test_schema_v1.json`  
  - Schemas are the **contract** between spec-generation and code-generation agents.

For a more detailed description (including diagrams and state definitions), see `ARCHITECTURE.md`.

---

## Repository Structure (Planned)

```text
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
└── ARCHITECTURE.md            # In-depth design & diagrams
```

> The codebase is being built **incrementally**. Some files/dirs above may be planned but not yet implemented.

---

## Development Notes

- **Strict separation of concerns**
  - Planning Agent decides **what to do** and in which order.
  - Execution graph focuses on **how to generate and validate tests** for a given test type.
  - MCP tools handle **I/O and validation** (context, filesystem, running tests).

- **Security & secrets**
  - Schemas use **env/vault variable names only** for auth; no raw secrets in specs.
  - CI/runtime is responsible for resolving env/vault values.

---

## Getting Started (WIP)

This project is still under active design and incremental implementation.  
Once the core graphs and MCP tools are in place, this section will document:

- How to install dependencies,
- How to run the MCP server,
- How to invoke the Planning Agent for:
  - generating tests locally,
  - running in GitHub Actions / CI.

For now, use `ARCHITECTURE.md` and the schema files in `schemas/` as the source of truth for design and contracts.

