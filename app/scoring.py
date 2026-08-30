from __future__ import annotations
from datetime import date

def absolute_weighted_score(eval_obj, criteria: list[dict]) -> float:
    weights = {int(c["criterion_id"]): float(c["weight"]) for c in criteria}
    total = 0.0
    for x in eval_obj.criteria:
        if x.max_score > 0:
            total += (x.score / x.max_score) * weights[x.criterion_id]
    return round(total, 4)

def rank_suppliers(records: list[dict], criteria: list[dict]) -> list[dict]:
    # Criterion benchmark = highest valid score observed for that criterion.
    benchmarks = {}
    for c in criteria:
        cid = int(c["criterion_id"])
        benchmarks[cid] = max(
            (next(x.score for x in r["evaluation"].criteria if x.criterion_id == cid) for r in records),
            default=0.0
        )

    weight_by_id = {int(c["criterion_id"]): float(c["weight"]) for c in criteria}
    total_weight = sum(weight_by_id.values())

    enriched = []
    for r in records:
        details = []
        weighted_rel_sum = 0.0
        for x in r["evaluation"].criteria:
            benchmark = benchmarks[x.criterion_id]
            gap = x.score - benchmark
            # Safe handling when benchmark is zero: define relative performance as 100%.
            relative = 100.0 if benchmark == 0 else (x.score / benchmark) * 100.0
            weighted_rel_sum += relative * weight_by_id[x.criterion_id]
            details.append({
                "criterion_id": x.criterion_id,
                "score": x.score,
                "max_score": x.max_score,
                "benchmark": benchmark,
                "gap": round(gap, 4),
                "relative_performance_pct": round(relative, 4),
                "weight": weight_by_id[x.criterion_id],
                "justification": x.justification,
                "evidence": x.evidence,
            })
        ppi = weighted_rel_sum / total_weight if total_weight else 0.0
        enriched.append({
            **{k:v for k,v in r.items() if k != "evaluation"},
            "absolute_score": absolute_weighted_score(r["evaluation"], criteria),
            "ppi": round(ppi, 4),
            "criteria": details,
            "warnings": list(r["evaluation"].warnings),
            "risks": list(r["evaluation"].risks),
            "overall_summary": r["evaluation"].overall_summary,
        })

    # Mandatory tie-break:
    # 1) Higher PPI
    # 2) Earlier submission date
    # 3) Higher historical experience rating
    # 4) Supplier name ascending
    enriched.sort(key=lambda x: (
        -x["ppi"],
        date.fromisoformat(x["submission_date"]),
        -float(x["experience_rating"]),
        x["supplier_name"].casefold(),
    ))

    for i, row in enumerate(enriched, start=1):
        row["final_rank"] = i
        row["tie_break_explanation"] = (
            "Sorted by PPI descending, submission date ascending, "
            "experience rating descending, then supplier name ascending."
        )
    return enriched
