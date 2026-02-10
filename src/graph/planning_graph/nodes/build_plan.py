"""Planning graph node: build the initial plan.

This node is responsible for translating a high-level user_request into an
ordered list of PlanStep items, stored on the PlanningAgentState.

The actual execution of each step is handled by other planning nodes
(`execute_current_step`, `advance_or_finish`) and by the execution graph.
"""

from __future__ import annotations

from typing import List

from ..planning_state import ArtifactsInfo, PlanStep, PlanningAgentState


def build_plan(state: PlanningAgentState) -> PlanningAgentState:
    """Construct an initial plan for the current request.

    Behaviour:
    - If a plan already exists, return state unchanged.
    - Otherwise, choose an ordered list of steps based on:
        * operation: what the user/CI actually wants to do
        * artifacts: whether specs/tests already exist for (target, test_type)
    - The concrete step `type` strings are generic; execution nodes will look
      at `test_type` to route into the right execution graph.
    """

    # If a plan has already been built, do not overwrite it.
    if state.get("plan"):
        return state

    test_type = state.get("test_type") or "unit"
    target = state.get("target")
    operation = state.get("operation") or "generate_and_run"

    artifacts: ArtifactsInfo = {
        "spec_exists": False,
        "tests_exist": False,
        "spec_paths": [],
        "test_paths": [],
        **(state.get("artifacts") or {}),
    }

    steps: List[PlanStep] = []

    def add_step(
        step_id: str,
        step_type: str,
        params: dict | None = None,
    ) -> None:
        steps.append(
            {
                "id": step_id,
                "type": step_type,
                "status": "pending",
                "params": params or {},
                "result": None,
                "error_message": None,
            }
        )

    # --- Decide which steps are needed based on operation + artifacts ---

    if operation == "run_only":
        # Just run existing tests (or whatever exists for this target).
        add_step(
            "run_tests",
            "run_tests",
            {"target": target, "test_type": test_type, "test_paths": artifacts.get("test_paths", [])},
        )
        add_step(
            "analyze_results",
            "analyze_results",
            {"target": target, "test_type": test_type},
        )

    elif operation in ("generate_only", "generate_and_run", "update_specs"):
        spec_exists = artifacts.get("spec_exists", False)
        tests_exist = artifacts.get("tests_exist", False)

        # Always start with context so downstream nodes have rich information.
        add_step(
            "retrieve_context",
            "retrieve_context",
            {"target": target, "test_type": test_type},
        )

        if not spec_exists or operation in ("generate_only", "generate_and_run", "update_specs"):
            # We either don't have specs, or we explicitly want to update them.
            add_step(
                "generate_spec",
                "generate_spec",
                {"target": target, "test_type": test_type},
            )

        # Validate whatever spec we will be using (newly generated or existing).
        add_step(
            "validate_spec",
            "validate_spec",
            {"test_type": test_type, "spec_paths": artifacts.get("spec_paths", [])},
        )

        if operation in ("generate_only", "generate_and_run") and (not tests_exist or operation != "generate_only"):
            # Generate / refresh tests if needed.
            add_step(
                "generate_code",
                "generate_code",
                {"test_type": test_type},
            )
            add_step(
                "validate_code",
                "validate_code",
                {"test_type": test_type},
            )
            add_step(
                "save_tests",
                "save_tests",
                {"target": target, "test_type": test_type},
            )

        if operation == "generate_and_run":
            add_step(
                "run_tests",
                "run_tests",
                {"target": target, "test_type": test_type},
            )
            add_step(
                "analyze_results",
                "analyze_results",
                {"target": target, "test_type": test_type},
            )

    elif operation == "analyze_results":
        # Assume results already exist somewhere (e.g. CI artifacts).
        add_step(
            "analyze_results",
            "analyze_results",
            {"target": target, "test_type": test_type},
        )

    else:
        # Fallback: behave like generate_and_run from scratch.
        add_step(
            "retrieve_context",
            "retrieve_context",
            {"target": target, "test_type": test_type},
        )
        add_step(
            "generate_spec",
            "generate_spec",
            {"target": target, "test_type": test_type},
        )
        add_step(
            "validate_spec",
            "validate_spec",
            {"test_type": test_type},
        )
        add_step(
            "generate_code",
            "generate_code",
            {"test_type": test_type},
        )
        add_step(
            "validate_code",
            "validate_code",
            {"test_type": test_type},
        )
        add_step(
            "save_tests",
            "save_tests",
            {"target": target, "test_type": test_type},
        )

    state["plan"] = steps
    state["current_step_index"] = 0
    state["status"] = "executing"

    # Basic log entry so we can trace that plan construction happened.
    logs = state.get("logs") or []
    logs.append(f"Plan built with {len(steps)} steps for test_type={test_type}, target={target}")
    state["logs"] = logs

    return state


__all__ = ["build_plan"]

