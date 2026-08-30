from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

class Criterion(BaseModel):
    criterion_id: int
    name: str
    description: str
    weight: float
    max_score: float
    is_active: bool = True

class CriterionEvaluation(BaseModel):
    criterion_id: int
    score: float
    max_score: float
    justification: str = ""
    evidence: str = ""

class EvaluationResponse(BaseModel):
    supplier_name: str
    criteria: List[CriterionEvaluation] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    overall_summary: str = ""

class SupplierInput(BaseModel):
    supplier_name: str
    submission_date: str
    experience_rating: float

class NormalizedEvaluation(BaseModel):
    supplier_name: str
    criteria: List[CriterionEvaluation]
    risks: List[str]
    overall_summary: str
    warnings: List[str] = Field(default_factory=list)
