from __future__ import annotations
from .models import CriterionEvaluation, NormalizedEvaluation

def normalize_evaluation(raw: dict, supplier_name: str, criteria: list[dict]) -> NormalizedEvaluation:
    warnings = []
    by_id = {}
    for item in raw.get("criteria", []) if isinstance(raw, dict) else []:
        try:
            cid = int(item.get("criterion_id"))
            by_id[cid] = item
        except Exception:
            warnings.append(f"Ignored criterion with invalid criterion_id: {item!r}")

    normalized = []
    for c in criteria:
        cid = int(c["criterion_id"])
        max_score = float(c["max_score"])
        item = by_id.get(cid)

        if item is None:
            warnings.append(f"Criterion {cid} missing; normalized to score 0.")
            normalized.append(CriterionEvaluation(
                criterion_id=cid, score=0.0, max_score=max_score,
                justification="Missing LLM result; normalized to zero.",
                evidence=""
            ))
            continue

        try:
            score = float(item.get("score", 0))
        except Exception:
            score = 0.0
            warnings.append(f"Criterion {cid} had non-numeric score; normalized to 0.")

        clipped = max(0.0, min(score, max_score))
        if clipped != score:
            warnings.append(f"Criterion {cid} score {score} clipped to {clipped}.")

        returned_max = item.get("max_score", max_score)
        try:
            returned_max = float(returned_max)
        except Exception:
            returned_max = max_score
        if returned_max != max_score:
            warnings.append(
                f"Criterion {cid} max_score {returned_max} replaced with configured {max_score}."
            )

        normalized.append(CriterionEvaluation(
            criterion_id=cid,
            score=clipped,
            max_score=max_score,
            justification=str(item.get("justification", "")),
            evidence=str(item.get("evidence", "")),
        ))

    return NormalizedEvaluation(
        supplier_name=supplier_name,
        criteria=normalized,
        risks=[str(x) for x in raw.get("risks", [])] if isinstance(raw, dict) else [],
        overall_summary=str(raw.get("overall_summary", "")) if isinstance(raw, dict) else "",
        warnings=warnings,
    )
