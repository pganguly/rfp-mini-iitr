from __future__ import annotations

from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END

from .db import (
    get_active_criteria,
    validate_active_weights,
    create_run,
    finish_run,
    save_supplier_result,
)
from .pdf_tools import extract_pdf_text
from .llm import evaluate_with_llm, evaluate_mock
from .validation import normalize_evaluation
from .scoring import rank_suppliers


class RFPGraphState(TypedDict, total=False):
    # Inputs
    suppliers: list[dict]
    db_path: Any
    mode: str
    model: str | None
    api_key: str | None
    base_url: str | None
    pdf_backend: str

    # Workflow state
    criteria: list[dict]
    rfp_run_id: str
    extracted_suppliers: list[dict]
    raw_evaluations: list[dict]
    normalized_records: list[dict]
    ranked_results: list[dict]
    status: str


def load_criteria_node(state: RFPGraphState) -> dict:
    criteria = get_active_criteria(state["db_path"])
    ok, total = validate_active_weights(criteria)
    if not ok:
        raise ValueError(
            f"Active criterion weights must total 100%; current total={total}"
        )
    return {"criteria": criteria}


def create_batch_node(state: RFPGraphState) -> dict:
    run_id = create_run(state["db_path"])
    return {"rfp_run_id": run_id, "status": "RUNNING"}


def extract_documents_node(state: RFPGraphState) -> dict:
    extracted = []
    for supplier in state["suppliers"]:
        text = extract_pdf_text(supplier["pdf_bytes"], backend=state.get("pdf_backend", "auto"))
        extracted.append({
            "supplier_name": supplier["supplier_name"],
            "submission_date": supplier["submission_date"],
            "experience_rating": float(supplier["experience_rating"]),
            "proposal_text": text,
        })
    return {"extracted_suppliers": extracted}


def evaluate_suppliers_node(state: RFPGraphState) -> dict:
    raw_evaluations = []
    for supplier in state["extracted_suppliers"]:
        if state.get("mode", "mock") == "llm":
            raw = evaluate_with_llm(
                supplier["supplier_name"],
                supplier["proposal_text"],
                state["criteria"],
                model=state.get("model") or "openai/gpt-4o-mini",
                api_key=state.get("api_key"),
                base_url=state.get("base_url"),
            )
        else:
            raw = evaluate_mock(
                supplier["supplier_name"],
                supplier["proposal_text"],
                state["criteria"],
            )
        raw_evaluations.append({
            "supplier": supplier,
            "raw": raw,
        })
    return {"raw_evaluations": raw_evaluations}


def validate_node(state: RFPGraphState) -> dict:
    normalized = []
    for item in state["raw_evaluations"]:
        supplier = item["supplier"]
        evaluation = normalize_evaluation(
            item["raw"],
            supplier["supplier_name"],
            state["criteria"],
        )
        normalized.append({
            "supplier_name": supplier["supplier_name"],
            "submission_date": supplier["submission_date"],
            "experience_rating": supplier["experience_rating"],
            "evaluation": evaluation,
        })
    return {"normalized_records": normalized}


def rank_node(state: RFPGraphState) -> dict:
    ranked = rank_suppliers(state["normalized_records"], state["criteria"])
    return {"ranked_results": ranked}


def persist_node(state: RFPGraphState) -> dict:
    try:
        for row in state["ranked_results"]:
            save_supplier_result(
                state["rfp_run_id"],
                row,
                state["db_path"],
            )
        finish_run(state["rfp_run_id"], "COMPLETED", state["db_path"])
        return {"status": "COMPLETED"}
    except Exception:
        finish_run(state["rfp_run_id"], "FAILED", state["db_path"])
        raise


def build_rfp_graph():
    builder = StateGraph(RFPGraphState)

    # Agentic orchestration, deterministic ordering of responsibilities:
    builder.add_node("load_criteria", load_criteria_node)
    builder.add_node("create_batch", create_batch_node)
    builder.add_node("extract_documents", extract_documents_node)
    builder.add_node("evaluate_suppliers", evaluate_suppliers_node)
    builder.add_node("validate", validate_node)
    builder.add_node("rank", rank_node)
    builder.add_node("persist", persist_node)

    builder.add_edge(START, "load_criteria")
    builder.add_edge("load_criteria", "create_batch")
    builder.add_edge("create_batch", "extract_documents")
    builder.add_edge("extract_documents", "evaluate_suppliers")
    builder.add_edge("evaluate_suppliers", "validate")
    builder.add_edge("validate", "rank")
    builder.add_edge("rank", "persist")
    builder.add_edge("persist", END)

    return builder.compile()


rfp_graph = build_rfp_graph()


def evaluate_batch_langgraph(
    suppliers,
    db_path,
    mode="mock",
    model=None,
    api_key=None,
    base_url=None,
    pdf_backend="auto",
):
    initial_state: RFPGraphState = {
        "suppliers": suppliers,
        "db_path": db_path,
        "mode": mode,
        "model": model,
        "api_key": api_key,
        "base_url": base_url,
        "pdf_backend": pdf_backend,
    }

    try:
        result = rfp_graph.invoke(initial_state)
        return (
            result["rfp_run_id"],
            result["criteria"],
            result["ranked_results"],
        )
    except Exception:
        # If a batch was created before failure, mark it failed.
        # Errors before create_batch simply propagate.
        raise
