"""State definitions for the Planning Agent graph.

These types mirror the structures documented in ARCHITECTURE.md and are used
by the planning graph (see `planning_graph.py`) and its nodes in
`planning_nodes/`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


class PlanStep(TypedDict):
    """Single step in a test-planning and execution plan.

    The Planning Agent builds a list of these steps and then executes them
    one by one, delegating to testing graphs or MCP tools as needed.
    """

    id: str  # stable identifier for the step
    type: str  # e.g. "retrieve_context", "generate_unit_spec", "generate_unit_tests"
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"]
    params: Dict[str, Any]  # step-specific parameters
    result: Optional[Dict[str, Any]]  # optional structured result
    error_message: Optional[str]  # populated on failure


class PlanningAgentState(TypedDict):
    """Shared state for the Planning Agent graph.

    This is the top-level state object that flows through:
    - `build_plan`
    - `execute_current_step`
    - `advance_or_finish`
    """

    # Input / high-level request metadata
    request_id: str
    user_request: str
    test_type: Optional[Literal["api", "unit", "integration", "e2e", "performance"]]
    target: Optional[str]  # file/module/endpoint/scenario to test

    # Plan and progress
    plan: List[PlanStep]
    current_step_index: int

    # Logging and retries
    max_retries_per_step: int
    attempt_counts: Dict[str, int]  # step_id -> attempts
    logs: List[str]  # high-level log lines for this plan

    # Overall status of the planning/execution lifecycle
    status: Literal["planning", "executing", "completed", "failed"]


__all__ = [
    "PlanStep",
    "PlanningAgentState",
]

