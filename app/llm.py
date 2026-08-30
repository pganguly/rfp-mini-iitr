from __future__ import annotations

import json
import os
from langchain_openai import ChatOpenAI

from .config import DEFAULT_MODEL, OPENROUTER_BASE_URL
from .models import EvaluationResponse


def build_prompt(supplier_name: str, proposal_text: str, criteria: list[dict]) -> str:
    criteria_json = json.dumps(criteria, indent=2)
    return f"""
You are evaluating ONE supplier proposal for an RFP.

Evaluate the supplier independently against every active criterion.

RULES:
1. Use only evidence explicitly present in the supplier proposal.
2. Produce one evaluation for every active criterion.
3. Each score must be between 0 and max_score.
4. Provide a concise justification for each score.
5. Provide short supporting evidence from the proposal.
6. If evidence is missing, explicitly say so and score conservatively.
7. Do not compare this supplier with other suppliers.
8. Do not calculate weighted scores.
9. Do not calculate peer benchmarks.
10. Do not calculate PPI.
11. Do not determine the final rank.
12. Keep reasoning concise.

RETURN ONLY VALID JSON IN THIS EXACT STRUCTURE:

{{
    "supplier_name": "{supplier_name}",
    "criteria": [
        {{
            "criterion_id": 1,
            "score": 0,
            "max_score": 10,
            "justification": "",
            "evidence": ""
        }}
    ],
    "risks": [],
    "overall_summary": ""
}}

IMPORTANT:
- Include one object in "criteria" for EVERY active criterion.
- Use the actual criterion_id and configured max_score.
- Do not omit any active criterion.
- Do not wrap the JSON in markdown.
- Do not add text before or after the JSON.
- The first character of the response must be {{
- The last character of the response must be }}

Supplier:
{supplier_name}

Active criteria:
{criteria_json}

Proposal:
{proposal_text}
""".strip()


def evaluate_with_llm(
    supplier_name: str,
    proposal_text: str,
    criteria: list[dict],
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    openrouter_key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise ValueError(
            "OpenRouter API key is missing. Set OPENROUTER_API_KEY "
            "or enter the key in the Streamlit sidebar."
        )

    selected_model = model or os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL

    default_headers = {}
    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    app_name = os.getenv("OPENROUTER_APP_NAME")
    if referer:
        default_headers["HTTP-Referer"] = referer
    if app_name:
        default_headers["X-Title"] = app_name

    llm = ChatOpenAI(
        model=selected_model,
        temperature=0,
        api_key=openrouter_key,
        base_url=base_url or OPENROUTER_BASE_URL,
        default_headers=default_headers or None,
    )
    try:
        structured_llm = llm.with_structured_output(EvaluationResponse)
        result = structured_llm.invoke(
            build_prompt(
                supplier_name=supplier_name,
                proposal_text=proposal_text,
                criteria=criteria,
            )
        )
        output = result.model_dump()
        output["_llm_metadata"] = {
            "model": selected_model,
            "success": True,
        }
        return output
    except Exception as exc:

        # Do not crash the complete batch.
        return {
            "supplier_name": supplier_name,
            "criteria": [],
            "risks": [
                "LLM evaluation failed."
            ],
            "overall_summary": (
                "The supplier could not be evaluated by the LLM. "
                "The validation layer will normalize missing criteria."
            ),
            "_llm_metadata": {
                "model": selected_model,
                "success": False,
                "error": str(exc),
            },
        }


def evaluate_mock(supplier_name: str, proposal_text: str, criteria: list[dict]) -> dict:
    text = proposal_text.lower()
    keyword_sets = {
        1: ["architecture", "integration", "scalability", "api", "technical"],
        2: ["timeline", "milestone", "staffing", "implementation", "risk"],
        3: ["price", "pricing", "cost", "assumption", "commercial"],
        4: ["security", "iso 27001", "soc 2", "privacy", "audit", "encryption"],
        5: ["support", "reference", "experience", "sla", "project"],
    }

    criteria_out = []
    for criterion in criteria:
        criterion_id = int(criterion["criterion_id"])
        max_score = float(criterion["max_score"])
        hits = sum(
            1 for keyword in keyword_sets.get(criterion_id, [])
            if keyword in text
        )
        score = min(max_score, 4 + hits * 1.2)
        criteria_out.append({
            "criterion_id": criterion_id,
            "score": round(score, 1),
            "max_score": max_score,
            "justification": f"Demo-mode score based on {hits} matched evidence indicators.",
            "evidence": (
                "Offline demo mode is keyword-based; use OpenRouter LLM mode "
                "for semantic evidence-grounded evaluation."
            ),
        })

    return {
        "supplier_name": supplier_name,
        "criteria": criteria_out,
        "risks": ["Demo mode is deterministic and not a semantic LLM assessment."],
        "overall_summary": "Generated by the offline demo evaluator.",
    }
